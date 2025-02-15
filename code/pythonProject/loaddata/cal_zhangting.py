import pymysql
import pandas as pd
from decimal import Decimal

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'happy',
    'charset': 'utf8mb4'
}


def calculate_limit_info(data):
    """
    计算是否涨停和是否炸板
    :param data: 包含单条或多条日线数据的 DataFrame
    :return: 包含计算结果的 DataFrame
    """
    # 计算涨停比例
    def get_limit_ratio(name):
        return Decimal('0.1') if 'ST' not in str(name) else Decimal('0.05')

    data['limit_ratio'] = data['stock_name'].apply(get_limit_ratio)

    # 计算涨停价格
    data['limit_up_price'] = data['previous_close_price'].apply(lambda x: Decimal(str(x))) * (Decimal('1') + data['limit_ratio'])

    # 判断是否涨停
    data['is_limit_up'] = data['close_price'].apply(lambda x: Decimal(str(x))) >= data['limit_up_price']

    # 判断是否炸板
    data['is_board_broken'] = (data['high_price'].apply(lambda x: Decimal(str(x))) > data['limit_up_price']) & (
            data['close_price'].apply(lambda x: Decimal(str(x))) < data['limit_up_price'])

    # 删除临时列
    data.drop(['limit_ratio', 'limit_up_price'], axis=1, inplace=True)

    return data


def update_database(data):
    """
    将计算结果更新回数据库
    :param data: 包含计算结果的 DataFrame
    """
    try:
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        update_sql = """
        UPDATE daily_data
        SET is_limit_up = %s,
            is_board_broken = %s
        WHERE stock_code = %s AND trade_date = %s
        """

        values = []
        for index, row in data.iterrows():
            values.append((
                int(row['is_limit_up']),
                int(row['is_board_broken']),
                row['stock_code'],
                row['trade_date']
            ))

        cursor.executemany(update_sql, values)
        conn.commit()
        print(f"成功更新 {len(values)} 条记录")

    except pymysql.Error as e:
        print(f"更新数据时出错: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


def main():
    try:
        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        # 查询所有数据
        select_sql = "SELECT stock_code, stock_name, previous_close_price, close_price, high_price, trade_date FROM daily_data"
        cursor.execute(select_sql)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        df = pd.DataFrame(rows, columns=columns)

        if not df.empty:
            # 计算是否涨停和是否炸板
            df = calculate_limit_info(df)
            # 更新数据库
            update_database(df)

    except pymysql.Error as e:
        print(f"查询数据时出错: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    main()