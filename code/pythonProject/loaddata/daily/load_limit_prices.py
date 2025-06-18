import chinadata.ca_data as ts
import pandas as pd
import pymysql
from datetime import datetime, timedelta

# 设置tushare的token
ts.set_token('x0939bc945cb5da1e5785097a469bc6ed99')
pro = ts.pro_api()

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

def load_limit_prices(trade_date=None):
    """获取指定日期的涨跌停价格"""
    try:
        # 如果没有指定日期，使用当前日期
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
            
        print(f"正在获取 {trade_date} 的涨跌停价格数据...")
        
        # 获取涨跌停价格数据
        df_limit = pro.stk_limit(trade_date=trade_date)
        
        if df_limit is None or df_limit.empty:
            print("获取到的数据为空")
            return False
            
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 插入新数据
            insert_sql = """
                INSERT INTO stock_limit_prices 
                (trade_date, ts_code, up_limit, down_limit)
                VALUES (%s, %s, %s, %s)
            """
            
            count = 0
            for _, row in df_limit.iterrows():
                cursor.execute(insert_sql, (
                    trade_date,
                    row['ts_code'],
                    row['up_limit'],
                    row['down_limit']
                ))
                count += 1
                
                if count % 100 == 0:
                    print(f"已处理 {count} 条记录")
            
            conn.commit()
            print(f"成功保存 {count} 条涨跌停价格记录")
            return True
            
        except Exception as e:
            print(f"保存数据失败: {str(e)}")
            conn.rollback()
            return False
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        print(f"获取涨跌停价格失败: {str(e)}")
        return False

def load_limit_prices_by_date_range(start_date, end_date):
    """获取日期范围内的涨跌停价格"""
    start = datetime.strptime(start_date, '%Y%m%d')
    end = datetime.strptime(end_date, '%Y%m%d')
    
    current = start
    while current <= end:
        date_str = current.strftime('%Y%m%d')
        print(f"\n处理日期: {date_str}")
        load_limit_prices(date_str)
        current += timedelta(days=1)

if __name__ == "__main__":
    # 可以通过命令行参数传入日期，这里演示几种用法
    
    # 获取单个日期的数据
    load_limit_prices('20250508')
    
    # 获取日期范围的数据
    # load_limit_prices_by_date_range('20240401', '20240403') 