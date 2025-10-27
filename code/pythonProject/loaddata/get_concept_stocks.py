from daily import tushare_data as ts
import pymysql
import time

# 设置 Tushare Pro 的 token
ts.set_token('1ab08efbf57546eab5a62499848c542a')
pro = ts.pro_api()

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'happy',
    'charset': 'utf8mb4'
}

# 记录每分钟的调用次数
call_count = 0
start_time = time.time()

def reset_call_count():
    global call_count, start_time
    call_count = 0
    start_time = time.time()

def throttle_call():
    global call_count, start_time
    current_time = time.time()
    elapsed_time = current_time - start_time
    if elapsed_time >= 90:
        reset_call_count()
    if call_count >= 49:
        wait_time = 90 - elapsed_time
        print(f"已达到每90秒 49 次调用限制，等待 {wait_time:.2f} 秒后继续...")
        time.sleep(wait_time)
        reset_call_count()
    call_count += 1

def get_concept_list():
    """
    获取所有概念板块列表
    :return: DataFrame，包含概念代码和名称
    """
    try:
        throttle_call()
        data = pro.ths_index(type='N')
        return data[['ts_code', 'name']]
    except Exception as e:
        print(f"获取概念板块列表时出错: {e}")
        return None

def get_concept_stocks(concept_code):
    """
    获取指定概念板块的成分股
    :param concept_code: 概念板块代码，如 'TS355'
    :return: list of dict，包含股票代码、名称等信息
    """
    try:
        throttle_call()
        df = pro.ths_member(ts_code=concept_code)
        if df.empty:
            return []
        
        stocks = []
        for _, row in df.iterrows():
            stock_info = {
                'stock_code': row['con_code'],
                'stock_name': row['con_name'],
                'weight': row.get('weight'),
                'in_date': row.get('in_date'),
                'out_date': row.get('out_date'),
                'is_new': row.get('is_new')
            }
            stocks.append(stock_info)
        return stocks
    except Exception as e:
        print(f"获取概念板块 {concept_code} 的成分股时出错: {e}")
        return []

def search_concept(keyword):
    """
    搜索概念板块
    :param keyword: 概念名称关键词
    :return: list of dict，包含匹配的概念板块信息
    """
    concepts = get_concept_list()
    if concepts is None:
        return []
    
    matched_concepts = concepts[concepts['name'].str.contains(keyword, na=False)]
    return matched_concepts.to_dict('records')

def save_concept_stocks_to_db(concept_code, concept_name):
    """
    将指定概念板块的成分股保存到数据库
    :param concept_code: 概念板块代码
    :param concept_name: 概念板块名称
    :return: 成功插入的记录数
    """
    stocks = get_concept_stocks(concept_code)
    if not stocks:
        print(f"未找到概念 {concept_name} 的成分股数据")
        return 0

    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        # 插入数据
        insert_count = 0
        for stock in stocks:
            insert_sql = """
            INSERT IGNORE INTO concept_stock 
            (sector_code, sector_name, stock_code, stokc_name, weight, in_date, out_date, is_new)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_sql, (
                concept_code,
                concept_name,
                stock['stock_code'],
                stock['stock_name'],
                stock['weight'],
                stock['in_date'],
                stock['out_date'],
                stock['is_new']
            ))
            insert_count += cursor.rowcount
        
        conn.commit()
        print(f"成功将 {insert_count} 条记录插入到数据库")
        return insert_count
    
    except Exception as e:
        print(f"保存数据到数据库时出错: {e}")
        if 'conn' in locals():
            conn.rollback()
        return 0
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # 示例用法
    # 1. 搜索包含特定关键词的概念
    keyword = "雅下水电概念"  # 可以修改为你想搜索的关键词
    print(f"\n搜索包含 '{keyword}' 的概念板块:")
    concepts = search_concept(keyword)
    for concept in concepts:
        print(f"概念名称: {concept['name']}, 代码: {concept['ts_code']}")
    
    # 2. 如果找到了想要的概念，获取该概念的成分股并保存到数据库
    if concepts:
        for concept in concepts:
            concept_code = concept['ts_code']
            concept_name = concept['name']
            print(f"\n正在处理概念 '{concept_name}':")
            save_concept_stocks_to_db(concept_code, concept_name) 