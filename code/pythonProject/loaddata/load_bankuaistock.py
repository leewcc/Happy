import tushare as ts
import pymysql
import time

# 设置 Tushare Pro 的 token
ts.set_token('a880b180343bdf47d774721036dabac9f9dd7ec3952c80fbe8ba515e')
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

def get_plate_codes(plate_type):
    """
    获取指定类型板块的代码列表
    :param plate_type: 板块类型，'I' 表示行业板块，'N' 表示概念板块
    :return: 板块代码列表
    """
    try:
        throttle_call()
        data = pro.ths_index(type=plate_type)
        return data['ts_code'].tolist()
    except Exception as e:
        print(f"获取 {plate_type} 板块代码时出错: {e}")
        return []

def get_and_insert_stocks(plate_type, table_name):
    """
    获取指定类型板块的成分股数据并插入到指定表中
    :param plate_type: 板块类型，'I' 表示行业板块，'N' 表示概念板块
    :param table_name: 要插入数据的表名
    """
    plate_codes = get_plate_codes(plate_type)
    try:
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        for ts_code in plate_codes:
            try:
                throttle_call()
                # 获取成分股数据
                df = pro.ths_member(ts_code=ts_code)
                if not df.empty:
                    for _, row in df.iterrows():
                        print(row)
                        sector_code = row['ts_code']
                        throttle_call()
                        sector_name = pro.ths_index(ts_code=sector_code)['name'].values[0]
                        stock_code = row['con_code']
                        stock_name = row['con_name']
                        weight = row.get('weight', None)
                        in_date = row.get('in_date', None)
                        out_date = row.get('out_date', None)
                        is_new = row.get('is_new', None)

                        insert_sql = f"""
                        INSERT IGNORE INTO {table_name} (sector_code, sector_name, stock_code, stokc_name, weight, in_date, out_date, is_new)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(insert_sql, (sector_code, sector_name, stock_code, stock_name, weight, in_date, out_date, is_new))
                    conn.commit()
                    print(f"成功插入 {sector_code} 板块的成分股数据到 {table_name} 表")
            except Exception as e:
                print(f"获取或插入 {ts_code} 板块成分股数据时出错: {e}")
    except Exception as e:
        print(f"数据库连接或操作出错: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    # 获取并插入行业板块成分股数据
    get_and_insert_stocks('I', 'industry_stock')
    # 获取并插入概念板块成分股数据
    get_and_insert_stocks('N', 'concept_stock')