import mysql.connector
from datetime import datetime, timedelta
import numpy as np

# 数据库连接配置
config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'database': 'happy',
    'raise_on_warnings': True
}

def format_time(time_str):
    """格式化时间字符串
    支持两种格式：
    1. HH:MM:SS 格式 (如 "09:52:21")
    2. HHMMSS 格式 (如 "95221")
    """
    if not time_str:
        return None
        
    try:
        # 如果已经是 HH:MM:SS 格式，直接返回
        if isinstance(time_str, str) and ':' in time_str:
            # 验证格式是否正确
            try:
                hours, minutes, seconds = map(int, time_str.split(':'))
                if 0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 60:
                    return time_str
            except:
                pass

        # 转换为字符串并去除所有非数字字符
        time_str = ''.join(filter(str.isdigit, str(time_str)))
        
        if len(time_str) == 5:  # 95221 格式
            hours = int(time_str[0])
            minutes = int(time_str[1:3])
            seconds = int(time_str[3:])
        elif len(time_str) == 6:  # 095221 格式
            hours = int(time_str[:2])
            minutes = int(time_str[2:4])
            seconds = int(time_str[4:])
        else:
            return None

        if 0 <= hours < 24 and 0 <= minutes < 60 and 0 <= seconds < 60:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
    except (ValueError, TypeError, AttributeError):
        pass
        
    return None

def format_change_rate(stock_code, rate):
    """格式化涨跌幅显示"""
    # 如果是字符串，先转换为数字
    if isinstance(rate, str):
        try:
            rate = float(rate.strip('%').strip('+'))
        except ValueError:
            return rate

    # 创业板（300开头）和科创板（688开头）涨跌幅为20%
    if stock_code.startswith(('300', '688')):
        if rate >= 19.8:
            return "<span class='positive bold'>涨停</span>"
        elif rate <= -19.8:
            return "<span class='negative bold'>核按钮</span>"
    # 主板涨跌幅为10%
    else:
        if rate >= 9.8:
            return "<span class='positive bold'>涨停</span>"
        elif rate <= -9.8:
            return "<span class='negative bold'>核按钮</span>"
    
    # 返回带有样式标记的涨跌幅
    if rate >= 8:
        return f"<span class='positive bold'>{rate:.2f}%</span>"
    elif rate <= -8:
        return f"<span class='negative bold'>{rate:.2f}%</span>"
    return f"{rate:.2f}%"

