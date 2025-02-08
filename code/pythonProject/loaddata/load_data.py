import tushare as ts
import pandas as pd
from datetime import datetime, timedelta

# 设置 Tushare Pro 的 token，你需要替换成自己的有效 token
ts.set_token('611ed160db014d775da9f5c6c511dd4cc269e5429b5815e885208216')
pro = ts.pro_api()

def get_all_stock_data_last_2_years():
    # 计算 2 年前的日期
    two_years_ago = (datetime.now() - timedelta(days=365 * 2)).strftime('%Y%m%d')
    today = datetime.now().strftime('%Y%m%d')

    # 获取所有上市股票的基本信息，包含股票代码和名称
    stock_basic = pro.stock_basic(exchange='', list_status='L', fields='ts_code,name,industry')

    stock_codes = stock_basic['ts_code'].tolist()
    all_data = []
    batch_size = 100
    for i in range(0, len(stock_codes), batch_size):
        batch_codes = ','.join(stock_codes[i:i + batch_size])
        try:
            df = pro.daily(ts_code=batch_codes, start_date=two_years_ago, end_date=today)
            all_data.append(df)
        except Exception as e:
            print(f"获取批次 {batch_codes} 数据时出错: {e}")

    # 合并所有批次的数据
    daily_data = pd.concat(all_data, ignore_index=True)

    # 合并股票基本信息和每日交易数据
    merged_data = pd.merge(daily_data, stock_basic, on='ts_code', how='left')

    # 调整日期格式为 YYYY-MM-DD
    merged_data['trade_date'] = pd.to_datetime(merged_data['trade_date'], format='%Y%m%d').dt.strftime('%Y-%m-%d')

    # 选择需要的列
    columns = [
        'trade_date', 'ts_code', 'name', 'open', 'close', 'high', 'low', 'vol', 'amount',
        'turnover_rate', 'pct_chg', 'pre_close', 'industry'
    ]
    result = merged_data[columns]

    # 重命名列名
    result.rename(columns={
        'trade_date': '日期',
        'ts_code': '股票代码',
        'name': '股票名字',
        'vol': '成交量',
        'industry': '所属行业板块'
    }, inplace=True)

    return result

if __name__ == "__main__":
    data = get_all_stock_data_last_2_years()
    if not data.empty:
        try:
            # 将数据保存到指定的 txt 文件
            data.to_csv(r'D:\happy\1.txt', sep='\t', na_rep='nan')
            print("数据已成功保存到 D:\\happy\\1.txt")
        except Exception as e:
            print(f"保存数据时出错: {e}")
    else:
        print("未获取到有效数据。")