# import chinadata.ca_data as ts
import tudata as ts
import pymysql
import pandas as pd
from ta.trend import SMAIndicator, MACD
from ta.volatility import BollingerBands
from ta.momentum import StochasticOscillator
from datetime import datetime, timedelta
from decimal import Decimal
import traceback
from sqlalchemy import create_engine
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue

# 设置 Tushare Pro 的 token
ts.set_token('a1dec7f45807440eb48f8f28ccee3ead')
# ts.set_token('le2937d38d26f5322ae6096286072faf933')
pro = ts.pro_api()

# 创建线程本地存储
thread_local = threading.local()

def get_pro():
    """
    获取线程本地的 Tushare Pro 实例
    """
    if not hasattr(thread_local, "pro") or thread_local.pro is None:
        thread_local.pro = ts.pro_api()
    return thread_local.pro

def get_db_connection():
    """
    获取线程本地的数据库连接
    """
    if not hasattr(thread_local, "conn") or thread_local.conn is None:
        thread_local.conn = pymysql.connect(
            host='localhost',
            user='leewcc',
            password='leewcc',
            database='happy',
            charset='utf8mb4',
            autocommit=False
        )
        # 同时创建新的游标
        thread_local.cursor = thread_local.conn.cursor()
    return thread_local.conn

def get_cursor():
    """
    获取线程本地的游标
    """
    if not hasattr(thread_local, "cursor") or thread_local.cursor is None:
        conn = get_db_connection()
        thread_local.cursor = conn.cursor()
    return thread_local.cursor

def check_connection():
    """
    检查连接是否有效，如果无效则重新连接
    """
    try:
        if hasattr(thread_local, "conn") and thread_local.conn is not None:
            thread_local.conn.ping(reconnect=True)
        else:
            get_db_connection()
            
        if not hasattr(thread_local, "cursor") or thread_local.cursor is None:
            thread_local.cursor = thread_local.conn.cursor()
            
    except Exception as e:
        # 如果发生任何错误，重新建立连接和游标
        if hasattr(thread_local, "cursor"):
            try:
                thread_local.cursor.close()
            except:
                pass
            thread_local.cursor = None
            
        if hasattr(thread_local, "conn"):
            try:
                thread_local.conn.close()
            except:
                pass
            thread_local.conn = None
            
        get_db_connection()
        
    return thread_local.conn, thread_local.cursor

def get_all_stock_codes():
    """
    从 Tushare Pro 获取所有股票代码
    :return: 包含所有股票代码的列表
    """
    try:
        pro = get_pro()
        data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name')
        print(data)
        all_codes = data[['ts_code', 'symbol', 'name']].values.tolist()
        return all_codes
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        last_frame = tb[-1]
        line_number = last_frame.lineno
        print(f"从 Tushare Pro 获取股票代码时出错: {e}，错误发生在第 {line_number} 行")
        return []

def calculate_indicators(data):
    """
    计算技术指标
    :param data: 包含日线数据的 DataFrame
    :return: 包含技术指标的 DataFrame
    """
    try:
        # 计算均线
        data['ma_5'] = SMAIndicator(data['close'], window=5).sma_indicator()
        data['ma_10'] = SMAIndicator(data['close'], window=10).sma_indicator()
        data['ma_20'] = SMAIndicator(data['close'], window=20).sma_indicator()
        data['ma_60'] = SMAIndicator(data['close'], window=60).sma_indicator()

        # 计算布林带
        bollinger = BollingerBands(data['close'])
        data['boll_low'] = bollinger.bollinger_lband()
        data['boll_mid'] = bollinger.bollinger_mavg()
        data['boll_up'] = bollinger.bollinger_hband()

        # 计算 KDJ
        kdj = StochasticOscillator(data['high'], data['low'], data['close'])
        data['kdj'] = kdj.stoch()

        # 计算 MACD
        macd = MACD(data['close'])
        data['macd'] = macd.macd()

        return data
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        last_frame = tb[-1]
        line_number = last_frame.lineno
        print(f"计算技术指标时出错: {e}，错误发生在第 {line_number} 行")
        print(traceback.format_exc())
        return []

