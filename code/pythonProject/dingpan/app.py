from flask import Flask, render_template, jsonify, request
from datetime import datetime
import pymysql
import pandas as pd
import threading
from get_realtime_quotes import QuotesManager
import time
import numpy as np

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

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/market_overview')
def market_overview():
    """获取市场概览数据"""
    global quotes_manager
    if not quotes_manager:
        return jsonify({'error': 'Quotes manager not initialized'})

    try:
        return jsonify({
            'indices': quotes_manager.get_index_quotes(),
            'amount_trend': quotes_manager.get_amount_trend(),
            'statistics': quotes_manager.get_market_stats()
        })
    except Exception as e:
        log(f"获取市场概览数据失败: {str(e)}")
        return jsonify({'error': str(e)})

@app.route('/api/stock_list')
def get_stock_list():
    """获取个股列表"""
    try:
        sort_by = request.args.get('sort_by', 'change_pct')  # 默认按涨幅排序
        order = request.args.get('order', 'desc')  # 默认降序
        
        # 获取原始数据
        stocks = list(quotes_manager.get_stock_list())
        
        # 计算早盘未竞价金额
        for stock in stocks:
            stock['non_bid_amount'] = (stock.get('amount', 0) or 0) - (stock.get('bid_amount', 0) or 0)
        
        # 排序
        reverse = order == 'desc'
        stocks.sort(key=lambda x: float(x.get(sort_by, 0) or 0), reverse=reverse)
        
        # 只返回前100条数据
        return jsonify(stocks[:100])
        
    except Exception as e:
        log(f"获取个股列表失败: {str(e)}")
        return jsonify([])

