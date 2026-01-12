"""
手动插入股票日线数据工具
支持输入股票代码、日期、价格等数据，自动计算技术指标并插入到 daily_data 表
"""
import pymysql
import pandas as pd
from ta.trend import SMAIndicator, MACD
from ta.volatility import BollingerBands
from ta.momentum import StochasticOscillator
from datetime import datetime, timedelta
from decimal import Decimal
import traceback
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'happy',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def get_stock_name(stock_code):
    """从数据库获取股票名称"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT name FROM stock WHERE stock_code = %s"
        cursor.execute(sql, (stock_code,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"获取股票名称失败: {e}")
        return None

def get_historical_data(stock_code, trade_date, days=120):
    """
    从数据库获取历史数据用于计算技术指标
    :param stock_code: 股票代码
    :param trade_date: 交易日期 (YYYYMMDD格式字符串)
    :param days: 需要获取的历史天数
    :return: DataFrame包含历史数据
    """
    try:
        conn = get_db_connection()
        
        # 将日期字符串转换为日期对象
        date_obj = datetime.strptime(trade_date, '%Y%m%d')
        start_date = (date_obj - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = (date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
        
        sql = """
        SELECT 
            trade_date,
            open_price as open,
            close_price as close,
            high_price as high,
            low_price as low,
            turnover_amount as amount,
            trading_volume as vol,
            price_change_rate as pct_chg,
            previous_close_price as pre_close
        FROM daily_data
        WHERE stock_code = %s 
        AND trade_date < %s
        AND trade_date >= %s
        ORDER BY trade_date ASC
        """
        
        # 使用 cursor 执行查询以避免 pandas 警告
        cursor = conn.cursor()
        cursor.execute(sql, (stock_code, date_obj.strftime('%Y-%m-%d'), start_date))
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=columns)
        cursor.close()
        conn.close()
        
        # 转换日期格式为 YYYYMMDD
        if not df.empty:
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y%m%d')
        
        return df
    except Exception as e:
        print(f"获取历史数据失败: {e}")
        print(traceback.format_exc())
        return pd.DataFrame()

def calculate_indicators(data):
    """
    计算技术指标
    :param data: 包含日线数据的 DataFrame
    :return: 包含技术指标的 DataFrame
    """
    try:
        if data.empty or len(data) < 5:
            print("数据不足，无法计算技术指标")
            return data
        
        # 确保数据类型正确
        data['close'] = pd.to_numeric(data['close'], errors='coerce')
        data['high'] = pd.to_numeric(data['high'], errors='coerce')
        data['low'] = pd.to_numeric(data['low'], errors='coerce')
        
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
        print(f"计算技术指标时出错: {e}")
        print(traceback.format_exc())
        return data

def calculate_limit_info(data, stock_name):
    """
    计算是否涨停、是否炸板和是否跌停
    :param data: 包含日线数据的 DataFrame
    :param stock_name: 股票名称
    :return: 包含计算结果的 DataFrame
    """
    try:
        limit_ratio = Decimal('0.1') if stock_name and 'ST' not in stock_name else Decimal('0.05')
        
        # 如果 up_limit 和 down_limit 不存在，使用计算方式获取
        if 'up_limit' not in data.columns or 'down_limit' not in data.columns:
            if 'pre_close' not in data.columns:
                # 如果没有前收盘价，使用前一天的收盘价
                data['pre_close'] = data['close'].shift(1)
            
            data['up_limit'] = data['pre_close'].apply(
                lambda x: Decimal(str(x)) * (Decimal('1') + limit_ratio) if pd.notna(x) and x != 0 else None
            )
            data['down_limit'] = data['pre_close'].apply(
                lambda x: Decimal(str(x)) * (Decimal('1') - limit_ratio) if pd.notna(x) and x != 0 else None
            )

        # 调整是否涨停的判断逻辑
        data['is_limit_up'] = (
            data['close'].apply(lambda x: Decimal(str(x)) if pd.notna(x) else None) == 
            data['up_limit'].apply(lambda x: Decimal(str(x)) if pd.notna(x) else None)
        ).fillna(False).astype(int)
        
        # 调整是否炸板的判断逻辑
        data['is_board_broken'] = (
            (data['high'].apply(lambda x: Decimal(str(x)) if pd.notna(x) else None) == 
             data['up_limit'].apply(lambda x: Decimal(str(x)) if pd.notna(x) else None)) &
            (data['close'].apply(lambda x: Decimal(str(x)) if pd.notna(x) else None) != 
             data['up_limit'].apply(lambda x: Decimal(str(x)) if pd.notna(x) else None))
        ).fillna(False).astype(int)
        
        data['is_limit_down'] = (
            data['close'].apply(lambda x: Decimal(str(x)) if pd.notna(x) else None) == 
            data['down_limit'].apply(lambda x: Decimal(str(x)) if pd.notna(x) else None)
        ).fillna(False).astype(int)
        
        return data
    except Exception as e:
        print(f"计算涨跌停相关信息时出错: {e}")
        print(traceback.format_exc())
        return data

def insert_daily_data(stock_code, stock_name, trade_date, open_price, close_price, 
                     high_price, low_price, turnover_amount, trading_volume=0):
    """
    手动插入股票日线数据
    :param stock_code: 股票代码 (如: 300456)
    :param stock_name: 股票名称 (可选，如果不提供则从数据库查询)
    :param trade_date: 交易日期 (格式: YYYYMMDD，如: 20251216)
    :param open_price: 开盘价
    :param close_price: 收盘价
    :param high_price: 最高价
    :param low_price: 最低价
    :param turnover_amount: 成交额
    :param trading_volume: 成交量 (可选，默认为0)
    """
    try:
        # 获取股票名称
        if not stock_name:
            stock_name = get_stock_name(stock_code)
            if not stock_name:
                print(f"未找到股票代码 {stock_code}，请先确保股票已存在于 stock 表中")
                return False
        
        # 检查数据是否已存在
        date_obj = datetime.strptime(trade_date, '%Y%m%d')
        conn = get_db_connection()
        cursor = conn.cursor()
        check_sql = "SELECT COUNT(*) FROM daily_data WHERE stock_code = %s AND trade_date = %s"
        cursor.execute(check_sql, (stock_code, date_obj.strftime('%Y-%m-%d')))
        exists = cursor.fetchone()[0] > 0
        cursor.close()
        conn.close()
        
        if exists:
            print(f"警告: 股票 {stock_code} 在 {trade_date} 的数据已存在，将更新现有数据")
        
        # 获取历史数据（包含当前日期之前的所有数据）
        print(f"正在获取股票 {stock_code} 的历史数据...")
        historical_data = get_historical_data(stock_code, trade_date, days=120)
        
        # 检查数据库中是否已存在当前日期的数据
        conn_check = get_db_connection()
        cursor_check = conn_check.cursor()
        check_current_sql = """
        SELECT 
            trade_date,
            open_price as open,
            close_price as close,
            high_price as high,
            low_price as low,
            turnover_amount as amount,
            trading_volume as vol,
            price_change_rate as pct_chg,
            previous_close_price as pre_close
        FROM daily_data
        WHERE stock_code = %s AND trade_date = %s
        """
        cursor_check.execute(check_current_sql, (stock_code, date_obj.strftime('%Y-%m-%d')))
        existing_row = cursor_check.fetchone()
        cursor_check.close()
        conn_check.close()
        
        # 构建新数据行（始终使用新输入的数据）
        new_row = {
            'trade_date': trade_date,
            'open': float(open_price),
            'close': float(close_price),
            'high': float(high_price),
            'low': float(low_price),
            'amount': float(turnover_amount),
            'vol': float(trading_volume),
            'pct_chg': None,  # 将在后面计算
            'pre_close': None  # 将从历史数据获取
        }
        
        # 如果有历史数据，获取前收盘价
        if not historical_data.empty:
            last_close = historical_data.iloc[-1]['close']
            new_row['pre_close'] = float(last_close)
            # 计算涨跌幅
            if last_close and last_close > 0:
                new_row['pct_chg'] = ((float(close_price) - float(last_close)) / float(last_close)) * 100
        
        # 如果数据库中已存在该日期的数据，从历史数据中移除它（避免重复）
        if existing_row:
            # 移除历史数据中可能存在的当前日期数据（虽然查询时已经排除了，但为了安全起见）
            if not historical_data.empty:
                historical_data = historical_data[historical_data['trade_date'] != trade_date]
        
        # 合并历史数据和新数据
        if not historical_data.empty:
            # 将新数据添加到历史数据末尾
            new_df = pd.DataFrame([new_row])
            combined_data = pd.concat([historical_data, new_df], ignore_index=True)
        else:
            # 如果没有历史数据，只使用新数据
            combined_data = pd.DataFrame([new_row])
            print("警告: 没有找到历史数据，技术指标可能不准确")
        
        # 计算技术指标
        print("正在计算技术指标...")
        combined_data = calculate_indicators(combined_data)
        
        # 计算涨跌停信息
        combined_data = calculate_limit_info(combined_data, stock_name)
        
        # 获取最后一行（即新插入的数据）
        new_data = combined_data.iloc[-1]
        
        # 准备插入数据（重新创建连接）
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_sql = """
        INSERT INTO daily_data (
            stock_name, stock_code, trade_date, low_price, high_price, open_price, close_price, 
            turnover_amount, trading_volume, turnover_rate, price_change_rate, previous_close_price, 
            call_auction_increase, ma_5, ma_10, ma_20, ma_60, boll_low, boll_mid, boll_up, 
            kdj, macd, industry_sector, concept_sector, is_limit_up, is_board_broken,
            up_limit, down_limit, turnover_rate_f, volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, 
            dv_ratio, dv_ttm, total_share, float_share, free_share, total_mv, circ_mv, is_limit_down
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON DUPLICATE KEY UPDATE
            stock_name = VALUES(stock_name),
            low_price = VALUES(low_price),
            high_price = VALUES(high_price),
            open_price = VALUES(open_price),
            close_price = VALUES(close_price),
            turnover_amount = VALUES(turnover_amount),
            trading_volume = VALUES(trading_volume),
            turnover_rate = VALUES(turnover_rate),
            price_change_rate = VALUES(price_change_rate),
            previous_close_price = VALUES(previous_close_price),
            call_auction_increase = VALUES(call_auction_increase),
            ma_5 = VALUES(ma_5),
            ma_10 = VALUES(ma_10),
            ma_20 = VALUES(ma_20),
            ma_60 = VALUES(ma_60),
            boll_low = VALUES(boll_low),
            boll_mid = VALUES(boll_mid),
            boll_up = VALUES(boll_up),
            kdj = VALUES(kdj),
            macd = VALUES(macd),
            industry_sector = VALUES(industry_sector),
            concept_sector = VALUES(concept_sector),
            is_limit_up = VALUES(is_limit_up),
            is_board_broken = VALUES(is_board_broken),
            up_limit = VALUES(up_limit),
            down_limit = VALUES(down_limit),
            turnover_rate_f = VALUES(turnover_rate_f),
            volume_ratio = VALUES(volume_ratio),
            pe = VALUES(pe),
            pe_ttm = VALUES(pe_ttm),
            pb = VALUES(pb),
            ps = VALUES(ps),
            ps_ttm = VALUES(ps_ttm),
            dv_ratio = VALUES(dv_ratio),
            dv_ttm = VALUES(dv_ttm),
            total_share = VALUES(total_share),
            float_share = VALUES(float_share),
            free_share = VALUES(free_share),
            total_mv = VALUES(total_mv),
            circ_mv = VALUES(circ_mv),
            is_limit_down = VALUES(is_limit_down)
        """
        
        # 准备参数
        params = (
            stock_name,
            stock_code,
            date_obj.strftime('%Y-%m-%d'),
            float(new_data['low']) if pd.notna(new_data['low']) else 0,
            float(new_data['high']) if pd.notna(new_data['high']) else 0,
            float(new_data['open']) if pd.notna(new_data['open']) else 0,
            float(new_data['close']) if pd.notna(new_data['close']) else 0,
            float(new_data['amount']) if pd.notna(new_data['amount']) else 0,
            float(new_data['vol']) if pd.notna(new_data['vol']) else 0,
            None,  # turnover_rate
            float(new_data['pct_chg']) if pd.notna(new_data['pct_chg']) else None,  # price_change_rate
            float(new_data['pre_close']) if pd.notna(new_data['pre_close']) else None,  # previous_close_price
            None,  # call_auction_increase
            float(new_data['ma_5']) if pd.notna(new_data['ma_5']) else None,
            float(new_data['ma_10']) if pd.notna(new_data['ma_10']) else None,
            float(new_data['ma_20']) if pd.notna(new_data['ma_20']) else None,
            float(new_data['ma_60']) if pd.notna(new_data['ma_60']) else None,
            float(new_data['boll_low']) if pd.notna(new_data['boll_low']) else None,
            float(new_data['boll_mid']) if pd.notna(new_data['boll_mid']) else None,
            float(new_data['boll_up']) if pd.notna(new_data['boll_up']) else None,
            float(new_data['kdj']) if pd.notna(new_data['kdj']) else None,
            float(new_data['macd']) if pd.notna(new_data['macd']) else None,
            '',  # industry_sector
            '',  # concept_sector
            int(new_data['is_limit_up']) if pd.notna(new_data['is_limit_up']) else 0,
            int(new_data['is_board_broken']) if pd.notna(new_data['is_board_broken']) else 0,
            float(new_data['up_limit']) if 'up_limit' in new_data and pd.notna(new_data['up_limit']) else None,
            float(new_data['down_limit']) if 'down_limit' in new_data and pd.notna(new_data['down_limit']) else None,
            None,  # turnover_rate_f
            None,  # volume_ratio
            None,  # pe
            None,  # pe_ttm
            None,  # pb
            None,  # ps
            None,  # ps_ttm
            None,  # dv_ratio
            None,  # dv_ttm
            None,  # total_share
            None,  # float_share
            None,  # free_share
            None,  # total_mv
            None,  # circ_mv
            int(new_data['is_limit_down']) if pd.notna(new_data['is_limit_down']) else 0
        )
        
        cursor.execute(insert_sql, params)
        conn.commit()
        
        print(f"成功插入股票 {stock_code} ({stock_name}) 在 {trade_date} 的数据")
        print(f"  开盘价: {open_price}, 收盘价: {close_price}")
        print(f"  最高价: {high_price}, 最低价: {low_price}")
        print(f"  成交额: {turnover_amount}")
        if pd.notna(new_data['ma_5']):
            print(f"  MA5: {new_data['ma_5']:.2f}, MA10: {new_data['ma_10']:.2f}, MA20: {new_data['ma_20']:.2f}, MA60: {new_data['ma_60']:.2f}")
        if pd.notna(new_data['boll_mid']):
            print(f"  布林带: 上轨={new_data['boll_up']:.2f}, 中轨={new_data['boll_mid']:.2f}, 下轨={new_data['boll_low']:.2f}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"插入数据失败: {e}")
        print(traceback.format_exc())
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def check_connection():
    """检查连接是否有效"""
    try:
        conn = get_db_connection()
        conn.ping(reconnect=True)
        return conn, conn.cursor()
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None, None

if __name__ == "__main__":
    """
    使用示例:
    python manual_insert_daily_data.py
    """
    print("=" * 60)
    print("手动插入股票日线数据工具")
    print("=" * 60)
    
    # 示例：插入股票 300456 在 20251216 的数据
    # 你可以修改这些参数
    stock_code = "300456"
    stock_name = '赛微电子'  # 如果为 None，将从数据库查询
    trade_date = "20251218"
    open_price = 60
    close_price = 71.15
    high_price = 60
    low_price = 71.15
    turnover_amount = 9000000  # 成交额（元）
    trading_volume = 10000000    # 成交量（手），可选
    
    print(f"\n准备插入数据:")
    print(f"  股票代码: {stock_code}")
    print(f"  交易日期: {trade_date}")
    print(f"  开盘价: {open_price}")
    print(f"  收盘价: {close_price}")
    print(f"  最高价: {high_price}")
    print(f"  最低价: {low_price}")
    print(f"  成交额: {turnover_amount}")
    print(f"  成交量: {trading_volume}")
    print()
    
    # 调用插入函数
    success = insert_daily_data(
        stock_code=stock_code,
        stock_name=stock_name,
        trade_date=trade_date,
        open_price=open_price,
        close_price=close_price,
        high_price=high_price,
        low_price=low_price,
        turnover_amount=turnover_amount,
        trading_volume=trading_volume
    )
    
    if success:
        print("\n数据插入成功！")
    else:
        print("\n数据插入失败！")

