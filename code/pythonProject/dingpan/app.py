from flask import Flask, render_template, jsonify, request
from datetime import datetime
import pymysql
import pandas as pd
import threading
from get_realtime_quotes import QuotesManager
import time
import numpy as np
import historical_data

app = Flask(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'leewcc',
    'password': 'leewcc',
    'database': 'happy',
    'charset': 'utf8mb4'
}

# 全局变量存储行情管理器实例
quotes_manager = None

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def start_quotes_manager():
    """启动行情管理器"""
    global quotes_manager
    quotes_manager = QuotesManager()
    quotes_manager.start()

# 在应用启动时初始化 quotes_manager
@app.before_request
def init_app():
    """应用初始化"""
    global quotes_manager
    if quotes_manager is None:
        start_quotes_manager()

# 确保 historical_data 模块可以访问 quotes_manager
def get_quotes_manager():
    """获取行情管理器实例"""
    global quotes_manager
    if quotes_manager is None:
        start_quotes_manager()
    return quotes_manager

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/market_overview', defaults={'date': None})
@app.route('/api/market_overview/<date>')
def market_overview(date):
    if date is None:
        # 返回实时数据
        return jsonify({
            'indices': quotes_manager.get_index_quotes(),
            'statistics': quotes_manager.get_market_stats(),
            'amount_trend': quotes_manager.get_amount_trend()
        })
    else:
        # 返回历史数据
        return jsonify(historical_data.get_historical_market_overview(date))

@app.route('/api/stock_list', defaults={'date': None})
@app.route('/api/stock_list/<date>')
def stock_list(date):
    """获取股票列表"""
    try:
        sort_by = request.args.get('sort_by', 'change_pct')  # 默认按涨幅排序
        order = request.args.get('order', 'desc')  # 默认降序
        
        if date is None:
            # 获取实时数据
            stocks = list(quotes_manager.get_stock_list())
            
            # 计算早盘未竞价金额
            for stock in stocks:
                stock['non_bid_amount'] = (stock.get('amount', 0) or 0) - (stock.get('bid_amount', 0) or 0)
            
            # 排序
            reverse = order == 'desc'
            stocks.sort(key=lambda x: float(x.get(sort_by, 0) or 0), reverse=reverse)
            
            # 只返回前100条数据
            return jsonify(stocks[:100])
        else:
            # 返回历史数据
            return jsonify(historical_data.get_historical_stock_list(date, sort_by, order))
            
    except Exception as e:
        print(f"获取股票列表失败: {str(e)}")
        return jsonify([])

