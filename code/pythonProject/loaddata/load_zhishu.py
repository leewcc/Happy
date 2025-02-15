import tushare as ts
import pymysql

# 设置 Tushare Pro 的 token
ts.set_token('a880b180343bdf47d774721036dabac9f9dd7ec3952c80fbe8ba515e')
pro = ts.pro_api()

# 定义要查询的指数代码列表
index_codes = [
    '000001.SH',  # 上证指数
    '399001.SZ',  # 深圳成指
    '399006.SZ',  # 创业板指
    '000688.SH',  # 科创50
    '000016.SH',  # 上证50
    '000300.SH',  # 沪深300
    '000905.SH',  # 中证500
    '000852.SH',  # 中证1000
    '000849.SH',  # 中证2000
    '899050.BJ'   # 北证50
]

# 连接到 MySQL 数据库
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='happy',
    charset='utf8mb4'
)
cursor = conn.cursor()

# 循环查询每个指数的信息
for code in index_codes:
    try:
        # 调用 index_basic 接口获取指数信息
        data = pro.index_basic(ts_code=code)
        if not data.empty:
            ts_code = data['ts_code'].values[0]
            name = data['name'].values[0]
            try:
                # 插入数据到指数表
                insert_sql = "INSERT IGNORE INTO index_info (ts_code, name) VALUES (%s, %s)"
                cursor.execute(insert_sql, (ts_code, name))
                conn.commit()
                print(f"成功插入指数代码 {ts_code} 的信息。")
            except pymysql.Error as e:
                print(f"插入指数代码 {ts_code} 的信息时出错: {e}")
                conn.rollback()
        else:
            print(f"未获取到指数代码 {code} 的信息。")
    except Exception as e:
        print(f"获取指数代码 {code} 的信息时出错: {e}")

# 关闭数据库连接
cursor.close()
conn.close()