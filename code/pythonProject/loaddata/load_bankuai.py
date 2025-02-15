import tushare as ts
import pymysql

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


def get_industry_sectors():
    """
    获取所有行业板块数据
    """
    try:
        data = pro.ths_index(type='I')
        return data[['ts_code', 'name']]
    except Exception as e:
        print(f"获取行业板块数据时出错: {e}")
        return None


def get_concept_sectors():
    """
    获取所有概念板块数据
    """
    try:
        data = pro.ths_index(type='N')
        return data[['ts_code', 'name']]
    except Exception as e:
        print(f"获取概念板块数据时出错: {e}")
        return None


def insert_into_database(sectors, table_name):
    try:
        # 连接到数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        for index, row in sectors.iterrows():
            print(row)
            ts_code = row['ts_code']
            name = row['name']

            # 使用 INSERT IGNORE INTO 忽略主键冲突
            sql = f"INSERT IGNORE INTO {table_name} (ts_code, name) VALUES (%s, %s)"
            cursor.execute(sql, (ts_code, name))

        # 提交事务
        conn.commit()
        print(f"{table_name} 数据插入成功")
    except Exception as e:
        print(f"插入数据到 {table_name} 表时出错: {e}")
        conn.rollback()
    finally:
        # 关闭数据库连接
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # 获取行业板块数据
    industry_sectors = get_industry_sectors()
    if industry_sectors is not None:
        insert_into_database(industry_sectors, 'industry_sector')

    # 获取概念板块数据
    concept_sectors = get_concept_sectors()
    if concept_sectors is not None:
        insert_into_database(concept_sectors, 'concept_sector')