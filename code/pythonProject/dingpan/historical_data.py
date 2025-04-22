import pymysql
from datetime import datetime
from get_realtime_quotes import QuotesManager
from app import get_quotes_manager  # 导入获取 quotes_manager 的函数

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'leewcc',
    'password': 'leewcc',
    'database': 'happy',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def get_historical_market_overview(date):
    """获取历史市场概览数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取指数数据
        indices_sql = """
            SELECT 
                ts_code,
                CASE ts_code
                    WHEN '000001.SH' THEN '上证指数'
                    WHEN '399001.SZ' THEN '深证成指'
                    WHEN '399006.SZ' THEN '创业板指'
                    WHEN '000688.SH' THEN '科创50'
                    WHEN '899050.BJ' THEN '北证50'
                END as name,
                close as price, 
                pre_close, 
                pct_chg as change_pct, 
                vol as volume, 
                amount
            FROM index_daily_data
            WHERE trade_date = %s
            AND ts_code IN ('000001.SH', '399001.SZ', '399006.SZ', '000688.SH', '899050.BJ')
        """
        cursor.execute(indices_sql, (date,))
        indices = cursor.fetchall()
        
        # 从 limit_stats 表获取市场统计数据
        stats_sql = """
            SELECT 
                SUM(CASE WHEN item = 'up_count' THEN count ELSE 0 END) as up_count,
                SUM(CASE WHEN item = 'down_count' THEN count ELSE 0 END) as down_count
            FROM limit_stats
            WHERE trade_date = %s
            AND item IN ('up_count', 'down_count')
        """
        cursor.execute(stats_sql, (date,))
        statistics = cursor.fetchone()
        
        # # 获取成交额趋势
        # trend_sql = """
        #     SELECT DATE_FORMAT(trade_date, '%Y-%m-%d') as trade_date, 
        #            SUM(turnover_amount) as total_amount
        #     FROM daily_data
        #     WHERE trade_date <= %s
        #     GROUP BY trade_date
        #     ORDER BY trade_date DESC
        #     LIMIT 30
        # """
        # cursor.execute(trend_sql, (date,))
        # amount_trend = cursor.fetchall()
        # print(f"成交额趋势数据: {len(amount_trend)} 条记录")
        # print(f"最近一天成交额: {amount_trend[0] if amount_trend else None}")
        
        # 获取涨跌分布数据
        stocks_sql = """
            SELECT 
                stock_code,
                price_change_rate as change_pct
            FROM daily_data
            WHERE trade_date = %s
        """
        cursor.execute(stocks_sql, (date,))
        stocks = cursor.fetchall()
        
        # 在 Python 中处理后缀拼接
        processed_stocks = []
        for stock in stocks:
            stock_code = stock['stock_code']
            suffix = ''
            if stock_code.startswith('60') or stock_code.startswith('68'):
                suffix = 'SH'
            elif stock_code.startswith(('00', '30')):
                suffix = 'SZ'
            elif stock_code.startswith(('83', '87')):
                suffix = 'BJ'
            
            processed_stocks.append({
                'ts_code': f"{stock_code}.{suffix}",
                'change_pct': float(stock['change_pct']) if stock['change_pct'] is not None else 0
            })
        
        result = {
            'indices': indices,
            'statistics': {
                **statistics,
                'stocks': processed_stocks
            },
            'amount_trend': []  # 暂时返回空列表
        }
        return result
        
    except Exception as e:
        print(f"获取历史市场概览数据失败: {str(e)}")
        print(f"错误类型: {type(e)}")
        import traceback
        traceback.print_exc()
        return {
            'indices': [],
            'statistics': {'up_count': 0, 'down_count': 0, 'total_amount': 0, 'stocks': []},
            'amount_trend': []
        }
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def get_historical_stock_list(date, sort_by=None, order=None):
    """获取历史股票列表数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        sql = """
            SELECT 
                d.stock_code as ts_code,
                d.stock_name as name,
                d.close_price as price,
                d.previous_close_price as pre_close,
                d.price_change_rate as change_pct,
                d.turnover_amount * 1000 as amount,  # 转换为元
                d.call_auction_increase * d.turnover_amount * 1000 as bid_amount,  # 转换为元
                d.turnover_amount * (1 - d.call_auction_increase) * 1000 as non_bid_amount  # 转换为元
            FROM daily_data d
            WHERE d.trade_date = %s
        """
        
        # 添加排序
        if sort_by:
            # 映射字段名
            field_mapping = {
                'price': 'close_price',
                'pre_close': 'previous_close_price',
                'change_pct': 'price_change_rate',
                'amount': 'turnover_amount'
            }
            sort_field = field_mapping.get(sort_by, sort_by)
            sql += f" ORDER BY {sort_field} {'ASC' if order == 'asc' else 'DESC'}"
            
        cursor.execute(sql, (date,))
        stocks = cursor.fetchall()
        
        # 使用全局的 quotes_manager
        quotes_manager = get_quotes_manager()
        stock_info_cache = quotes_manager.stock_info_cache
        
        # 添加行业和概念信息
        processed_stocks = []
        for stock in stocks:
            stock_code = stock['ts_code']
            # 添加后缀
            suffix = ''
            if stock_code.startswith('60') or stock_code.startswith('68'):
                suffix = 'SH'
            elif stock_code.startswith(('00', '30')):
                suffix = 'SZ'
            elif stock_code.startswith(('83', '87')):
                suffix = 'BJ'
            
            ts_code = f"{stock_code}.{suffix}"
            info = stock_info_cache.get(ts_code, {'industry': '-', 'concepts': '-'})
            
            processed_stocks.append({
                'ts_code': ts_code,  # 使用带后缀的代码
                'name': stock['name'],
                'price': float(stock['price']) if stock['price'] is not None else 0,
                'pre_close': float(stock['pre_close']) if stock['pre_close'] is not None else 0,
                'change_pct': float(stock['change_pct']) if stock['change_pct'] is not None else 0,
                'amount': float(stock['amount']) if stock['amount'] is not None else 0,
                'bid_amount': float(stock['bid_amount']) if stock['bid_amount'] is not None else 0,
                'non_bid_amount': float(stock['non_bid_amount']) if stock['non_bid_amount'] is not None else 0,
                'industry': info['industry'],
                'concepts': info['concepts']
            })
        
        return processed_stocks[:100]
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def get_historical_limit_analysis(date):
    """获取历史涨停分析数据"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # 获取涨跌停统计
        stats_sql = """
            SELECT item, count
            FROM limit_stats
            WHERE trade_date = %s
        """
        cursor.execute(stats_sql, (date,))
        stats_results = cursor.fetchall()
        print(stats_results)
        # 转换统计数据为所需格式
        statistics = {
            'limit_up_count': 0,
            'gem_limit_up_count': 0,
            'broken_limit_count': 0,
            'limit_down_count': 0,
            'continuous_count': 0
        }
        
        for stat in stats_results:
            if stat['item'] == 'limit_up_count':
                statistics['limit_up_count'] = stat['count']
            elif stat['item'] == 'gem_limit_up_count':
                statistics['gem_limit_up_count'] = stat['count']
            elif stat['item'] == 'broken_count':
                statistics['broken_limit_count'] = stat['count']
            elif stat['item'] == 'limit_down_count':
                statistics['limit_down_count'] = stat['count']
            elif stat['item'] == 'consecutive_count':
                statistics['continuous_count'] = stat['count']
        
        # 获取上一个交易日统计
        last_date_sql = """
            SELECT trade_date, item, count
            FROM limit_stats
            WHERE trade_date < %s
            ORDER BY trade_date DESC
            LIMIT 5
        """
        cursor.execute(last_date_sql, (date,))
        last_stats = cursor.fetchall()
        
        last_trade_date_stats = {
            'trade_date': last_stats[0]['trade_date'] if last_stats else None,
            'limit_up_count': 0,
            'gem_limit_up_count': 0,
            'broken_count': 0,
            'limit_down_count': 0,
            'continuous_count': 0
        }
        
        for stat in last_stats:
            if stat['item'] == 'limit_up_count':
                last_trade_date_stats['limit_up_count'] = stat['count']
            elif stat['item'] == 'gem_limit_up_count':
                last_trade_date_stats['gem_limit_up_count'] = stat['count']
            elif stat['item'] == 'broken_count':
                last_trade_date_stats['broken_count'] = stat['count']
            elif stat['item'] == 'limit_down_count':
                last_trade_date_stats['limit_down_count'] = stat['count']
            elif stat['item'] == 'consecutive_count':
                last_trade_date_stats['continuous_count'] = stat['count']
        
        # 直接从 limit_stocks 获取数据
        stocks_sql = """
            SELECT 
                ts_code,
                name,
                pct_chg as change_pct,
                limit_times as continuous_days,
                first_time as first_limit_time,
                amount,
                limit_type,
                open_times > 0 as is_broken
            FROM limit_stocks
            WHERE trade_date = %s
        """
        cursor.execute(stocks_sql, (date,))
        stocks = cursor.fetchall()
        
        # 使用全局的 quotes_manager 获取行业和概念信息
        quotes_manager = get_quotes_manager()
        stock_info_cache = quotes_manager.stock_info_cache
        
        # 处理股票列表数据
        stocks_list = []
        # 用于统计概念数据
        concept_data = {}
        
        for stock in stocks:
            ts_code = stock['ts_code']
            info = stock_info_cache.get(ts_code, {'industry': '-', 'concepts': '-'})
            
            stock_data = {
                'ts_code': ts_code,
                'name': stock['name'],
                'change_pct': float(stock['change_pct']) if stock['change_pct'] is not None else 0,
                'continuous_days': stock['continuous_days'] or 0,
                'first_limit_time': stock['first_limit_time'] or '-',
                'amount': float(stock['amount']) / 100000000 if stock['amount'] is not None else 0,  # 转换为亿元
                'industry': info['industry'],
                'concepts': info['concepts'],
                'type': 'limit_up' if stock['limit_type'] == 'U' else 'limit_down' if stock['limit_type'] == 'D' else 'broken',
                'is_broken': bool(stock['is_broken'])
            }
            stocks_list.append(stock_data)
            
            # 统计概念数据
            if info['concepts'] != '-':
                concepts = info['concepts'].split(',')
                for concept in concepts:
                    concept = concept.strip()
                    if not concept:
                        continue
                        
                    if concept not in concept_data:
                        concept_data[concept] = {
                            'concept': concept,
                            'limit_up_count': 0,
                            'continuous_count': 0,
                            'broken_count': 0,
                            'limit_down_count': 0,
                            'gem_limit_up_count': 0
                        }
                    
                    if stock['limit_type'] == 'U':
                        concept_data[concept]['limit_up_count'] += 1
                        if stock['continuous_days'] and stock['continuous_days'] > 1:
                            concept_data[concept]['continuous_count'] += 1
                    elif stock['limit_type'] == 'D':
                        concept_data[concept]['limit_down_count'] += 1
                    
                    if stock['is_broken']:
                        concept_data[concept]['broken_count'] += 1
        
        # 转换概念统计为列表并排序
        concept_stats = list(concept_data.values())
        concept_stats.sort(key=lambda x: x['limit_up_count'], reverse=True)
        
        return {
            'statistics': statistics,
            'last_trade_date_stats': last_trade_date_stats,
            'concept_stats': concept_stats,
            'limit_stocks': stocks_list
        }
        
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close() 