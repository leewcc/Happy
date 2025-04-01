import pandas as pd
from sqlalchemy import create_engine
import datetime

def load_turnover_avg():
    # 数据库连接
    engine = create_engine('mysql+pymysql://leewcc:leewcc@localhost:3306/happy?charset=utf8mb4')
    
    # 获取2024-01-01之后的数据
    start_date = '2024-01-01'
    sql = f"""
    SELECT stock_code, trade_date, turnover_amount 
    FROM daily_data 
    WHERE trade_date >= '{start_date}'
    ORDER BY stock_code, trade_date
    """
    
    # 读取数据
    df = pd.read_sql(sql, engine)
    
    # 将trade_date转换为datetime类型
    df['trade_date'] = pd.to_datetime(df['trade_date'])
    
    # 按股票代码分组
    grouped = df.groupby('stock_code')
    
    # 存储结果的列表
    results = []
    
    # 对每个股票进行处理
    for stock_code, group in grouped:
        # 按日期排序
        group = group.sort_values('trade_date')
        
        # 计算不同天数的平均成交额
        group['avg_1d'] = group['turnover_amount']
        group['avg_2d'] = group['turnover_amount'].rolling(window=2).mean()
        group['avg_3d'] = group['turnover_amount'].rolling(window=3).mean()
        group['avg_4d'] = group['turnover_amount'].rolling(window=4).mean()
        group['avg_5d'] = group['turnover_amount'].rolling(window=5).mean()
        
        # 将NaN值替换为0
        group = group.fillna(0)
        
        # 添加到结果列表
        results.append(group[['stock_code', 'trade_date', 'avg_1d', 'avg_2d', 'avg_3d', 'avg_4d', 'avg_5d']])
    
    # 合并所有结果
    result_df = pd.concat(results)
    
    # 将结果写入数据库
        
    # 写入新数据
    result_df.to_sql('stock_turnover_avg', engine, if_exists='append', index=False)
    
    print(f"Successfully updated turnover amount averages from {start_date}")

if __name__ == "__main__":
    load_turnover_avg()