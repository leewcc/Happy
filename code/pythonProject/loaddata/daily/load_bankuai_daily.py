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


def get_data(ts_code, start_date, end_date):
    """
    获取指定指数代码和日期范围的数据
    :param ts_code: 指数代码
    :param start_date: 开始日期
    :param end_date: 结束日期
    :return: 数据 DataFrame
    """
    df = pro.ths_daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
    if not df.empty:
        df = df.sort_values(by='trade_date')
    return df


def calculate_indicators(data):
    """
    计算技术指标
    :param data: 数据 DataFrame
    :return: 包含技术指标的数据 DataFrame
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

    return data


def insert_data(table_name, data, index_name, target_date):
    """
    插入指定日期的数据到指定表
    :param table_name: 表名
    :param data: 数据 DataFrame
    :param index_name: 指数名称
    :param target_date: 指定日期
    """
    target_row = data[data['trade_date'] == target_date]
    if not target_row.empty:
        insert_sql = f"""
        INSERT INTO {table_name} (ts_code, name, trade_date, close, open, high, low, pre_close, price_change, pct_change, vol, turnover_rate, total_mv, float_mv, avg_price, ma_5, ma_10, ma_20, ma_60, boll_up, boll_mid, boll_low, kdj, macd)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        row = target_row.iloc[0]
        values = [
            row['ts_code'],
            index_name,
            row['trade_date'],
            float(row['close']) if pd.notna(row['close']) else None,
            float(row['open']) if pd.notna(row['open']) else None,
            float(row['high']) if pd.notna(row['high']) else None,
            float(row['low']) if pd.notna(row['low']) else None,
            float(row['pre_close']) if pd.notna(row['pre_close']) else None,
            float(row['change']) if pd.notna(row['change']) else None,
            float(row['pct_change']) if pd.notna(row['pct_change']) else None,
            float(row['vol']) if pd.notna(row['vol']) else None,
            float(row['turnover_rate']) if pd.notna(row['turnover_rate']) else 0,
            float(row.get('total_mv', 0)) if pd.notna(row.get('total_mv', 0)) else None,
            float(row.get('float_mv', 0)) if pd.notna(row.get('float_mv', 0)) else None,
            float(row['avg_price']) if pd.notna(row['avg_price']) else None,
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
            print(f"插入 {row['ts_code']} 在 {row['trade_date']} 的数据成功。")
        except pymysql.Error as e:
            print(f"插入 {row['ts_code']} 在 {row['trade_date']} 的数据时出错: {e}")
            conn.rollback()
    else:
        print(f"未找到 {target_date} 关于 {index_name}({ts_code}) 的数据。")


# 从 concept_sector 表获取概念指数信息
cursor.execute("SELECT ts_code, name FROM concept_sector")
concept_index_rows = cursor.fetchall()
concept_index_df = pd.DataFrame(concept_index_rows, columns=['ts_code', 'name'])

# 从 industry_sector 表获取行业指数信息
cursor.execute("SELECT ts_code, name FROM industry_sector")
industry_index_rows = cursor.fetchall()
industry_index_df = pd.DataFrame(industry_index_rows, columns=['ts_code', 'name'])

# 指定日期
target_date = '20250214'  # 你可以修改这个日期
# 计算近 120 天的开始日期
target_datetime = datetime.strptime(target_date, '%Y%m%d')
start_date = (target_datetime - timedelta(days=120)).strftime('%Y%m%d')

# 获取行业指数数据
for index, row in industry_index_df.iterrows():
    ts_code = row['ts_code']
    index_name = row['name']
    try:
        data = get_data(ts_code, start_date, target_date)
        if not data.empty:
            data = calculate_indicators(data)
            insert_data('industry_sector_daily', data, index_name, target_date)
        else:
            print(f"未获取到 {ts_code} 在 {start_date} 到 {target_date} 的行业指数数据。")
    except Exception as e:
        print(f"处理 {ts_code} 的行业指数数据时出错: {e}")

# 获取概念指数数据
for index, row in concept_index_df.iterrows():
    ts_code = row['ts_code']
    index_name = row['name']
    try:
        data = get_data(ts_code, start_date, target_date)
        if not data.empty:
            data = calculate_indicators(data)
            insert_data('concept_sector_daily', data, index_name, target_date)
        else:
            print(f"未获取到 {ts_code} 在 {start_date} 到 {target_date} 的概念指数数据。")
    except Exception as e:
        print(f"处理 {ts_code} 的概念指数数据时出错: {e}")

# 关闭数据库连接
cursor.close()
conn.close()