import tudata as ts
import pandas as pd
from datetime import datetime, timedelta
import pymysql
import time
from get_limit_stocks_concepts import main as process_concepts

# 设置 Tushare Pro 的 token
# ts.set_token('1ab08efbf57546eab5a62499848c542a')
ts.set_token('fd367c69db694ae9af1a6788fa335afd')
pro = ts.pro_api()

# 连接到 MySQL 数据库
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='happy',
    charset='utf8mb4',
    use_unicode=True
)
cursor = conn.cursor()

# 用于缓存股票代码和所属概念的字典
concept_cache = {}

def get_concepts(stock_code):
    """
    获取股票的概念信息
    """
    if stock_code in concept_cache:
        return concept_cache[stock_code]
    
    query = "SELECT sector_name FROM concept_stock WHERE stock_code = %s"
    cursor.execute(query, (stock_code,))
    results = cursor.fetchall()
    concepts = [row[0] for row in results]
    concept_str = ','.join(concepts) if concepts else '-'
    concept_cache[stock_code] = concept_str
    return concept_str

def get_industry(stock_code):
    """
    获取股票的行业信息
    """
    query = "SELECT industry FROM stock WHERE stock_code = %s"
    cursor.execute(query, (stock_code,))
    result = cursor.fetchone()
    return result[0] if result else '-'

def get_market_type(stock_code):
    """
    判断股票的市场类型
    """
    if stock_code.startswith('6'):
        return 'HS'  # 沪深主板（上交所）
    elif stock_code.startswith(('00', '002')):
        return 'HS'  # 沪深主板（深交所）
    elif stock_code.startswith('30'):
        return 'GEM'  # 创业板
    elif stock_code.startswith('68'):
        return 'STAR'  # 科创板
    return 'Unknown'

def format_time(time_str):
    """
    格式化时间字符串
    """
    if pd.isna(time_str) or not time_str:
        return None
    try:
        if len(time_str) == 5:
            return f"0{time_str[:1]}:{time_str[1:3]}:{time_str[3:]}"
        elif len(time_str) == 6:
            return f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
    except:
        return None
    return None

def get_limit_data(trade_date):
    """
    获取涨跌停数据并合并涨停原因
    """
    try:
        print(f"\n获取{trade_date}的涨跌停数据...")
        
        # 获取基本涨跌停数据
        df_limit = pro.limit_list_d(trade_date=trade_date)
        if df_limit.empty:
            print("未获取到涨跌停数据")
            return pd.DataFrame()
        
        # 获取涨停原因数据
        print("获取涨停原因数据...")
        df_reason_up = pro.limit_list_ths(trade_date=trade_date, limit_type='涨停池')
        df_reason_break = pro.limit_list_ths(trade_date=trade_date, limit_type='炸板池')
        
        # 创建涨停原因映射
        reason_map = {}
        
        # 处理涨停池的原因
        if not df_reason_up.empty:
            for _, row in df_reason_up.iterrows():
                reason_map[row['ts_code']] = row.get('lu_desc', '')
        
        # 处理炸板池的原因
        if not df_reason_break.empty:
            for _, row in df_reason_break.iterrows():
                reason_map[row['ts_code']] = row.get('lu_desc', '')
        
        # 添加涨停原因到主数据框
        df_limit['reason'] = df_limit['ts_code'].map(lambda x: reason_map.get(x, ''))
        
        return df_limit
    
    except Exception as e:
        print(f"获取数据失败: {str(e)}")
        return pd.DataFrame()

def get_limit_price(stock_code, trade_date):
    """
    获取股票指定日期的跌停价格
    """
    query = """
    SELECT down_limit 
    FROM stock_limit_prices 
    WHERE ts_code = %s AND trade_date = %s
    """
    cursor.execute(query, (stock_code, trade_date))
    result = cursor.fetchone()
    return float(result[0]) if result else None