@app.route('/api/limit_up_analysis', defaults={'date': None})
@app.route('/api/limit_up_analysis/<date>')
def limit_up_analysis(date):
    """获取涨停分析数据"""
    try:
        if date is None:
            # 获取实时数据
            market_stats = quotes_manager.get_market_stats()
            concept_stats = quotes_manager.get_concept_stats()
            last_trade_date_stats = quotes_manager.get_last_trade_date_stats()
            
            # 获取所有相关股票列表
            stocks_list = []
            
            # 添加涨停股票
            for ts_code, stock in market_stats.get('limit_ups', {}).items():
                stocks_list.append({
                    'ts_code': ts_code,
                    'name': stock['name'],
                    'change_pct': stock['change_pct'],
                    'continuous_days': stock['limit_times'],
                    'first_limit_time': stock.get('first_limit_time', '-'),
                    'amount': stock['amount'] / 100000000,
                    'industry': stock['industry'],
                    'concepts': stock['concepts'],
                    'type': 'limit_up',
                    'is_broken': False
                })
                
            # 添加炸板股票
            for ts_code, stock in market_stats.get('broken_limits', {}).items():
                if ts_code not in [s['ts_code'] for s in stocks_list]:
                    stocks_list.append({
                        'ts_code': ts_code,
                        'name': stock['name'],
                        'change_pct': stock['change_pct'],
                        'continuous_days': 0,
                        'first_limit_time': stock.get('first_limit_time', '-'),
                        'amount': stock['amount'] / 100000000,
                        'industry': stock['industry'],
                        'concepts': stock['concepts'],
                        'type': 'broken',
                        'is_broken': True
                    })
                    
            # 添加跌停股票
            for ts_code, stock in market_stats.get('limit_downs', {}).items():
                if ts_code not in [s['ts_code'] for s in stocks_list]:
                    stocks_list.append({
                        'ts_code': ts_code,
                        'name': stock['name'],
                        'change_pct': stock['change_pct'],
                        'continuous_days': 0,
                        'first_limit_time': '-',
                        'amount': stock['amount'] / 100000000,
                        'industry': stock['industry'],
                        'concepts': stock['concepts'],
                        'type': 'limit_down',
                        'is_broken': False
                    })

            # 获取概念统计
            concept_summary = []
            for concept, stats in concept_stats.items():
                gem_limit_ups = [s for s in stats['limit_ups'] 
                                if s['ts_code'].startswith(('300', '301', '688'))]
                
                concept_summary.append({
                    'concept': concept,
                    'limit_up_count': stats['limit_up_count'],
                    'continuous_count': len([s for s in stats['limit_ups'] 
                                           if s['ts_code'] in market_stats.get('limit_ups', {}) 
                                           and market_stats['limit_ups'][s['ts_code']].get('limit_times', 1) > 1]),
                    'gem_limit_up_count': len(gem_limit_ups),
                    'broken_count': stats['broken_limit_count'],
                    'limit_down_count': stats['limit_down_count']
                })
            
            response_data = {
                'statistics': {
                    'limit_up_count': market_stats.get('limit_up_count', 0),
                    'gem_limit_up_count': market_stats.get('cyb_limit_up_count', 0) + market_stats.get('kc_limit_up_count', 0),
                    'broken_limit_count': market_stats.get('broken_limit_count', 0),
                    'limit_down_count': market_stats.get('limit_down_count', 0),
                    'continuous_limit_count': market_stats.get('continuous_limit_count', 0)
                },
                'last_trade_date_stats': last_trade_date_stats,
                'concept_stats': concept_summary,
                'limit_stocks': stocks_list
            }
            
            return jsonify(response_data)
        else:
            # 返回历史数据
            return jsonify(historical_data.get_historical_limit_analysis(date))
            
    except Exception as e:
        print(f"获取涨停分析数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)})

@app.route('/api/stock_kline/<ts_code>')
def stock_kline(ts_code):
    """获取个股K线数据"""
    stock_code = ts_code[:6]
    print(f"\n开始获取股票 {ts_code} (代码: {stock_code}) 的K线数据...")
    
    # 创建ts_code到quote的映射，提高查找效率（只创建一次）
    quotes_map = {quote['ts_code']: quote for quote in quotes_manager.quotes_data}
    
    # 从内存中获取行业和概念信息
    quote = quotes_map.get(ts_code)
    if quote:
        stock_info = {
            'industry': quote.get('industry', '-'),
            'concepts': quote.get('concepts', '-').split(',')  # 转换为列表
        }
    else:
        stock_info = {'industry': '-', 'concepts': '-'}
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        # 获取近240天日线数据
        kline_sql = """
            SELECT 
                DATE_FORMAT(trade_date, '%%Y-%%m-%%d') as trade_date,
                open_price as open,
                high_price as high,
                low_price as low,
                close_price as close,
                trading_volume as volume,
                turnover_amount as amount,
                ma_5, ma_10, ma_20, ma_60,
                boll_up, boll_mid, boll_low
            FROM daily_data
            WHERE stock_code = %s
            AND trade_date >= DATE_SUB(CURDATE(), INTERVAL 300 DAY)
            ORDER BY trade_date DESC 
            LIMIT 240
        """
        
        import time
        start_time = time.time()
        cursor.execute(kline_sql, (stock_code,))
        results = cursor.fetchall()
        end_time = time.time()
        query_time = end_time - start_time
        
        print(f"SQL查询耗时: {query_time:.4f} 秒")
        print(f"从数据库获取到 {len(results)} 条K线记录")
        
        # 转换为DataFrame并按日期正序排列
        kline_df = pd.DataFrame(results)
        if not kline_df.empty:
            kline_df = kline_df.sort_values('trade_date')
            kline_df = kline_df.reset_index(drop=True)
            
            # 检查今日是否已有数据
            today_date = datetime.now().strftime('%Y-%m-%d')
            has_today_data = not kline_df.empty and kline_df['trade_date'].iloc[-1] == today_date
            
            # 如果今日没有数据，则从实时数据获取
            if not has_today_data:
                today_quote = quotes_map.get(ts_code)
                
                if today_quote:
                    print(f"添加今日({today_date})实时数据")
                    today_data = {
                        'trade_date': today_date,
                        'open': float(today_quote['open']),
                        'high': float(today_quote['high']),  
                        'low': float(today_quote['low']),   
                        'close': float(today_quote['price']),
                        'volume': float(today_quote['amount']/today_quote['price']),  # 用成交额除以价格估算成交量
                        'amount': float(today_quote['amount'])/1000
                    }
                    
                    today_df = pd.DataFrame([today_data])
                    kline_df = pd.concat([kline_df, today_df], ignore_index=True)
                    
                    # 计算最新的均线（只有添加了今日数据才需要计算）
                    closes = kline_df['close'].astype(float).tolist()
                    
                    if len(closes) >= 5:
                        kline_df.iloc[-1, kline_df.columns.get_loc('ma_5')] = sum(closes[-5:]) / 5
                    if len(closes) >= 10:
                        kline_df.iloc[-1, kline_df.columns.get_loc('ma_10')] = sum(closes[-10:]) / 10
                    if len(closes) >= 20:
                        ma20 = sum(closes[-20:]) / 20
                        kline_df.iloc[-1, kline_df.columns.get_loc('ma_20')] = ma20
                        # 计算BOLL
                        import numpy as np
                        std = np.std(closes[-20:])
                        kline_df.iloc[-1, kline_df.columns.get_loc('boll_mid')] = ma20
                        kline_df.iloc[-1, kline_df.columns.get_loc('boll_up')] = ma20 + 2 * std
                        kline_df.iloc[-1, kline_df.columns.get_loc('boll_low')] = ma20 - 2 * std
                    if len(closes) >= 60:
                        kline_df.iloc[-1, kline_df.columns.get_loc('ma_60')] = sum(closes[-60:]) / 60
                
        else:
            print("未获取到K线数据")
        
        # 在返回数据时添加行业和概念信息
        response_data = {
            'kline': kline_df.to_dict('records'),
            'industry': stock_info['industry'],
            'concepts': stock_info['concepts']
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"获取K线数据失败: {str(e)}")
        return jsonify({
            'kline': [],
            'industry': '-',
            'concepts': []
        })
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    # 启动行情管理器
    print("Starting quotes manager...")
    start_quotes_manager()
    
    # 等待行情管理器初始化完成
    while not quotes_manager or not quotes_manager.is_ready():
        time.sleep(1)
        print("Waiting for quotes manager to initialize...")
    
    print("Quotes manager initialized, starting web server...")
    app.run(debug=True, port=8888) 