def get_market_analysis(target_date=None, previous_date=None, pre_previous_date=None):
    """获取市场分析数据"""
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # 如果没有提供日期，使用默认值
        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')
        if not previous_date:
            previous_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        if not pre_previous_date:
            pre_previous_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
        
        target_date_formatted = datetime.strptime(target_date, '%Y-%m-%d').strftime('%Y%m%d')
        previous_date_formatted = datetime.strptime(previous_date, '%Y-%m-%d').strftime('%Y%m%d')
        pre_previous_date_formatted = datetime.strptime(pre_previous_date, '%Y-%m-%d').strftime('%Y%m%d')

        # 初始化 market_data 字典
        market_data = {
            'market_overview': {},
            'index_changes': [],
            'limit_up_stats': {},
            'yesterday_stats': {},
            'concept_stats': [],
            'consecutive_limit_stocks': {},
            'all_limit_stocks': [],
            'pre_consecutive_stocks': [],
            'yesterday_consecutive_stocks': [],
            'updown_trend': {},
            'limit_trend': {}
        }

        # 定义指数代码和名称的映射
        index_mapping = {
            '000001.SH': '上证指数',
            '399001.SZ': '深证成指',
            '399006.SZ': '创业板指',
            '000016.SH': '上证50',
            '000300.SH': '沪深300',
            '000905.SH': '中证500',
            '000852.SH': '中证1000',
            '000688.SH': '科创50',
            '899050.BJ': '北证50'
        }

        # 修改指数日线数据表查询
        index_query = """
        SELECT ts_code, pct_chg, close, pre_close
        FROM index_daily_data
        WHERE trade_date = %s AND ts_code IN ({})
        """.format(','.join(['%s'] * len(index_mapping)))
        
        # 构建查询参数
        query_params = [target_date_formatted] + list(index_mapping.keys())
        cursor.execute(index_query, query_params)
        index_results = cursor.fetchall()

        # 处理指数数据
        for result in index_results:
            index_code = result[0]
            index_name = index_mapping.get(index_code, index_code)
            change_percentage = result[1]
            close_price = result[2]
            pre_close = result[3]
            
            market_data['index_changes'].append({
                'name': index_name,
                'code': index_code,
                'change': f"{change_percentage:.2f}%",
                'is_positive': change_percentage > 0,
                'close': f"{close_price:.2f}",
                'pre_close': f"{pre_close:.2f}"
            })

        # 修改指数优先级排序
        index_priority = [
            '上证指数', 
            '深证成指', 
            '创业板指',
            '上证50',
            '沪深300',
            '中证500',
            '中证1000',
            '科创50',
            '北证50'
        ]

        # 按照优先级排序
        market_data['index_changes'].sort(key=lambda x: (
            index_priority.index(x['name']) if x['name'] in index_priority else len(index_priority)
        ))

        # 股票日线表统计当天的上涨股票数，下跌股票数
        stock_query = """
        SELECT 
            SUM(CASE WHEN close_price > previous_close_price THEN 1 ELSE 0 END) AS up_count,
            SUM(CASE WHEN close_price < previous_close_price THEN 1 ELSE 0 END) AS down_count
        FROM daily_data
        WHERE trade_date = %s
        """
        cursor.execute(stock_query, (target_date,))
        up_count, down_count = cursor.fetchone()
        
        # 确保数据不为 None
        market_data['market_overview'] = {
            'up_count': int(up_count) if up_count is not None else 0,
            'down_count': int(down_count) if down_count is not None else 0
        }

        # 统计当天不同涨幅范围的股票个数
        range_query = """
        SELECT 
            SUM(CASE WHEN (close_price - previous_close_price) / previous_close_price * 100 <= -7 THEN 1 ELSE 0 END) AS range_1,
            SUM(CASE WHEN (close_price - previous_close_price) / previous_close_price * 100 > -7 AND (close_price - previous_close_price) / previous_close_price * 100 <= -3 THEN 1 ELSE 0 END) AS range_2,
            SUM(CASE WHEN (close_price - previous_close_price) / previous_close_price * 100 > -3 AND (close_price - previous_close_price) / previous_close_price * 100 < 0 THEN 1 ELSE 0 END) AS range_3,
            SUM(CASE WHEN (close_price - previous_close_price) / previous_close_price * 100 >= 0 AND (close_price - previous_close_price) / previous_close_price * 100 <= 3 THEN 1 ELSE 0 END) AS range_4,
            SUM(CASE WHEN (close_price - previous_close_price) / previous_close_price * 100 > 3 AND (close_price - previous_close_price) / previous_close_price * 100 <= 7 THEN 1 ELSE 0 END) AS range_5,
            SUM(CASE WHEN (close_price - previous_close_price) / previous_close_price * 100 > 7 THEN 1 ELSE 0 END) AS range_6
        FROM daily_data
        WHERE trade_date = %s
        """
        cursor.execute(range_query, (target_date_formatted,))
        range_counts = cursor.fetchone()

        ranges = [
            "<-7",
            "-7~-3",
            "-3~0",
            "0~3",
            "3~7",
            ">7"
        ]

        market_data['range_distribution'] = {
            'ranges': ranges,
            'counts': [int(count) if count else 0 for count in range_counts]  # 确保数据是数字
        }

        # 涨跌停股票表上获取当天涨停数，昨日涨停数
        limit_count_query = """
        SELECT 
            SUM(CASE WHEN trade_date = %s AND limit_type = 'U' AND market_type IN ('STAR', 'HS', 'GEM') THEN 1 ELSE 0 END) AS today_limit_count,
            SUM(CASE WHEN trade_date = %s AND limit_type = 'U' AND market_type IN ('STAR', 'HS', 'GEM') THEN 1 ELSE 0 END) AS yesterday_limit_count
        FROM limit_stocks
        """
        cursor.execute(limit_count_query, (target_date_formatted, previous_date_formatted))
        today_limit_count, yesterday_limit_count = cursor.fetchone()
        market_data['limit_up_stats'] = {
            'today_limit_count': today_limit_count,
            'yesterday_limit_count': yesterday_limit_count
        }

        # 统计今日和昨日首次涨停数量
        first_limit_count_query = """
        SELECT 
            SUM(CASE WHEN trade_date = %s AND limit_type = 'U' AND limit_times = 1 AND market_type IN ('STAR', 'HS', 'GEM') THEN 1 ELSE 0 END) AS today_first_limit_count,
            SUM(CASE WHEN trade_date = %s AND limit_type = 'U' AND limit_times = 1 AND market_type IN ('STAR', 'HS', 'GEM') THEN 1 ELSE 0 END) AS yesterday_first_limit_count
        FROM limit_stocks
        """
        cursor.execute(first_limit_count_query, (target_date_formatted, previous_date_formatted))
        today_first_limit_count, yesterday_first_limit_count = cursor.fetchone()
        market_data['limit_up_stats']['today_first_limit_count'] = today_first_limit_count
        market_data['limit_up_stats']['yesterday_first_limit_count'] = yesterday_first_limit_count

        # 计算各类股票的平均涨幅
        # 涨停股平均涨幅
        limit_up_avg_query = """
        SELECT AVG((dd.close_price - dd.previous_close_price) / dd.previous_close_price * 100)
        FROM daily_data dd
        JOIN limit_stocks ls ON dd.stock_code = LEFT(ls.ts_code, 6)
        WHERE dd.trade_date = %s AND ls.trade_date = %s AND ls.limit_type = 'U'
        """
        cursor.execute(limit_up_avg_query, (target_date, target_date_formatted))
        limit_up_avg = cursor.fetchone()[0]
        market_data['limit_up_stats']['limit_up_avg_gain'] = format_change_rate('000000', limit_up_avg or 0)

        # 创业板和科创板的涨停数、和昨日的涨停数
        gem_star_limit_query = """
        SELECT 
            SUM(CASE WHEN trade_date = %s AND limit_type = 'U' AND market_type IN ('GEM', 'STAR') THEN 1 ELSE 0 END) AS today_gem_star_limit_up_count,
            SUM(CASE WHEN trade_date = %s AND limit_type = 'U' AND market_type IN ('GEM', 'STAR') THEN 1 ELSE 0 END) AS yesterday_gem_star_limit_up_count
        FROM limit_stocks
        """
        cursor.execute(gem_star_limit_query, (target_date_formatted, previous_date_formatted))
        today_gem_star_limit_up_count, yesterday_gem_star_limit_up_count = cursor.fetchone()
        market_data['limit_up_stats']['today_gem_star_limit_up_count'] = today_gem_star_limit_up_count
        market_data['limit_up_stats']['yesterday_gem_star_limit_up_count'] = yesterday_gem_star_limit_up_count

        # 今日炸板率和昨日炸板率
        board_broken_query = """
        SELECT 
            IFNULL(SUM(CASE WHEN trade_date = %s AND limit_type = 'Z' AND market_type IN ('STAR', 'HS', 'GEM') THEN 1 ELSE 0 END) / 
                   NULLIF(SUM(CASE WHEN trade_date = %s AND (limit_type = 'U' OR limit_type = 'Z') AND market_type IN ('STAR', 'HS', 'GEM') THEN 1 ELSE 0 END), 0), 0) AS today_board_broken_rate,
            IFNULL(SUM(CASE WHEN trade_date = %s AND limit_type = 'Z' AND market_type IN ('STAR', 'HS', 'GEM') THEN 1 ELSE 0 END) / 
                   NULLIF(SUM(CASE WHEN trade_date = %s AND (limit_type = 'U' OR limit_type = 'Z') AND market_type IN ('STAR', 'HS', 'GEM') THEN 1 ELSE 0 END), 0), 0) AS yesterday_board_broken_rate
        FROM limit_stocks
        """
        cursor.execute(board_broken_query, (target_date_formatted, target_date_formatted, previous_date_formatted, previous_date_formatted))
        today_board_broken_rate, yesterday_board_broken_rate = cursor.fetchone()
        market_data['limit_up_stats']['today_board_broken_rate'] = today_board_broken_rate
        market_data['limit_up_stats']['yesterday_board_broken_rate'] = yesterday_board_broken_rate

        # 今日跌停数和昨日跌停数
        limit_down_query = """
        SELECT 
            SUM(CASE WHEN trade_date = %s AND limit_type = 'D' AND market_type IN ('STAR', 'HS', 'GEM') THEN 1 ELSE 0 END) AS today_limit_down_count,
            SUM(CASE WHEN trade_date = %s AND limit_type = 'D' AND market_type IN ('STAR', 'HS', 'GEM') THEN 1 ELSE 0 END) AS yesterday_limit_down_count
        FROM limit_stocks
        """
        cursor.execute(limit_down_query, (target_date_formatted, previous_date_formatted))
        today_limit_down_count, yesterday_limit_down_count = cursor.fetchone()
        market_data['limit_up_stats']['today_limit_down_count'] = today_limit_down_count
        market_data['limit_up_stats']['yesterday_limit_down_count'] = yesterday_limit_down_count

        # 今日连板家数和昨日连板家数
        consecutive_limit_count_query = """
        SELECT 
            COUNT(DISTINCT CASE WHEN trade_date = %s AND limit_type = 'U' AND limit_times > 1 AND market_type IN ('STAR', 'HS', 'GEM') THEN ts_code END) AS today_consecutive_limit_count,
            COUNT(DISTINCT CASE WHEN trade_date = %s AND limit_type = 'U' AND limit_times > 1 AND market_type IN ('STAR', 'HS', 'GEM') THEN ts_code END) AS yesterday_consecutive_limit_count
        FROM limit_stocks
        """
        cursor.execute(consecutive_limit_count_query, (target_date_formatted, previous_date_formatted))
        today_consecutive_limit_count, yesterday_consecutive_limit_count = cursor.fetchone()
        market_data['limit_up_stats']['today_consecutive_limit_count'] = today_consecutive_limit_count
        market_data['limit_up_stats']['yesterday_consecutive_limit_count'] = yesterday_consecutive_limit_count

        # 获取前日连板但昨日未涨停的股票列表及连板天数
        pre_consecutive_not_limit_query = """
        SELECT DISTINCT ls.ts_code, ls.limit_times
        FROM limit_stocks ls
        WHERE ls.trade_date = %s 
        AND ls.limit_type = 'U' 
        AND ls.limit_times > 1 
        AND ls.market_type IN ('STAR', 'HS', 'GEM')
        AND ls.ts_code NOT IN (
            SELECT ts_code
            FROM limit_stocks
            WHERE trade_date = %s AND limit_type = 'U' AND market_type IN ('STAR', 'HS', 'GEM')
        )
        """
        cursor.execute(pre_consecutive_not_limit_query, (pre_previous_date_formatted, previous_date_formatted))
        pre_consecutive_not_limit_stocks = cursor.fetchall()

        if pre_consecutive_not_limit_stocks:
            stock_codes = [row[0][:6] for row in pre_consecutive_not_limit_stocks]
            limit_times_dict = {row[0][:6]: row[1] for row in pre_consecutive_not_limit_stocks}
            
            today_quote_query = """
            SELECT dd.stock_code, dd.stock_name, 
                   (dd.open_price - dd.previous_close_price) / dd.previous_close_price * 100 as open_change,
                   (dd.close_price - dd.previous_close_price) / dd.previous_close_price * 100 as close_change,
                   dd.turnover_rate_f as turnover_ratio,
                   dd.turnover_amount,
                   ls.industry,
                   ls.concept
            FROM daily_data dd
            JOIN limit_stocks ls ON dd.stock_code = LEFT(ls.ts_code, 6) AND ls.trade_date = %s
            WHERE dd.trade_date = %s AND dd.stock_code IN ({})
            """.format(','.join(['%s'] * len(stock_codes)))
            
            query_params = [pre_previous_date_formatted, target_date] + stock_codes
            cursor.execute(today_quote_query, query_params)
            today_quotes = cursor.fetchall()
            
            market_data['pre_consecutive_stocks'] = [
                {
                    'stock_code': quote[0],
                    'stock_name': quote[1],
                    'limit_times': str(limit_times_dict[quote[0]]),
                    'open_change': format_change_rate(quote[0], quote[2]),
                    'close_change': format_change_rate(quote[0], quote[3]),
                    'turnover_ratio': int(quote[4]) if quote[4] else 0,
                    'amount': quote[5] / 100000,  # 从千元转换为亿元
                    'industry': quote[6],
                    'concept': quote[7]
                }
                for quote in sorted(today_quotes, key=lambda x: limit_times_dict[x[0]], reverse=True)
            ]
        else:
            market_data['pre_consecutive_stocks'] = []

        # 获取昨日连板今日未涨停的股票列表及连板天数
        yesterday_consecutive_not_limit_query = """
        SELECT DISTINCT ls.ts_code, ls.limit_times
        FROM limit_stocks ls
        WHERE ls.trade_date = %s 
        AND ls.limit_type = 'U' 
        AND ls.limit_times > 1 
        AND ls.market_type IN ('STAR', 'HS', 'GEM')
        AND ls.ts_code NOT IN (
            SELECT ts_code
            FROM limit_stocks
            WHERE trade_date = %s AND limit_type = 'U' AND market_type IN ('STAR', 'HS', 'GEM')
        )
        """
        cursor.execute(yesterday_consecutive_not_limit_query, (previous_date_formatted, target_date_formatted))
        yesterday_consecutive_not_limit_stocks = cursor.fetchall()

        if yesterday_consecutive_not_limit_stocks:
            stock_codes = [row[0][:6] for row in yesterday_consecutive_not_limit_stocks]
            limit_times_dict = {row[0][:6]: row[1] for row in yesterday_consecutive_not_limit_stocks}
            
            today_quote_query = """
            SELECT dd.stock_code, dd.stock_name, 
                   (dd.open_price - dd.previous_close_price) / dd.previous_close_price * 100 as open_change,
                   (dd.close_price - dd.previous_close_price) / dd.previous_close_price * 100 as close_change,
                   dd.turnover_rate_f as turnover_ratio,
                   dd.turnover_amount,
                   ls.industry,
                   ls.concept
            FROM daily_data dd
            JOIN limit_stocks ls ON dd.stock_code = LEFT(ls.ts_code, 6) AND ls.trade_date = %s
            WHERE dd.trade_date = %s AND dd.stock_code IN ({})
            """.format(','.join(['%s'] * len(stock_codes)))
            query_params = [previous_date_formatted, target_date] + stock_codes
            cursor.execute(today_quote_query, query_params)
            today_quotes = cursor.fetchall()
            
            market_data['yesterday_consecutive_stocks'] = [
                {
                    'stock_code': quote[0],
                    'stock_name': quote[1],
                    'limit_times': str(limit_times_dict[quote[0]]),
                    'open_change': format_change_rate(quote[0], quote[2]),
                    'close_change': format_change_rate(quote[0], quote[3]),
                    'turnover_ratio': int(quote[4]) if quote[4] else 0,
                    'amount': quote[5] / 100000,  # 从千元转换为亿元
                    'industry': quote[6],
                    'concept': quote[7]
                }
                for quote in sorted(today_quotes, key=lambda x: limit_times_dict[x[0]], reverse=True)
            ]
        else:
            market_data['yesterday_consecutive_stocks'] = []

        # 从涨跌停板上获取当日的连续涨停股票的，按照连板天数从高到低输出
        consecutive_limit_stocks_query = """
        SELECT ls.ts_code, s.stock_name, ls.limit_times, ls.first_time, ls.last_time, 
               ls.concept, ls.industry, ls.turnover_ratio, ls.amount, 
               ls.float_mv, ls.total_mv, ls.limit_amount
        FROM limit_stocks ls
        JOIN stock s ON ls.ts_code = s.stock_code
        WHERE ls.trade_date = %s AND ls.limit_type = 'U' AND ls.limit_times > 1 AND ls.market_type IN ('STAR', 'HS', 'GEM')
        ORDER BY ls.limit_times DESC
        """
        cursor.execute(consecutive_limit_stocks_query, (target_date_formatted,))
        consecutive_limit_stocks = cursor.fetchall()

        # 添加详细的调试打印
        for stock in consecutive_limit_stocks:
            print(f"股票: {stock[1]}")
            print(f"原始first_time: {stock[3]}, 类型: {type(stock[3])}")
            print(f"原始last_time: {stock[4]}, 类型: {type(stock[4])}")
            print(f"格式化后first_time: {format_time(stock[3])}")
            print(f"格式化后last_time: {format_time(stock[4])}")
            print("---")

        # 修改当日连板股票数据处理
        stocks_data = [
            {
                'limit_times': stock[2],
                'name': stock[1],
                'stock_code': stock[0][:6],  # 添加股票代码
                'first_time': format_time(stock[3]),
                'last_time': format_time(stock[4]),
                'turnover_ratio': stock[7],
                'amount': f"{stock[8] / 100000000:.2f}" if stock[8] else "0.00",
                'concept': stock[5],
                'industry': stock[6],
                'total_mv': f"{stock[10] / 100000000:.2f}" if stock[10] else "0.00"
            }
            for stock in consecutive_limit_stocks
        ]

        # 添加调试打印
        print("处理后的数据:", stocks_data)

        # 将处理后的数据按连板天数分组
        market_data['consecutive_limit_stocks'] = group_consecutive_stocks(stocks_data)

        # 添加调试打印
        print("分组后的数据:", market_data['consecutive_limit_stocks'])

        # 获取所有涨跌停股票数据
        all_limit_stocks_query = """
        SELECT 
            ls.*, 
            ls.concept as core_concept  # 只获取核心概念
        FROM limit_stocks ls
        WHERE ls.trade_date = %s AND ls.market_type IN ('STAR', 'HS', 'GEM')
        """
        cursor.execute(all_limit_stocks_query, (target_date_formatted,))
        columns = [col[0] for col in cursor.description]
        all_limit_stocks = []
        
        for row in cursor.fetchall():
            stock_dict = dict(zip(columns, row))
            # 打印一下跌停股票的数据，看看字段情况
            if stock_dict.get('limit_type') == 'D':
                print("跌停股票数据:", stock_dict)
            
            # 格式化数据
            if stock_dict['amount'] is not None:
                stock_dict['amount'] = f"{stock_dict['amount'] / 100000000:.2f}"
            if stock_dict['float_mv'] is not None:
                stock_dict['float_mv'] = f"{stock_dict['float_mv'] / 100000000:.2f}"
            if stock_dict['total_mv'] is not None:
                stock_dict['total_mv'] = f"{stock_dict['total_mv'] / 100000000:.2f}"
            if stock_dict['limit_amount'] is not None:
                stock_dict['limit_amount'] = f"{stock_dict['limit_amount'] / 100000000:.2f}"
            
            # 格式化时间
            stock_dict['first_time'] = format_time(stock_dict['first_time'])
            stock_dict['last_time'] = format_time(stock_dict['last_time'])
            
            # 转换涨停类型
            stock_dict['limit_type'] = {
                'U': '涨停',
                'D': '跌停',
                'Z': '炸板'
            }.get(stock_dict['limit_type'], stock_dict['limit_type'])
            stock_dict['stock_code'] = stock_dict['ts_code'][:6]    
            all_limit_stocks.append(stock_dict)
        
        market_data['all_limit_stocks'] = all_limit_stocks

        # 修改概念统计部分
        market_data['concept_stats'] = process_concept_stocks(all_limit_stocks)

        # 昨日涨停股今日表现
        yesterday_limit_query = """
        SELECT dd.stock_code, (dd.close_price - dd.previous_close_price) / dd.previous_close_price * 100
        FROM daily_data dd
        JOIN (
            SELECT LEFT(ts_code, 6) as stock_code
            FROM limit_stocks
            WHERE trade_date = %s AND limit_type = 'U' AND market_type IN ('STAR', 'HS', 'GEM')
        ) ls ON dd.stock_code = ls.stock_code
        WHERE dd.trade_date = %s
        """
        cursor.execute(yesterday_limit_query, (previous_date_formatted, target_date_formatted))
        yesterday_limit_gains = [result[1] for result in cursor.fetchall()]
        if yesterday_limit_gains:
            market_data['yesterday_stats']['limit_up_median_gain'] = format_change_rate('000000', np.median(yesterday_limit_gains))
            market_data['yesterday_stats']['limit_up_avg_gain'] = format_change_rate('000000', np.mean(yesterday_limit_gains))
        else:
            market_data['yesterday_stats']['limit_up_median_gain'] = "无数据"
            market_data['yesterday_stats']['limit_up_avg_gain'] = "无数据"

        # 昨日首次涨停股今日表现
        yesterday_first_limit_query = """
        SELECT dd.stock_code, (dd.close_price - dd.previous_close_price) / dd.previous_close_price * 100
        FROM daily_data dd
        JOIN (
            SELECT LEFT(ts_code, 6) as stock_code
            FROM limit_stocks
            WHERE trade_date = %s AND limit_type = 'U' AND limit_times = 1 AND market_type IN ('STAR', 'HS', 'GEM')
        ) ls ON dd.stock_code = ls.stock_code
        WHERE dd.trade_date = %s
        """
        cursor.execute(yesterday_first_limit_query, (previous_date_formatted, target_date_formatted))
        yesterday_first_limit_gains = [result[1] for result in cursor.fetchall()]
        if yesterday_first_limit_gains:
            market_data['yesterday_stats']['first_limit_median_gain'] = format_change_rate('000000', np.median(yesterday_first_limit_gains))
            market_data['yesterday_stats']['first_limit_avg_gain'] = format_change_rate('000000', np.mean(yesterday_first_limit_gains))
        else:
            market_data['yesterday_stats']['first_limit_median_gain'] = "无数据"
            market_data['yesterday_stats']['first_limit_avg_gain'] = "无数据"

        # 昨日炸板股今日表现
        yesterday_broken_query = """
        SELECT dd.stock_code, (dd.close_price - dd.previous_close_price) / dd.previous_close_price * 100
        FROM daily_data dd
        JOIN (
            SELECT LEFT(ts_code, 6) as stock_code
            FROM limit_stocks
            WHERE trade_date = %s AND limit_type = 'Z' AND market_type IN ('STAR', 'HS', 'GEM')
        ) ls ON dd.stock_code = ls.stock_code
        WHERE dd.trade_date = %s
        """
        cursor.execute(yesterday_broken_query, (previous_date_formatted, target_date_formatted))
        yesterday_broken_gains = [result[1] for result in cursor.fetchall()]
        if yesterday_broken_gains:
            market_data['yesterday_stats']['board_broken_median_gain'] = format_change_rate('000000', np.median(yesterday_broken_gains))
            market_data['yesterday_stats']['board_broken_avg_gain'] = format_change_rate('000000', np.mean(yesterday_broken_gains))
        else:
            market_data['yesterday_stats']['board_broken_median_gain'] = "无数据"
            market_data['yesterday_stats']['board_broken_avg_gain'] = "无数据"

        # 获取近10天的上涨下跌家数
        updown_query = """
        WITH dates AS (
            SELECT DISTINCT trade_date 
            FROM limit_stats 
            WHERE trade_date <= %s 
            ORDER BY trade_date DESC 
            LIMIT 10
        )
        SELECT ls.trade_date, ls.item, ls.count
        FROM limit_stats ls
        JOIN dates d ON ls.trade_date = d.trade_date
        WHERE ls.item IN ('up_count', 'down_count')
        ORDER BY ls.trade_date ASC
        """
        cursor.execute(updown_query, (target_date_formatted,))
        updown_results = cursor.fetchall()
        
        print("\n原始数据:")
        for row in updown_results:
            print(f"日期: {row[0]}, 项目: {row[1]}, 数量: {row[2]}")

        # 处理数据为两个列表
        dates = []
        up_counts = []
        down_counts = []
        temp_data = {}  # 用于临时存储每个日期的数据

        # 先按日期整理数据
        for row in updown_results:
            date = row[0]
            item = row[1]
            count = row[2]
            
            if date not in temp_data:
                temp_data[date] = {'up_count': None, 'down_count': None}
            
            if item == 'up_count':
                temp_data[date]['up_count'] = count
            elif item == 'down_count':
                temp_data[date]['down_count'] = count

        print("\n整理后的临时数据:")
        for date, counts in temp_data.items():
            print(f"日期: {date}, 上涨: {counts['up_count']}, 下跌: {counts['down_count']}")

        # 只保留同时有上涨和下跌数据的日期
        for date, counts in temp_data.items():
            if counts['up_count'] is not None and counts['down_count'] is not None:
                # 跳过上涨下跌都为0的数据
                if counts['up_count'] == 0 and counts['down_count'] == 0:
                    print(f"跳过零数据日期: {date}")
                    continue
                dates.append(date)
                up_counts.append(counts['up_count'])
                down_counts.append(counts['down_count'])

        print("\n最终数据:")
        for i in range(len(dates)):
            print(f"日期: {dates[i]}, 上涨: {up_counts[i]}, 下跌: {down_counts[i]}")

        market_data['updown_trend'] = {
            'dates': dates,
            'up_counts': up_counts,
            'down_counts': down_counts
        }

        # 获取近120天的涨跌停数据趋势
        limit_trend_query = """
        WITH dates AS (
            SELECT DISTINCT trade_date 
            FROM limit_stats 
            WHERE trade_date <= %s 
            ORDER BY trade_date DESC 
            LIMIT 120
        )
        SELECT ls.trade_date, ls.item, ls.count
        FROM limit_stats ls
        JOIN dates d ON ls.trade_date = d.trade_date
        WHERE ls.item IN ('limit_up_count', 'limit_down_count', 'broken_count', 'consecutive_count')
        ORDER BY ls.trade_date ASC
        """
        cursor.execute(limit_trend_query, (target_date_formatted,))
        limit_trend_results = cursor.fetchall()

        # 处理数据
        limit_dates = []
        limit_up_counts = []
        limit_down_counts = []
        broken_counts = []
        consecutive_counts = []
        temp_data = {}

        # 按日期整理数据
        for row in limit_trend_results:
            date = row[0]
            item = row[1]
            count = row[2]
            
            if date not in temp_data:
                temp_data[date] = {
                    'limit_up_count': None,
                    'limit_down_count': None,
                    'broken_count': None,
                    'consecutive_count': None
                }
            
            temp_data[date][item] = count

        # 只保留有完整数据的日期
        for date, counts in temp_data.items():
            if all(v is not None for v in counts.values()):
                limit_dates.append(date)
                limit_up_counts.append(counts['limit_up_count'])
                limit_down_counts.append(counts['limit_down_count'])
                broken_counts.append(counts['broken_count'])
                consecutive_counts.append(counts['consecutive_count'])

        market_data['limit_trend'] = {
            'dates': limit_dates,
            'limit_up_counts': limit_up_counts,
            'limit_down_counts': limit_down_counts,
            'broken_counts': broken_counts,
            'consecutive_counts': consecutive_counts
        }

        # 获取近30天的连板高度趋势
        max_consecutive_query = """
        SELECT ls.trade_date, 
               COALESCE(MAX(ls.limit_times), 0) as max_consecutive,
               (SELECT GROUP_CONCAT(name SEPARATOR ',') 
                FROM limit_stocks 
                WHERE trade_date = ls.trade_date 
                AND limit_type = 'U' 
                AND limit_times = COALESCE(MAX(ls.limit_times), 0)
                LIMIT 3) as stock_names
        FROM limit_stocks ls
        WHERE ls.trade_date <= %s 
        AND ls.trade_date >= DATE_SUB(%s, INTERVAL 30 DAY)
        AND ls.limit_type = 'U'
        AND EXISTS (
            SELECT 1 FROM limit_stocks 
            WHERE trade_date = ls.trade_date 
            AND limit_type = 'U'
        )
        GROUP BY ls.trade_date
        ORDER BY ls.trade_date ASC
        """
        cursor.execute(max_consecutive_query, (target_date_formatted, target_date_formatted))
        max_consecutive_results = cursor.fetchall()

        # 处理数据
        consecutive_dates = []
        max_consecutive_values = []
        max_consecutive_stocks = []

        for row in max_consecutive_results:
            date = row[0]
            max_consecutive = row[1]
            stock_names = row[2] if row[2] else ""
            
            # 只添加有涨停数据的日期
            if max_consecutive > 0:
                consecutive_dates.append(date)
                max_consecutive_values.append(max_consecutive)
                max_consecutive_stocks.append(stock_names)

        market_data['consecutive_height_trend'] = {
            'dates': consecutive_dates,
            'max_consecutive_values': max_consecutive_values,
            'max_consecutive_stocks': max_consecutive_stocks
        }

        cursor.close()
        connection.close()
        return market_data

    except mysql.connector.Error as error:
        print("数据库错误:", error)
        return {
            'index_changes': [],
            'market_overview': {'up_count': 0, 'down_count': 0},
            'range_distribution': {'ranges': [], 'counts': []},
            'limit_up_stats': {
                'today_limit_count': 0,
                'yesterday_limit_count': 0,
                'today_gem_star_limit_up_count': 0,
                'yesterday_gem_star_limit_up_count': 0,
                'today_board_broken_rate': 0,
                'yesterday_board_broken_rate': 0,
                'today_limit_down_count': 0,
                'yesterday_limit_down_count': 0,
                'today_consecutive_limit_count': 0,
                'yesterday_consecutive_limit_count': 0
            },
            'consecutive_limit_stocks': [],
            'all_limit_stocks': [],
            'concept_stats': [],
            'yesterday_stats': {},
            'pre_consecutive_stocks': [],
            'yesterday_consecutive_stocks': [],
            'updown_trend': {},
            'limit_trend': {}
        }