def calculate_limit_info(data, stock_name):
    """
    计算是否涨停、是否炸板和是否跌停
    :param data: 包含日线数据的 DataFrame
    :param stock_name: 股票名称
    :return: 包含计算结果的 DataFrame
    """
    try:
        limit_ratio = Decimal('0.1') if 'ST' not in stock_name else Decimal('0.05')
        # 如果 up_limit 和 down_limit 不存在，使用计算方式获取
        if 'up_limit' not in data.columns or 'down_limit' not in data.columns:
            data['pre_close'] = data['close'].shift(1)
            data['up_limit'] = data['pre_close'].apply(lambda x: Decimal(str(x))) * (Decimal('1') + limit_ratio)
            data['down_limit'] = data['pre_close'].apply(lambda x: Decimal(str(x))) * (Decimal('1') - limit_ratio)
            data.drop('pre_close', axis=1, inplace=True)

        # 调整是否涨停的判断逻辑
        data['is_limit_up'] = data['close'].apply(lambda x: Decimal(str(x))) == data['up_limit'].apply(lambda x: Decimal(str(x)))
        # 调整是否炸板的判断逻辑
        data['is_board_broken'] = (data['high'].apply(lambda x: Decimal(str(x))) == data['up_limit'].apply(lambda x: Decimal(str(x)))) & (
                data['close'].apply(lambda x: Decimal(str(x))) != data['up_limit'].apply(lambda x: Decimal(str(x))))
        data['is_limit_down'] = data['close'].apply(lambda x: Decimal(str(x))) == data['down_limit'].apply(lambda x: Decimal(str(x)))
        return data
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        last_frame = tb[-1]
        line_number = last_frame.lineno
        print(f"计算涨跌停相关信息时出错: {e}，错误发生在第 {line_number} 行")
        print(traceback.format_exc())
        return []

def check_data_exists(stock_code, specified_date):
    """
    检查指定股票在指定日期的数据是否已存在
    """
    try:
        conn, cursor = check_connection()
        check_sql = """
        SELECT COUNT(*) FROM daily_data 
        WHERE stock_code = %s AND trade_date = %s
        """
        cursor.execute(check_sql, (stock_code, specified_date))
        count = cursor.fetchone()[0]
        return count > 0
    except Exception as e:
        print(f"检查数据是否存在时出错: {e}")
        return False

