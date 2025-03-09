import pymysql
from datetime import datetime

def get_db_connection():
    """
    获取数据库连接
    """
    return pymysql.connect(
        host='localhost',
        user='root',
        password='root',
        database='happy',
        charset='utf8mb4'
    )

def get_all_trade_dates():
    """
    获取所有交易日期
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT DISTINCT trade_date 
            FROM limit_stocks 
            ORDER BY trade_date
        """)
        dates = [row[0] for row in cursor.fetchall()]
        return dates
    finally:
        cursor.close()
        conn.close()

def calculate_stats_for_date(trade_date, conn):
    """
    计算指定日期的统计数据
    """
    cursor = conn.cursor()
    
    try:
        # 统计涨跌停数据
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN limit_type = 'U' THEN 1 ELSE 0 END) as limit_up_count,
                SUM(CASE WHEN limit_type = 'D' THEN 1 ELSE 0 END) as limit_down_count,
                SUM(CASE WHEN limit_type = 'Z' THEN 1 ELSE 0 END) as broken_count,
                SUM(CASE WHEN limit_type = 'U' AND limit_times > 1 THEN 1 ELSE 0 END) as consecutive_count
            FROM limit_stocks
            WHERE trade_date = %s
        """, (trade_date,))
        
        limit_result = cursor.fetchone()
        
        # 统计上涨下跌家数
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN price_change_rate > 0 THEN 1 ELSE 0 END) as up_count,
                SUM(CASE WHEN price_change_rate < 0 THEN 1 ELSE 0 END) as down_count
            FROM daily_data
            WHERE trade_date = %s
        """, (trade_date,))
        
        updown_result = cursor.fetchone()
        
        stats = {
            'limit_up_count': int(limit_result[0]) if limit_result[0] else 0,
            'limit_down_count': int(limit_result[1]) if limit_result[1] else 0,
            'broken_count': int(limit_result[2]) if limit_result[2] else 0,
            'consecutive_count': int(limit_result[3]) if limit_result[3] else 0,
            'up_count': int(updown_result[0]) if updown_result[0] else 0,
            'down_count': int(updown_result[1]) if updown_result[1] else 0
        }
        
        return stats
        
    except Exception as e:
        print(f"计算{trade_date}的统计数据时出错: {str(e)}")
        return None

def insert_stats(trade_date, stats, conn):
    """
    插入统计数据
    """
    cursor = conn.cursor()
    
    try:
        # 删除已有数据
        cursor.execute("""
            DELETE FROM limit_stats 
            WHERE trade_date = %s
        """, (trade_date,))
        
        # 插入新数据
        insert_sql = """
            INSERT INTO limit_stats (trade_date, item, count)
            VALUES (%s, %s, %s)
        """
        
        for item, count in stats.items():
            cursor.execute(insert_sql, (trade_date, item, count))
        
        conn.commit()
        print(f"成功插入{trade_date}的统计数据：涨停{stats['limit_up_count']}家，"
              f"跌停{stats['limit_down_count']}家，"
              f"炸板{stats['broken_count']}家，"
              f"连板{stats['consecutive_count']}家，"
              f"上涨{stats['up_count']}家，"
              f"下跌{stats['down_count']}家")
        
    except Exception as e:
        print(f"插入{trade_date}的统计数据时出错: {str(e)}")
        conn.rollback()

def main():
    """
    主函数
    """
    try:
        # 获取所有交易日期
        trade_dates = get_all_trade_dates()
        if not trade_dates:
            print("未找到任何交易日期")
            return
        
        print(f"找到{len(trade_dates)}个交易日的数据")
        
        # 建立数据库连接
        conn = get_db_connection()
        
        # 处理每个交易日的数据
        for trade_date in trade_dates:
            print(f"\n处理{trade_date}的数据...")
            
            # 计算统计数据
            stats = calculate_stats_for_date(trade_date, conn)
            if stats:
                # 插入统计数据
                insert_stats(trade_date, stats, conn)
            else:
                print(f"跳过{trade_date}的数据处理")
        
        print("\n所有数据处理完成")
        
    except Exception as e:
        print(f"处理过程中出错: {str(e)}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 