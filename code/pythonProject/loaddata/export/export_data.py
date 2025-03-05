import mysql.connector
import pandas as pd
import os

# 数据库连接配置
config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'happy',
    'raise_on_warnings': True
}

# 解析建表语句获取字段名和中文名
def parse_create_table_sql(sql):
    lines = sql.split('\n')
    field_dict = {}
    for line in lines:
        if '`' in line and 'COMMENT' in line:
            parts = line.split('`')
            field_name = parts[1]
            comment_start = line.find('COMMENT \'')
            if comment_start != -1:
                comment_end = line.find('\'', comment_start + 9)
                comment = line[comment_start + 9:comment_end]
                field_dict[field_name] = comment
    return field_dict

try:
    connection = mysql.connector.connect(**config)
    cursor = connection.cursor()

    # 获取所有表名
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]

    # 确保保存路径存在
    save_path = r'C:\happy\Happy'
    if not os.path.exists(save_path):
        os.makedirs(save_path)

    for table in tables:
        # 获取表的建表语句
        cursor.execute(f"SHOW CREATE TABLE {table}")
        create_sql = cursor.fetchone()[1]
        field_dict = parse_create_table_sql(create_sql)

        # 分页查询数据
        page_size = 20000
        offset = 0
        all_data = []

        while True:
            cursor.execute(f"SELECT * FROM {table} LIMIT {page_size} OFFSET {offset}")
            rows = cursor.fetchall()
            if not rows:
                break
            all_data.extend(rows)
            offset += page_size

        columns = [col[0] for col in cursor.description]
        df = pd.DataFrame(all_data, columns=[field_dict.get(col, col) for col in columns])

        # 构建 Excel 文件路径
        file_path = os.path.join(save_path, f'{table}.xlsx')

        # 导出为 Excel 文件
        df.to_excel(file_path, index=False)
        print(f"成功导出表 {table} 到 {file_path}")

except mysql.connector.Error as err:
    print(f"数据库错误: {err}")
finally:
    if connection.is_connected():
        cursor.close()
        connection.close()
        print("数据库连接已关闭")