def insert_into_daily_data_table(stock_code, stock_name, data, specified_date):
    """
    将指定日期的日线数据插入到 daily_data 表中
    :param stock_code: 股票代码
    :param stock_name: 股票名称
    :param data: 包含日线数据和技术指标的 DataFrame
    :param specified_date: 指定日期，格式为 'YYYYMMDD'
    """
    conn, cursor = check_connection()
    
    insert_sql = """
    INSERT INTO daily_data (stock_name, stock_code, trade_date, low_price, high_price, open_price, close_price, 
    turnover_amount, trading_volume, turnover_rate, price_change_rate, previous_close_price, call_auction_increase, 
    ma_5, ma_10, ma_20, ma_60, boll_low, boll_mid, boll_up, kdj, macd, industry_sector, concept_sector, is_limit_up, is_board_broken,
    up_limit, down_limit, turnover_rate_f, volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, dv_ratio, dv_ttm, total_share, float_share, free_share, total_mv, circ_mv, is_limit_down) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    specified_date_data = data[data['trade_date'] == specified_date]
    for index, row in specified_date_data.iterrows():
        try:
            conn, cursor = check_connection()
            
            trade_date = row['trade_date']
            low_price = float(row['low']) if row['low'] is not None else 0
            high_price = float(row['high']) if row['high'] is not None else 0
            open_price = float(row['open']) if row['open'] is not None else 0
            close_price = float(row['close']) if row['close'] is not None else 0
            turnover_amount = float(row['amount']) if row['amount'] is not None else 0
            trading_volume = float(row['vol']) if row['vol'] is not None else 0
            turnover_rate = float(row.get('turnover_rate', 0))
            price_change_rate = float(row.get('pct_chg', 0))
            previous_close_price = float(row.get('pre_close', 0))
            call_auction_increase = None
            ma_5 = float(row['ma_5']) if pd.notna(row['ma_5']) else None
            ma_10 = float(row['ma_10']) if pd.notna(row['ma_10']) else None
            ma_20 = float(row['ma_20']) if pd.notna(row['ma_20']) else None
            ma_60 = float(row['ma_60']) if pd.notna(row['ma_60']) else None
            boll_low = float(row['boll_low']) if pd.notna(row['boll_low']) else None
            boll_mid = float(row['boll_mid']) if pd.notna(row['boll_mid']) else None
            boll_up = float(row['boll_up']) if pd.notna(row['boll_up']) else None
            kdj = float(row['kdj']) if pd.notna(row['kdj']) else None
            macd = float(row['macd']) if pd.notna(row['macd']) else None
            industry_sector = ''  # 暂无行业信息
            concept_sector = ''  # 暂无概念信息
            is_limit_up = int(row['is_limit_up'])
            is_board_broken = int(row['is_board_broken'])

            up_limit = float(row.get('up_limit', 0)) if row.get('up_limit') is not None else 0
            down_limit = float(row.get('down_limit', 0)) if row.get('down_limit') is not None else 0
            turnover_rate_f = float(row.get('turnover_rate_f', 0)) if row.get('turnover_rate_f') is not None else 0
            volume_ratio = float(row.get('volume_ratio', 0)) if row.get('volume_ratio') is not None else 0
            pe = float(row.get('pe', 0)) if pd.notna(row.get('pe', 0)) else None
            pe_ttm = float(row.get('pe_ttm', 0)) if pd.notna(row.get('pe_ttm', 0)) else None
            pb = float(row.get('pb', 0)) if row.get('pb') is not None else 0
            ps = float(row.get('ps', 0)) if row.get('ps') is not None else 0
            ps_ttm = float(row.get('ps_ttm', 0)) if row.get('ps_ttm') is not None else 0
            dv_ratio = float(row.get('dv_ratio', 0)) if row.get('dv_ratio') is not None else 0
            dv_ttm = float(row.get('dv_ttm', 0)) if row.get('dv_ttm') is not None else 0
            total_share = float(row.get('total_share', 0)) if row.get('total_share') is not None else 0
            float_share = float(row.get('float_share', 0)) if row.get('float_share') is not None else 0
            free_share = float(row.get('free_share', 0)) if row.get('free_share') is not None else 0
            total_mv = float(row.get('total_mv', 0)) if row.get('total_mv') is not None else 0
            circ_mv = float(row.get('circ_mv', 0)) if row.get('circ_mv') is not None else 0
            is_limit_down = int(row['is_limit_down'])

            cursor.execute(insert_sql, (
                stock_name, stock_code, trade_date, low_price, high_price, open_price, close_price,
                turnover_amount, trading_volume, turnover_rate, price_change_rate, previous_close_price,
                call_auction_increase, ma_5, ma_10, ma_20, ma_60, boll_low, boll_mid, boll_up, kdj, macd,
                industry_sector, concept_sector, is_limit_up, is_board_broken,
                up_limit, down_limit, turnover_rate_f, volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, dv_ratio, dv_ttm,
                total_share, float_share, free_share, total_mv, circ_mv, is_limit_down
            ))
            conn.commit()
            print(f"插入 {stock_code} {trade_date} 数据成功")
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            last_frame = tb[-1]
            line_number = last_frame.lineno
            print(f"插入 {stock_code} {trade_date} 数据时出错: {e}，错误发生在第 {line_number} 行")
            print(traceback.format_exc())
            conn.rollback()

def update_turnover_avg(daily_data, specified_date):
    """
    更新指定日期的成交额移动平均数据
    :param daily_data: DataFrame 包含股票日线数据
    :param specified_date: 指定日期，格式为 'YYYYMMDD'
    :param conn: 数据库连接
    """
    try:
        conn, cursor = check_connection()
        
        # 使用传入的daily_data，只需要提取需要的列
        df = daily_data[['ts_code', 'trade_date', 'amount']].copy()
        df.columns = ['stock_code', 'trade_date', 'turnover_amount']
        
        # 按股票代码分组
        grouped = df.groupby('stock_code')
        
        # 存储结果的列表
        results = []
        
        # 对每个股票进行处理
        for stock_code, group in grouped:
            # 按日期排序
            group = group.sort_values('trade_date')
            
            # 计算不同天数的平均成交额
            group['avg_1d'] = group['turnover_amount']
            group['avg_2d'] = group['turnover_amount'].rolling(window=2).mean()
            group['avg_3d'] = group['turnover_amount'].rolling(window=3).mean()
            group['avg_4d'] = group['turnover_amount'].rolling(window=4).mean()
            group['avg_5d'] = group['turnover_amount'].rolling(window=5).mean()
            
            # 将NaN值替换为0
            group = group.fillna(0)
            
            # 只保留指定日期的数据
            group = group[group['trade_date'] == specified_date]
            
            # 添加到结果列表
            if not group.empty:
                results.append(group[['stock_code', 'trade_date', 'avg_1d', 'avg_2d', 'avg_3d', 'avg_4d', 'avg_5d']])
        
        if results:
            # 合并所有结果
            result_df = pd.concat(results)
            
            # 准备插入语句
            insert_sql = """
            INSERT IGNORE INTO stock_turnover_avg 
            (stock_code, trade_date, avg_1d, avg_2d, avg_3d, avg_4d, avg_5d)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            # 插入数据
            for _, row in result_df.iterrows():
                try:
                    cursor.execute(insert_sql, (
                        row['stock_code'],
                        row['trade_date'],
                        float(row['avg_1d']),
                        float(row['avg_2d']),
                        float(row['avg_3d']),
                        float(row['avg_4d']),
                        float(row['avg_5d'])
                    ))
                    conn.commit()
                except Exception as e:
                    print(f"更新成交额移动平均数据时出错: {e}")
                    print(traceback.format_exc())
                    conn.rollback()
            
            print(f"Successfully updated turnover amount averages for {specified_date}")
            
    except Exception as e:
        print(f"更新成交额移动平均数据时出错: {e}")
        print(traceback.format_exc())
        if 'conn' in locals():
            conn.rollback()

