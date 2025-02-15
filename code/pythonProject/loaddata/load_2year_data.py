import tushare as ts
import pymysql
import pandas as pd
from ta.trend import SMAIndicator, MACD
from ta.volatility import BollingerBands
from ta.momentum import StochasticOscillator
from datetime import datetime, timedelta
from decimal import Decimal
import traceback

# 设置 Tushare Pro 的 token
ts.set_token('a880b180343bdf47d774721036dabac9f9dd7ec3952c80fbe8ba515e')
pro = ts.pro_api()

# 连接到 MySQL 数据库
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='happy',
    charset='utf8mb4'
)
cursor = conn.cursor()

# 计算近 5 年的日期范围
five_years_ago = (datetime.now() - timedelta(days=365 * 5)).strftime('%Y%m%d')
today = datetime.now().strftime('%Y%m%d')

# 删除 daily_data 表中的所有数据
try:
    cursor.execute("TRUNCATE TABLE daily_data")
    conn.commit()
    print("成功清空 daily_data 表中的数据。")
except Exception as e:
    print(f"清空 daily_data 表数据时出错: {e}")


def get_all_stock_codes():
    """
    从 Tushare Pro 获取所有股票代码
    :return: 包含所有股票代码的列表
    """
    try:
        data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name')
        all_codes = data[['ts_code', 'symbol', 'name']].values.tolist()
        return all_codes
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        last_frame = tb[-1]
        line_number = last_frame.lineno
        print(f"从 Tushare Pro 获取股票代码时出错: {e}，错误发生在第 {line_number} 行")
        print(traceback.format_exc())
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


def insert_into_daily_data_table(stock_code, stock_name, data):
    """
    将日线数据插入到 daily_data 表中
    :param stock_code: 股票代码
    :param stock_name: 股票名称
    :param data: 包含日线数据和技术指标的 DataFrame
    """
    insert_sql = """
    INSERT INTO daily_data (stock_name, stock_code, trade_date, low_price, high_price, open_price, close_price, 
    turnover_amount, trading_volume, turnover_rate, price_change_rate, previous_close_price, call_auction_increase, 
    ma_5, ma_10, ma_20, ma_60, boll_low, boll_mid, boll_up, kdj, macd, industry_sector, concept_sector, is_limit_up, is_board_broken,
    up_limit, down_limit, turnover_rate_f, volume_ratio, pe, pe_ttm, pb, ps, ps_ttm, dv_ratio, dv_ttm, total_share, float_share, free_share, total_mv, circ_mv, is_limit_down) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    for index, row in data.iterrows():
        try:
            trade_date = row['trade_date']
            low_price = float(row['low']) if pd.notna(row['low']) else 0
            high_price = float(row['high']) if pd.notna(row['high']) else 0
            open_price = float(row['open']) if pd.notna(row['open']) else 0
            close_price = float(row['close']) if pd.notna(row['close']) else 0
            turnover_amount = float(row['amount']) if pd.notna(row['amount']) else 0
            trading_volume = float(row['vol']) if pd.notna(row['vol']) else 0
            turnover_rate = float(row.get('turnover_rate', 0))
            price_change_rate = float(row.get('pct_chg', 0))
            previous_close_price = float(row.get('pre_close', 0))
            call_auction_increase = None  # 暂时设为 None，可根据实际情况修改
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

            up_limit = float(row.get('up_limit', 0)) if pd.notna(row.get('up_limit')) else 0
            down_limit = float(row.get('down_limit', 0)) if pd.notna(row.get('down_limit')) else 0
            turnover_rate_f = float(row.get('turnover_rate_f', 0)) if pd.notna(row.get('turnover_rate_f')) else 0
            volume_ratio = float(row.get('volume_ratio', 0)) if pd.notna(row.get('volume_ratio')) else 0
            pe = float(row.get('pe', 0)) if pd.notna(row.get('pe', 0)) else None
            pe_ttm = float(row.get('pe_ttm', 0)) if pd.notna(row.get('pe_ttm', 0)) else None
            pb = float(row.get('pb', 0)) if pd.notna(row.get('pb')) else 0
            ps = float(row.get('ps', 0)) if pd.notna(row.get('ps')) else 0
            ps_ttm = float(row.get('ps_ttm', 0)) if pd.notna(row.get('ps_ttm')) else 0
            dv_ratio = float(row.get('dv_ratio', 0)) if pd.notna(row.get('dv_ratio')) else 0
            dv_ttm = float(row.get('dv_ttm', 0)) if pd.notna(row.get('dv_ttm')) else None
            total_share = float(row.get('total_share', 0)) if pd.notna(row.get('total_share')) else 0
            float_share = float(row.get('float_share', 0)) if pd.notna(row.get('float_share')) else 0
            free_share = float(row.get('free_share', 0)) if pd.notna(row.get('free_share')) else 0
            total_mv = float(row.get('total_mv', 0)) if pd.notna(row.get('total_mv')) else 0
            circ_mv = float(row.get('circ_mv', 0)) if pd.notna(row.get('circ_mv')) else 0
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

if __name__ == "__main__":
    all_codes = get_all_stock_codes()
    for ts_code, stock_code, stock_name in all_codes:
        try:
            # 获取日线数据
            daily_data = pro.daily(ts_code=ts_code, start_date=five_years_ago, end_date=today)
            if not daily_data.empty:
                # 按日期升序排序
                daily_data = daily_data.sort_values(by='trade_date')

                # 获取基本面数据
                daily_basic_data = pro.daily_basic(ts_code=ts_code, start_date=five_years_ago, end_date=today)
                if not daily_basic_data.empty:
                    # 合并基本面数据到日线数据，指定 suffixes 为空字符串
                    merged_data = pd.merge(daily_data, daily_basic_data, on=['ts_code', 'trade_date'], how='left', suffixes=('', '_drop'))
                    # 删除多余的列
                    columns_to_drop = [col for col in merged_data.columns if col.endswith('_drop')]
                    daily_data = merged_data.drop(columns=columns_to_drop)

                # 获取涨跌停价格数据
                stk_limit_data = pro.stk_limit(ts_code=ts_code, start_date=five_years_ago, end_date=today)
                if not stk_limit_data.empty:
                    # 合并涨跌停价格数据到日线数据
                    daily_data = pd.merge(daily_data, stk_limit_data, on=['ts_code', 'trade_date'], how='left')

                # 计算技术指标
                daily_data = calculate_indicators(daily_data)
                # 计算是否涨停、是否炸板和是否跌停
                daily_data = calculate_limit_info(daily_data, stock_name)
                # 插入数据到 daily_data 表
                insert_into_daily_data_table(stock_code, stock_name, daily_data)
                print(f"{stock_code} 数据插入成功。")
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            last_frame = tb[-1]
            line_number = last_frame.lineno
            print(f"获取 {stock_code} 数据时出错: {e}，错误发生在第 {line_number} 行")
            print(traceback.format_exc())

    # 关闭数据库连接
    cursor.close()
    conn.close()