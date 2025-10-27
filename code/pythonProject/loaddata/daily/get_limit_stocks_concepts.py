# import chinadata.ca_data as ts
import tudata as ts
import pandas as pd
from datetime import datetime
import pymysql
import time

# 设置 Tushare Pro 的 token
ts.set_token('3463b38b6b244e9c8549e599f4430b92')
# ts.set_token('le2937d38d26f5322ae6096286072faf933')
pro = ts.pro_api()

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host='localhost',
        user='root',
        password='root',
        database='happy',
        charset='utf8mb4'
    )

def get_limit_stocks(trade_date):
    """获取指定日期的涨跌停和炸板股票"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
        SELECT 
            ts_code,
            name,
            limit_type
        FROM limit_stocks
        WHERE trade_date = %s
        ORDER BY limit_type, ts_code
        """
        
        cursor.execute(query, (trade_date,))
        stocks = cursor.fetchall()
        return stocks
        
    finally:
        cursor.close()
        conn.close()

def get_stock_concepts(stock_code):
    """获取股票的同花顺概念信息"""
    try:
        # 调用同花顺概念成分接口
        df = pro.ths_member(con_code=stock_code)
        print(stock_code)
        if df.empty:
            return []
        
        # 提取概念信息
        concepts = []
        for _, row in df.iterrows():
            concept = {
                'ts_code': row['ts_code'],  # 概念代码
                'name': row['con_name'],    # 股票名称
            }
            concepts.append(concept)
        
        # 休眠0.3秒，避免触发频率限制
        time.sleep(0.3)
        return concepts
        
    except Exception as e:
        print(f"获取{stock_code}概念信息时出错: {str(e)}")
        return []

def format_limit_type(limit_type):
    """格式化涨跌停类型"""
    type_marks = {
        'U': '🔴涨停',
        'D': '🟢跌停',
        'Z': '🟡炸板'
    }
    return type_marks.get(limit_type, '未知')

def get_concept_map():
    """获取所有概念的映射关系"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        query = """
        SELECT ts_code, name 
        FROM concept_sector
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # 创建映射字典
        concept_map = {row[0]: row[1] for row in results}
        return concept_map
        
    finally:
        cursor.close()
        conn.close()

def insert_stock_concept(stock_code, concept_code, concept_name, stock_name):
    """插入单个股票概念关系"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 插入数据
        insert_sql = """
        INSERT IGNORE INTO concept_stock 
        (sector_code, sector_name, stock_code, stokc_name, is_new) 
        VALUES (%s, %s, %s, %s, 'Y')
        """
        
        cursor.execute(insert_sql, (concept_code, concept_name, stock_code, stock_name))
        conn.commit()
            
    except Exception as e:
        print(f"插入概念数据时出错: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main(trade_date=None):
    """主函数"""
    if trade_date is None:
        trade_date = datetime.now().strftime('%Y%m%d')
    
    print(f"\n获取 {trade_date} 的涨跌停股票概念信息...\n")
    
    # 获取概念映射
    concept_map = get_concept_map()
    print(f"获取到 {len(concept_map)} 个概念")
    
    # 获取涨跌停股票列表
    stocks = get_limit_stocks(trade_date)
    if not stocks:
        print("未找到任何涨跌停股票")
        return
    
    # 遍历每只股票获取概念信息
    for ts_code, name, limit_type in stocks:
        print("="*80)
        print(f"{format_limit_type(limit_type)} {ts_code} {name}")
        
        # 获取概念信息
        concepts = get_stock_concepts(ts_code)
        if concepts:
            print("\n所属概念:")
            for concept in concepts:
                concept_name = concept_map.get(concept['ts_code'])
                if concept_name:  # 只有在找到映射时才插入和显示
                    insert_stock_concept(ts_code, concept['ts_code'], concept_name, name)
                    print(f"- {concept['ts_code']}: {concept_name}")
        else:
            print("\n未找到概念信息")
        
        print()
    
    print("="*80)
    print("\n数据获取完成")
    

if __name__ == "__main__":
    # 可以传入指定日期，格式为'YYYYMMDD'
    main('20250311') 
