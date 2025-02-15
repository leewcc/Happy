import tushare as ts
import pymysql
import pandas as pd
from ta.trend import SMAIndicator, MACD
from ta.volatility import BollingerBands
from ta.momentum import StochasticOscillator
from datetime import datetime, timedelta

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

def get_120_days_data(ts_code, specified_date):
    """
    获取指定日期的近 120 天的日线数据
    :param ts_code: 指数代码
    :param specified_date: 指定日期，格式为 'YYYYMMDD'
    :return: 近 120 天的日线数据 DataFrame
    """
    specified_date_obj = datetime.strptime(specified_date, '%Y%m%d')
    start_date = (specified_date_obj - timedelta(days=120)).strftime('%Y%m%d')
    df = pro.index_daily(ts_code=ts_code, start_date=start_date, end_date=specified_date)
    if not df.empty:
        df = df.sort_values(by='trade_date')
    return df

def calculate_indicators_for_date(data, specified_date):
    """
    计算指定日期的技术指标
    :param data: 近 120 天的日线数据 DataFrame
    :param specified_date: 指定日期，格式为 'YYYYMMDD'
    :return: 指定日期的数据及技术指标 DataFrame
    """
    # 计算均线
    data['ma_5'] = SMAIndicator(data['close'], window=5).sma_indicator()
    data['ma_10'] = SMAIndicator(data['close'], window=10).sma_indicator()
    data['ma_20'] = SMAIndicator(data['close'], window=20).sma_indicator()
    data['ma_60'] = SMAIndicator(data['close'], window=60).sma_indicator()

    # 计算布林带
    bollinger = BollingerBands(data['close'])
    data['boll_up'] = bollinger.bollinger_hband()
    data['boll_mid'] = bollinger.bollinger_mavg()
    data['boll_low'] = bollinger.bollinger_lband()

    # 计算 KDJ
    kdj = StochasticOscillator(data['high'], data['low'], data['close'])
    data['kdj'] = kdj.stoch()

    # 计算 MACD
    macd = MACD(data['close'])
    data['macd'] = macd.macd()

    # 筛选指定日期的数据
    specified_date_data = data[data['trade_date'] == specified_date]
    return specified_date_data

def insert_specified_date_data(ts_code, data):
    """
    插入指定日期的数据到数据库
    :param ts_code: 指数代码
    :param data: 指定日期的数据及技术指标 DataFrame
    """
    insert_sql = """
    INSERT IGNORE INTO index_daily_data (ts_code, trade_date, close, open, high, low, pre_close, price_change, pct_chg, vol, amount, ma_5, ma_10, ma_20, ma_60, boll_up, boll_mid, boll_low, kdj, macd)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    for index, row in data.iterrows():
        values = [
            row['ts_code'],
            row['trade_date'],
            float(row['close']) if pd.notna(row['close']) else None,
            float(row['open']) if pd.notna(row['open']) else None,
            float(row['high']) if pd.notna(row['high']) else None,
            float(row['low']) if pd.notna(row['low']) else None,
            float(row['pre_close']) if pd.notna(row['pre_close']) else None,
            float(row['change']) if pd.notna(row['change']) else None,
            float(row['pct_chg']) if pd.notna(row['pct_chg']) else None,
            float(row['vol']) if pd.notna(row['vol']) else None,
            float(row['amount']) if pd.notna(row['amount']) else None,
            float(row['ma_5']) if pd.notna(row['ma_5']) else None,
            float(row['ma_10']) if pd.notna(row['ma_10']) else None,
            float(row['ma_20']) if pd.notna(row['ma_20']) else None,
            float(row['ma_60']) if pd.notna(row['ma_60']) else None,
            float(row['boll_up']) if pd.notna(row['boll_up']) else None,
            float(row['boll_mid']) if pd.notna(row['boll_mid']) else None,
            float(row['boll_low']) if pd.notna(row['boll_low']) else None,
            float(row['kdj']) if pd.notna(row['kdj']) else None,
            float(row['macd']) if pd.notna(row['macd']) else None
        ]
        try:
            cursor.execute(insert_sql, values)
            conn.commit()
            print(f"插入 {ts_code} 在 {row['trade_date']} 的数据成功。")
        except pymysql.Error as e:
            print(f"插入 {ts_code} 在 {row['trade_date']} 的数据时出错: {e}")
            conn.rollback()

if __name__ == "__main__":
    # 从 index_info 表中获取所有指数代码
    cursor.execute("SELECT ts_code FROM index_info")
    index_codes = [row[0] for row in cursor.fetchall()]

    # 指定日期，格式为 'YYYYMMDD'
    specified_date = '20250214'

    for ts_code in index_codes:
        try:
            # 获取近 120 天的日线数据
            data = get_120_days_data(ts_code, specified_date)
            if not data.empty:
                # 计算指定日期的技术指标
                specified_date_data = calculate_indicators_for_date(data, specified_date)
                if not specified_date_data.empty:
                    # 插入指定日期的数据到数据库
                    insert_specified_date_data(ts_code, specified_date_data)
                else:
                    print(f"未找到 {ts_code} 在 {specified_date} 的数据。")
            else:
                print(f"未获取到 {ts_code} 的近 120 天日线数据。")
        except Exception as e:
            print(f"处理 {ts_code} 数据时出错: {e}")

    # 关闭数据库连接
    cursor.close()
    conn.close()