def insert_limit_stocks(data, trade_date):
    """
    将涨跌停数据插入数据库
    """
    insert_sql = """
    INSERT IGNORE INTO limit_stocks (
        trade_date, ts_code, industry, concept, market_type, name, 
        close, pct_chg, amount, limit_amount, float_mv, total_mv, 
        turnover_ratio, fd_amount, first_time, last_time, 
        open_times, up_stat, limit_times, limit_type, reason
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
        %s, %s, %s, %s, %s, %s, %s, %s, %s
    )
    """
    
    for _, row in data.iterrows():
        try:
            # 获取股票的行业和概念信息
            industry = get_industry(row['ts_code'])
            concepts = get_concepts(row['ts_code'])
            market_type = get_market_type(row['ts_code'])
            
            # 格式化时间
            first_time = format_time(row.get('first_time'))
            last_time = format_time(row.get('last_time'))
            
            # 准备基础数据
            base_values = [
                trade_date,
                row['ts_code'],
                industry,
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
                first_time,
                last_time,
                int(row['open_times']) if pd.notna(row['open_times']) else None,
                row['up_stat'] if pd.notna(row['up_stat']) else None,
                int(row['limit_times']) if pd.notna(row['limit_times']) else None
            ]
            
            # 插入原始记录
            values = base_values + [row['limit'] if pd.notna(row['limit']) else None, row.get('reason', '')]
            cursor.execute(insert_sql, values)
            conn.commit()
            print(f"成功插入 {row['ts_code']} 的数据")
            # 检查是否是炸板且收盘价为跌停的情况
            if row['limit'] == 'Z':  # 是炸板
                down_limit = get_limit_price(row['ts_code'], trade_date)
                if (down_limit is not None and 
                    pd.notna(row['close']) and
                    abs(float(row['close']) - down_limit) < 0.01):  # 考虑价格误差范围
                    
                    # 插入额外的跌停记录
                    values = base_values + ['D', row.get('reason', '')]
                    cursor.execute(insert_sql, values)
                    print(f"为炸板跌停股票 {row['ts_code']} 添加跌停记录")
                    conn.commit()
        except Exception as e:
            print(f"插入 {row['ts_code']} 的数据时出错: {str(e)}")
            conn.rollback()

def calculate_limit_stats(data, trade_date):
    """
    计算涨跌停统计数据并插入数据库
    """
    try:
        # 初始化统计数据
        stats = {
            'limit_up_count': 0,    # 涨停数
            'limit_down_count': 0,  # 跌停数
            'broken_count': 0,      # 炸板数
            'consecutive_count': 0   # 连板数
        }
        
        # 统计各项数据
        for _, row in data.iterrows():
            limit_type = row['limit']
            if limit_type == 'U':  # 涨停
                stats['limit_up_count'] += 1
                # 连板数统计（limit_times > 1 的为连板）
                if pd.notna(row['limit_times']) and row['limit_times'] > 1:
                    stats['consecutive_count'] += 1
            elif limit_type == 'D':  # 跌停
                stats['limit_down_count'] += 1
            elif limit_type == 'Z':  # 炸板
                stats['broken_count'] += 1
        
        # 插入统计数据
        insert_sql = """
        INSERT IGNORE INTO limit_stats (trade_date, item, count)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE count = VALUES(count)
        """
        
        # 批量插入所有统计项
        for item, count in stats.items():
            cursor.execute(insert_sql, (trade_date, item, count))
        
        conn.commit()
        print(f"成功插入统计数据：涨停{stats['limit_up_count']}家，"
              f"跌停{stats['limit_down_count']}家，"
              f"炸板{stats['broken_count']}家，"
              f"连板{stats['consecutive_count']}家")
        
    except Exception as e:
        print(f"插入统计数据时出错: {str(e)}")
        conn.rollback()

def main(trade_date=None):
    """
    主函数
    """
    try:
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
            
        print(f"开始处理 {trade_date} 的涨跌停数据...")
        
        # 获取并插入新数据
        limit_data = get_limit_data(trade_date)
        if not limit_data.empty:
            # 插入涨跌停明细数据
            insert_limit_stocks(limit_data, trade_date)
            print(f"成功处理 {len(limit_data)} 条涨跌停数据")
            
            # 计算并插入统计数据
            calculate_limit_stats(limit_data, trade_date)
            
        else:
            print("没有获取到涨跌停数据")
            
    except Exception as e:
        print(f"处理数据时出错: {str(e)}")
    finally:
        cursor.close()
        conn.close()
        
    # 处理概念数据
    print("\n=== 开始处理概念数据 ===")
    process_concepts(trade_date)

if __name__ == "__main__":
    main('20251215')
    