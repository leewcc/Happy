import pandas as pd
from datetime import datetime, timedelta
import pymysql
import time
from tqdm import tqdm
import logging
from pytdx.hq import TdxHq_API
from pytdx.params import TDXParams

# 配置日志输出到控制台
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'leewcc',
    'password': 'leewcc',
    'database': 'happy',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def get_market_code(ts_code):
    """获取市场代码和股票代码"""
    code = ts_code[:6]
    if ts_code.endswith('SZ'):
        market = TDXParams.MARKET_SZ
    else:
        market = TDXParams.MARKET_SH
    return market, code

def load_min_data(api, ts_code, start_date, end_date, freq=1):
    """
    获取股票分钟数据
    
    参数：
        api: TDX API实例
        ts_code (str): 股票代码，如 '000001.SZ'
        start_date (str): 开始日期，格式：'2023-08-25 09:00:00'
        end_date (str): 结束日期，格式：'2023-08-25 15:00:00'
        freq (int): 频率，默认1分钟
    """
    try:
        logging.info(f"开始获取 {ts_code} 的分钟数据，时间范围：{start_date} 至 {end_date}")
        
        market, code = get_market_code(ts_code)
        date_str = start_date.replace('-', '')  # 转换日期格式为 YYYYMMDD
        
        # 调用pytdx接口获取分钟数据
        df = api.get_history_minute_time_data(1, '600001', 20250417)
        
        if df is None or len(df) == 0:
            logging.warning(f"未获取到 {ts_code} 的数据")
            return 0
            
        # 转换为DataFrame并处理数据
        df = pd.DataFrame(df)
        df['ts_code'] = ts_code
        df['trade_time'] = pd.to_datetime(start_date).strftime('%Y-%m-%d ') + \
                          df['datetime'].apply(lambda x: f"{x//60:02d}:{x%60:02d}:00")
        
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 准备插入语句
        insert_sql = """
            INSERT INTO min1 (
                ts_code, trade_time, open, close, high, low, vol, amount
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s
            ) ON DUPLICATE KEY UPDATE
                open = VALUES(open),
                close = VALUES(close),
                high = VALUES(high),
                low = VALUES(low),
                vol = VALUES(vol),
                amount = VALUES(amount)
        """
        
        # 批量插入数据
        records = []
        for _, row in df.iterrows():
            record = (
                row['ts_code'],
                row['trade_time'],
                row['open'],
                row['close'],
                row['high'],
                row['low'],
                row['vol'],
                row['amount']
            )
            records.append(record)
        
        cursor.executemany(insert_sql, records)
        conn.commit()
        
        rows_affected = len(records)
        logging.info(f"成功插入/更新 {rows_affected} 条记录")
        
        return rows_affected
        
    except Exception as e:
        logging.error(f"处理 {ts_code} 数据时出错: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return 0
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def load_stock_min_data(start_date, end_date, freq=1):
    """
    批量获取股票分钟数据
    """
    api = TdxHq_API()
    try:
        # 连接通达信服务器
        api.connect('119.147.212.81', 7709)
        
        stocks = ['300005.SZ']
        total_count = 0
        
        print(f"开始处理股票列表: {stocks}")
        for stock in stocks:
            # 每次调用接口后等待一段时间
            time.sleep(0.1)
            
            count = load_min_data(api, stock, start_date, end_date, freq)
            total_count += count
            print(f"股票 {stock} 处理完成，获取到 {count} 条记录")
            
        logging.info(f"任务完成，共处理 {total_count} 条记录")
        
    except Exception as e:
        logging.error(f"批量处理数据时出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        api.disconnect()

if __name__ == '__main__':
    # 设置时间范围
    start_date = '2025-04-18'
    end_date = '2025-04-18'
    
    # 执行数据加载
    load_stock_min_data(start_date, end_date)
