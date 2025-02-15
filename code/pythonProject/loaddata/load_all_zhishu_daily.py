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

# 计算近 5 年的日期范围
five_years_ago = (datetime.now() - timedelta(days=365 * 5)).strftime('%Y%m%d')
today = datetime.now().strftime('%Y%m%d')

# 从 index_info 表中获取所有指数代码
cursor.execute("SELECT ts_code FROM index_info")
index_codes = [row[0] for row in cursor.fetchall()]

for ts_code in index_codes:
    try:
        # 调用 index_daily 接口获取指数的日线数据
        df = pro.index_daily(ts_code=ts_code, start_date=five_years_ago, end_date=today)
        if not df.empty:
            # 按日期升序排序
            df = df.sort_values(by='trade_date')

            # 计算技术指标
            # 计算均线
            df['ma_5'] = SMAIndicator(df['close'], window=5).sma_indicator()
            df['ma_10'] = SMAIndicator(df['close'], window=10).sma_indicator()
            df['ma_20'] = SMAIndicator(df['close'], window=20).sma_indicator()
            df['ma_60'] = SMAIndicator(df['close'], window=60).sma_indicator()

            # 计算布林带
            bollinger = BollingerBands(df['close'])
            df['boll_up'] = bollinger.bollinger_hband()
            df['boll_mid'] = bollinger.bollinger_mavg()
            df['boll_low'] = bollinger.bollinger_lband()

            # 计算 KDJ
            kdj = StochasticOscillator(df['high'], df['low'], df['close'])
            df['kdj'] = kdj.stoch()

            # 计算 MACD
            macd = MACD(df['close'])
            df['macd'] = macd.macd()

            # 插入数据到 index_daily_data 表
            insert_sql = """
            INSERT IGNORE INTO index_daily_data (ts_code, trade_date, close, open, high, low, pre_close, price_change, pct_chg, vol, amount, ma_5, ma_10, ma_20, ma_60, boll_up, boll_mid, boll_low, kdj, macd)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for index, row in df.iterrows():
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
                except pymysql.Error as e:
                    print(f"插入 {ts_code} 在 {row['trade_date']} 的数据时出错: {e}")
                    conn.rollback()
            print(f"{ts_code} 的数据插入成功。")
        else:
            print(f"未获取到 {ts_code} 的日线数据。")
    except Exception as e:
        print(f"获取 {ts_code} 的日线数据时出错: {e}")

# 关闭数据库连接
cursor.close()
conn.close()