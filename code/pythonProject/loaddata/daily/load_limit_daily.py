import tushare as ts
import pymysql
import pandas as pd

# 设置 Tushare Pro 的 token
ts.set_token('a880b180343bdf47d774721036dabac9f9dd7ec3952c80fbe8ba515e')
pro = ts.pro_api()

# 连接到 MySQL 数据库
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='happy',
    charset='utf8mb4'
)
cursor = conn.cursor()


def get_limit_list_data(trade_date):
    """
    获取指定日期的涨跌停板数据
    :param trade_date: 指定的交易日期，格式为 'YYYYMMDD'
    :return: 涨跌停板数据 DataFrame
    """
    df = pro.limit_list_d(trade_date=trade_date)
    return df


def get_concepts(stock_code):
    """
    根据股票代码从 concept_stock 表中查询所属概念，并将概念名称合并成一个字符串
    :param stock_code: 股票代码
    :return: 所属概念字符串，以逗号相连
    """
    query = "SELECT sector_name FROM concept_stock WHERE stock_code = %s"
    cursor.execute(query, (stock_code,))
    results = cursor.fetchall()
    concepts = [row[0] for row in results]
    return ','.join(concepts)


def insert_into_limit_stocks(data, trade_date):
    """
    将涨跌停板数据插入到 limit_stocks 表中
    :param data: 涨跌停板数据 DataFrame
    :param trade_date: 指定的交易日期，格式为 'YYYYMMDD'
    """
    insert_sql = """
    INSERT INTO limit_stocks (trade_date, ts_code, industry, concept, market_type, name, close, pct_chg, amount, limit_amount, float_mv, total_mv, turnover_ratio, fd_amount, first_time, last_time, open_times, up_stat, limit_times, limit_type)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    for index, row in data.iterrows():
        stock_code = row['ts_code']
        concepts = get_concepts(stock_code)
        # 这里假设 market_type 根据交易所来判断，你可以根据实际情况修改
        if stock_code.startswith('6'):
            market_type = 'HS'  # 沪深主板（上交所）
        elif stock_code.startswith(('00', '002')):
            market_type = 'HS'  # 沪深主板（深交所）
        elif stock_code.startswith('30'):
            market_type = 'GEM'  # 创业板
        elif stock_code.startswith('68'):
            market_type = 'STAR'  # 科创板
        else:
            market_type = 'Unknown'

        values = [
            trade_date,
            row['ts_code'],
            row['industry'],
            concepts,
            market_type,
            row['name'],
            float(row['close']) if pd.notna(row['close']) else None,
            float(row['pct_chg']) if pd.notna(row['pct_chg']) else None,
            float(row['amount']) if pd.notna(row['amount']) else None,
            float(row['limit_amount']) if pd.notna(row['limit_amount']) else None,
            float(row['float_mv']) if pd.notna(row['float_mv']) else None,
            float(row['total_mv']) if pd.notna(row['total_mv']) else None,
            float(row['turnover_ratio']) if pd.notna(row['turnover_ratio']) else None,
            float(row['fd_amount']) if pd.notna(row['fd_amount']) else None,
            row['first_time'] if pd.notna(row['first_time']) else None,
            row['last_time'] if pd.notna(row['last_time']) else None,
            int(row['open_times']) if pd.notna(row['open_times']) else None,
            row['up_stat'] if pd.notna(row['up_stat']) else None,
            int(row['limit_times']) if pd.notna(row['limit_times']) else None,
            row['limit'] if pd.notna(row['limit']) else None
        ]
        try:
            cursor.execute(insert_sql, values)
            conn.commit()
            print(f"成功插入 {stock_code} 在 {trade_date} 的数据")
        except pymysql.Error as e:
            print(f"插入 {stock_code} 在 {trade_date} 的数据时出错: {e}")
            conn.rollback()


if __name__ == "__main__":
    # 指定要查询的日期，格式为 'YYYYMMDD'
    specified_date = '20250214'
    # 获取指定日期的涨跌停板数据
    limit_list_data = get_limit_list_data(specified_date)
    if not limit_list_data.empty:
        # 将数据插入到 limit_stocks 表中
        insert_into_limit_stocks(limit_list_data, specified_date)
    else:
        print(f"未获取到 {specified_date} 的涨跌停板数据")

    # 关闭数据库连接
    cursor.close()
    conn.close()