def group_consecutive_stocks(stocks):
    """按连板天数分组处理股票数据"""
    # 按连板天数排序，但保持原始数据结构不变
    sorted_stocks = sorted(stocks, key=lambda x: x['limit_times'], reverse=True)
    
    # 确保每个股票数据包含所有必要的字段，但不重新格式化时间
    for stock in sorted_stocks:
        stock['name'] = stock.get('name', '')
        stock['turnover_ratio'] = stock.get('turnover_ratio', 0)
        stock['amount'] = stock.get('amount', '0.00')
        stock['total_mv'] = stock.get('total_mv', '0.00')
        stock['industry'] = stock.get('industry', '')
        stock['concept'] = stock.get('concept', '')
        stock['limit_times'] = stock.get('limit_times', 0)
        # 保持原始的时间格式
        stock['first_time'] = stock.get('first_time', '')
        stock['last_time'] = stock.get('last_time', '')
    
    return sorted_stocks

def process_concept_stocks(stocks_data):
    """按概念分类处理股票数据"""
    concept_stats = {}
    
    # 遍历所有股票，按概念分类
    for stock in stocks_data:
        # 处理所有概念
        concepts = stock.get('concept', '').split(',')
        for concept in concepts:
            concept = concept.strip()
            if not concept or concept == '-':
                continue
                
            if concept not in concept_stats:
                concept_stats[concept] = {
                    'name': concept,
                    'limit_up_stocks': [],    # 涨停股票
                    'broken_stocks': [],      # 炸板股票
                    'limit_down_stocks': [],  # 跌停股票
                    'up_count': 0,            # 涨停数
                    'broken_count': 0,        # 炸板数
                    'down_count': 0           # 跌停数
                }
            
            # 准备股票数据
            stock_info = {
                'stock_code': stock['ts_code'][:6],  # 添加股票代码
                'stock_name': stock['name'],
                'limit_times': stock.get('limit_times', 0),
                'first_time': stock.get('first_time', ''),
                'last_time': stock.get('last_time', ''),
                'turnover_ratio': stock.get('turnover_ratio', 0),
                'amount': stock.get('amount', '0.00'),
                'total_mv': stock.get('total_mv', '0.00'),
                'industry': stock.get('industry', ''),
                'concept': stock.get('concept', ''),
                'core_concept': stock.get('core_concept', ''),
                'pct_chg': stock.get('pct_chg', 0),  # 使用 pct_chg 字段
                'limit_amount': stock.get('limit_amount', '0.00'),
                'close_change': stock.get('pct_chg', 0)  # 添加收盘涨幅字段
            }
            
            # 根据股票类型归类
            if stock['limit_type'] == '涨停':
                concept_stats[concept]['limit_up_stocks'].append(stock_info)
                concept_stats[concept]['up_count'] += 1
            elif stock['limit_type'] == '炸板':
                concept_stats[concept]['broken_stocks'].append(stock_info)
                concept_stats[concept]['broken_count'] += 1
            elif stock['limit_type'] == '跌停':
                concept_stats[concept]['limit_down_stocks'].append(stock_info)
                concept_stats[concept]['down_count'] += 1
    
    # 转换为列表并按涨停数量排序
    concept_list = list(concept_stats.values())
    # 过滤掉涨停家数小于等于2的概念
    concept_list = [concept for concept in concept_list if concept['up_count'] > 2]
    concept_list.sort(key=lambda x: x['up_count'], reverse=True)
    
    # 对每个概念内的股票列表进行排序
    for concept in concept_list:
        # 涨停股票按连板天数降序
        concept['limit_up_stocks'].sort(key=lambda x: x['limit_times'], reverse=True)
        # 炸板股票按收盘涨幅降序
        concept['broken_stocks'].sort(key=lambda x: float(x['pct_chg']) if x['pct_chg'] else 0, reverse=True)
        # 跌停股票按连板天数降序
        concept['limit_down_stocks'].sort(key=lambda x: x['limit_times'], reverse=True)
    
    return concept_list
