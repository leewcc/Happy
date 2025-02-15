import tushare as ts
import pymysql

# 设置Tushare Pro的token
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

def get_stock_data():
    try:
        # 获取所有股票的基本信息
        data = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,market,exchange,is_hs')
        return data
    except Exception as e:
        print(f"获取股票数据时出错: {e}")
        return None

def insert_into_database(data):
    try:
        # 连接到数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        for index, row in data.iterrows():
            stock_code = row['symbol']
            stock_name = row['name']
            area = row['area']
            industry = row['industry']
            exchange_code = row['exchange']
            # 判断是否为ST股票
            is_st = True if 'ST' in stock_name else False

            # 插入数据到数据库
            sql = "INSERT INTO stock (stock_code, stock_name, area, industry, exchange_code, is_st) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (stock_code, stock_name, area, industry, exchange_code, is_st))

        # 提交事务
        conn.commit()
        print("数据插入成功")
    except Exception as e:
        print(f"插入数据到数据库时出错: {e}")
        conn.rollback()
    finally:
        # 关闭数据库连接
        cursor.close()
        conn.close()

if __name__ == "__main__":
    stock_data = get_stock_data()
    if stock_data is not None:
        insert_into_database(stock_data)