@app.route('/api/limit_up_analysis')
def limit_up_analysis():
    """获取涨停分析数据"""
    global quotes_manager
    if not quotes_manager:
        print("行情管理器未初始化")
        return jsonify({'error': 'Quotes manager not initialized'})

    try:
        market_stats = quotes_manager.get_market_stats()
        concept_stats = quotes_manager.get_concept_stats()
        last_trade_date_stats = quotes_manager.get_last_trade_date_stats()
        
        print("市场统计数据:", market_stats)  # 添加调试日志
        print("概念统计数据:", concept_stats)  # 添加调试日志
        
        # 获取涨停股票列表
        limit_up_stocks = []
        for ts_code, stock in market_stats.get('limit_ups', {}).items():
            limit_up_stocks.append({
                'ts_code': ts_code,
                'name': stock['name'],
                'change_pct': stock['change_pct'],
                'continuous_days': 1 + (1 if stock['is_continuous'] else 0),
                'first_limit_time': stock.get('first_limit_time', '-'),
                'amount': stock['amount'] / 100000000,  # 转换为亿
                'industry': stock['industry'],
                'concepts': stock['concepts'],
                'is_broken': ts_code in market_stats.get('broken_limits', {})
            })
        
        # 获取概念统计
        concept_summary = []
        for concept, stats in concept_stats.items():
            # 计算创业板涨停数
            gem_limit_ups = [s for s in stats['limit_ups'] 
                             if s['ts_code'].startswith(('300', '301', '688'))]
            
            concept_summary.append({
                'concept': concept,
                'limit_up_count': stats['limit_up_count'],
                'continuous_count': len([s for s in stats['limit_ups'] 
                                       if s['ts_code'] in market_stats.get('limit_ups', {}) 
                                       and market_stats['limit_ups'][s['ts_code']]['is_continuous']]),
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
            'last_trade_date_stats': last_trade_date_stats,  # 添加昨日统计数据
            'concept_stats': concept_summary,
            'limit_stocks': limit_up_stocks
        }
        
        print("返回数据:", response_data)  # 添加调试日志
        return jsonify(response_data)
        
    except Exception as e:
        print(f"获取涨停分析数据失败: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印完整错误堆栈
        return jsonify({'error': str(e)})

@app.route('/api/stock_kline/<ts_code>')
def stock_kline(ts_code):
    """获取个股K线数据"""
    stock_code = ts_code[:6]
    print(f"\n开始获取股票 {ts_code} (代码: {stock_code}) 的K线数据...")
    
    # 从内存中获取行业和概念信息
    stock_info = {'industry': '-', 'concepts': '-'}
    for quote in quotes_manager.quotes_data:
        if quote['ts_code'] == ts_code:
            stock_info = {
                'industry': quote.get('industry', '-'),
                'concepts': quote.get('concepts', '-').split(',')  # 转换为列表
            }
            break
    
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
            ORDER BY trade_date DESC 
            LIMIT 240
        """
        cursor.execute(kline_sql, (stock_code,))
        results = cursor.fetchall()
        print(f"从数据库获取到 {len(results)} 条K线记录")
        
        # 转换为DataFrame并按日期正序排列
        kline_df = pd.DataFrame(results)
        if not kline_df.empty:
            kline_df = kline_df.sort_values('trade_date')
            kline_df = kline_df.reset_index(drop=True)
            print(f"数据日期范围: {kline_df['trade_date'].iloc[0]} 至 {kline_df['trade_date'].iloc[-1]}")
            print(f"最新收盘价: {kline_df['close'].iloc[-1]}")
            
            # 从内存中获取今日实时数据
            today_quote = None
            for quote in quotes_manager.quotes_data:
                print(f"quote: {quote}")
                if quote['ts_code'] == ts_code:
                    today_quote = quote
                    print("\n今日实时数据详情:")
                    print(f"股票代码: {quote['ts_code']}")
                    print(f"股票名称: {quote.get('NAME', '-')}")
                    print(f"开盘价: {quote.get('OPEN', '-')}")
                    print(f"最高价: {quote.get('HIGH', '-')}")
                    print(f"最低价: {quote.get('LOW', '-')}")
                    print(f"当前价: {quote.get('PRICE', '-')}")
                    print(f"成交量: {quote.get('VOLUME', '-')}")
                    print(f"成交额: {quote.get('AMOUNT', '-')}")
                    print(f"涨跌幅: {quote.get('CHANGE_PCT', '-')}%")
                    break
            
            # 如果有实时数据，更新或添加到K线数据中
            if today_quote:
                print(f"today_quote: {today_quote}")
                today_date = datetime.now().strftime('%Y-%m-%d')
                today_data = {
                    'trade_date': today_date,
                    'open': float(today_quote['open']),
                    'high': float(today_quote['high']),  
                    'low': float(today_quote['low']),   
                    'close': float(today_quote['price']),
                    'volume': float(today_quote['amount']/today_quote['price']),  # 用成交额除以价格估算成交量
                    'amount': float(today_quote['amount'])/1000
                }
                
                # 如果最后一条记录是今天的数据，则更新它
                if kline_df['trade_date'].iloc[-1] == today_date:
                    print(f"更新今日({today_date})实时数据")
                    kline_df.iloc[-1, kline_df.columns.get_loc('open')] = today_data['open']
                    kline_df.iloc[-1, kline_df.columns.get_loc('high')] = today_data['high']
                    kline_df.iloc[-1, kline_df.columns.get_loc('low')] = today_data['low']
                    kline_df.iloc[-1, kline_df.columns.get_loc('close')] = today_data['close']
                    kline_df.iloc[-1, kline_df.columns.get_loc('volume')] = today_data['volume']
                    kline_df.iloc[-1, kline_df.columns.get_loc('amount')] = today_data['amount']
                else:
                    print(f"添加今日({today_date})实时数据")
                    today_df = pd.DataFrame([today_data])
                    kline_df = pd.concat([kline_df, today_df], ignore_index=True)
                
                # 计算最新的均线
                closes = kline_df['close'].astype(float).tolist()
                
                if len(closes) >= 5:
                    kline_df.iloc[-1, kline_df.columns.get_loc('ma_5')] = sum(closes[-5:]) / 5
                if len(closes) >= 10:
                    kline_df.iloc[-1, kline_df.columns.get_loc('ma_10')] = sum(closes[-10:]) / 10
                if len(closes) >= 20:
                    ma20 = sum(closes[-20:]) / 20
                    kline_df.iloc[-1, kline_df.columns.get_loc('ma_20')] = ma20
                    # 计算BOLL
                    std = np.std(closes[-20:])
                    kline_df.iloc[-1, kline_df.columns.get_loc('boll_mid')] = ma20
                    kline_df.iloc[-1, kline_df.columns.get_loc('boll_up')] = ma20 + 2 * std
                    kline_df.iloc[-1, kline_df.columns.get_loc('boll_low')] = ma20 - 2 * std
                if len(closes) >= 60:
                    kline_df.iloc[-1, kline_df.columns.get_loc('ma_60')] = sum(closes[-60:]) / 60
                
                print(f"合并后数据范围: {kline_df['trade_date'].iloc[0]} 至 {kline_df['trade_date'].iloc[-1]}")
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