def calculate_up_down_stats(specified_date, conn):
    """
    计算指定日期的上涨下跌家数统计
    """
    cursor = conn.cursor()
    
    try:
        # 使用SQL直接统计上涨下跌家数
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN price_change_rate > 0 THEN 1 ELSE 0 END) as up_count,
                SUM(CASE WHEN price_change_rate < 0 THEN 1 ELSE 0 END) as down_count
            FROM daily_data
            WHERE trade_date = %s
        """, (specified_date,))
        
        result = cursor.fetchone()
        
        stats = {
            'up_count': int(result[0]) if result[0] else 0,
            'down_count': int(result[1]) if result[1] else 0
        }
        
        # 插入统计数据
        insert_sql = """
            INSERT INTO limit_stats (trade_date, item, count)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE count = VALUES(count)
        """
        
        for item, count in stats.items():
            cursor.execute(insert_sql, (specified_date, item, count))
        
        conn.commit()
        print(f"成功插入{specified_date}的上涨下跌统计：上涨{stats['up_count']}家，"
              f"下跌{stats['down_count']}家")
        
    except Exception as e:
        print(f"计算或插入{specified_date}的上涨下跌统计数据时出错: {str(e)}")
        conn.rollback()

def process_stock_batch(stock_batch, specified_date, sixty_days_ago):
    """
    处理一批股票数据
    """
    try:
        for ts_code, stock_code, stock_name in stock_batch:
            try:
                # 检查数据是否已存在
                if check_data_exists(stock_code, specified_date):
                    print(f"{stock_code} 在 {specified_date} 的数据已存在，跳过。")
                    continue

                # 获取指定日期前 60 天内的日线数据
                pro = get_pro()
                daily_data = pro.daily(ts_code=ts_code, start_date=sixty_days_ago, end_date=specified_date)
                if not daily_data.empty:
                    # 按日期升序排序
                    daily_data = daily_data.sort_values(by='trade_date')

                    # 获取指定日期的基本面数据
                    daily_basic_data = pro.daily_basic(ts_code=ts_code, trade_date=specified_date)
                    if not daily_basic_data.empty:
                        # 合并基本面数据到日线数据，指定 suffixes 为空字符串
                        merged_data = pd.merge(daily_data, daily_basic_data, on=['ts_code', 'trade_date'], how='left', suffixes=('', '_drop'))
                        # 删除多余的列
                        columns_to_drop = [col for col in merged_data.columns if col.endswith('_drop')]
                        daily_data = merged_data.drop(columns=columns_to_drop)

                    # 获取指定日期的涨跌停价格
                    stk_limit_data = pro.stk_limit(ts_code=ts_code, trade_date=specified_date)
                    if not stk_limit_data.empty:
                        # 合并涨跌停价格数据到日线数据
                        daily_data = pd.merge(daily_data, stk_limit_data, on=['ts_code', 'trade_date'], how='left')

                    # 计算技术指标
                    daily_data = calculate_indicators(daily_data)
                    # 计算是否涨停、是否炸板和是否跌停
                    daily_data = calculate_limit_info(daily_data, stock_name)
                    # 插入指定日期的数据到 daily_data 表
                    insert_into_daily_data_table(stock_code, stock_name, daily_data, specified_date)
                    update_turnover_avg(daily_data, specified_date)
                    print(f"{stock_code} 数据插入成功。")
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)
                last_frame = tb[-1]
                line_number = last_frame.lineno
                print(f"获取 {stock_code} 数据时出错: {e}，错误发生在第 {line_number} 行")
                print(traceback.format_exc())
    finally:
        # 确保关闭当前线程的数据库连接
        if hasattr(thread_local, "conn") and thread_local.conn is not None:
            thread_local.conn.close()
            thread_local.conn = None
        if hasattr(thread_local, "cursor") and thread_local.cursor is not None:
            thread_local.cursor = None

if __name__ == "__main__":
    try:
        # 等待直到17:00
        while True:
            try:
                current_time = datetime.now()
                target_time = current_time.replace(hour=17, minute=0, second=0, microsecond=0)
                
                if current_time.hour < 17 and False:
                    # 计算到17:00还需要多少秒
                    wait_seconds = (target_time - current_time).total_seconds()
                    print(f"当前时间: {current_time.strftime('%H:%M:%S')}, 等待到17:00执行，还需等待 {int(wait_seconds)} 秒")
                    time.sleep(60)  # 每分钟检查一次
                    continue
                
                print(f"开始执行数据加载任务，当前时间: {current_time.strftime('%H:%M:%S')}")
            
                # 指定日期，格式为 'YYYYMMDD'
                specified_date = "20251024"
                specified_date_obj = datetime.strptime(specified_date, '%Y%m%d')
                sixty_days_ago = (specified_date_obj - timedelta(days=120)).strftime('%Y%m%d')

                # 获取所有股票代码
                all_codes = get_all_stock_codes()
                
                # 将股票列表分成40个批次
                batch_size = max(1, len(all_codes) // 3)
                stock_batches = [all_codes[i:i + batch_size] for i in range(0, len(all_codes), batch_size)]
                
                # 使用线程池处理数据
                with ThreadPoolExecutor(max_workers=3) as executor:
                    try:
                        # 创建所有任务
                        futures = [
                            executor.submit(process_stock_batch, batch, specified_date, sixty_days_ago)
                            for batch in stock_batches
                        ]
                        
                        # 等待所有任务完成
                        for future in as_completed(futures):
                            try:
                                future.result()
                            except Exception as e:
                                print(f"批次处理失败: {e}")
                                print(traceback.format_exc())
                    except KeyboardInterrupt:
                        print("\n检测到 CTRL+C，正在优雅地关闭所有线程...")
                        executor.shutdown(wait=False)
                        raise KeyboardInterrupt

                # 计算上涨下跌统计
                conn = get_db_connection()
                calculate_up_down_stats(specified_date, conn)
                conn.close()
                
                # 任务完成后等待到第二天
                print("今天的任务已完成，等待到明天17:00继续执行")
                time.sleep(3600)

            except KeyboardInterrupt:
                print("\n程序被用户中断")
                break
            except Exception as e:
                print(f"处理数据时出错: {e}")
                print(traceback.format_exc())
                # 发生错误时等待一段时间再重试
                time.sleep(300)  # 等待5分钟后重试

    except Exception as e:
        print(f"程序发生严重错误: {e}")
        print(traceback.format_exc())

    finally:
        print("\n正在清理资源...")
        # 确保关闭所有数据库连接
        if hasattr(thread_local, "conn") and thread_local.conn is not None:
            thread_local.conn.close()
            thread_local.conn = None
        if hasattr(thread_local, "cursor") and thread_local.cursor is not None:
            thread_local.cursor = None
        print("程序已安全退出")
