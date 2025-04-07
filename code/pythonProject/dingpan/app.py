from flask import Flask, render_template, jsonify, request
from datetime import datetime
import pymysql
import pandas as pd
import threading
from get_realtime_quotes import QuotesManager
import time

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
    conn = get_db_connection()
    try:
        # 获取涨停统计
        stats_sql = """
            SELECT 
                COUNT(*) as total_limit_up,
                SUM(CASE WHEN ts_code LIKE '300%' OR ts_code LIKE '688%' THEN 1 ELSE 0 END) as gem_limit_up,
                COUNT(DISTINCT CASE WHEN first_limit_up_time IS NOT NULL THEN ts_code END) as new_limit_up
            FROM realtime_quotes
            WHERE trade_date = CURDATE() AND is_up_limit = 1
        """
        stats_df = pd.read_sql(stats_sql, conn)
        
        # 获取行业涨停分布
        industry_sql = """
            SELECT 
                s.industry,
                COUNT(*) as limit_up_count
            FROM realtime_quotes r
            JOIN stock s ON r.ts_code = s.ts_code
            WHERE r.trade_date = CURDATE() AND r.is_up_limit = 1
            GROUP BY s.industry
            ORDER BY limit_up_count DESC
        """
        industry_df = pd.read_sql(industry_sql, conn)
        
        return jsonify({
            'statistics': stats_df.to_dict('records')[0],
            'industry_distribution': industry_df.to_dict('records')
        })
    finally:
        conn.close()

@app.route('/api/stock_kline/<ts_code>')
def stock_kline(ts_code):
    """获取个股K线数据"""
    conn = get_db_connection()
    try:
        # 获取近120天日线数据
        kline_sql = """
            SELECT trade_date, open, high, low, close, volume, amount
            FROM daily_quotes
            WHERE ts_code = %s
            AND trade_date >= DATE_SUB(CURDATE(), INTERVAL 120 DAY)
            ORDER BY trade_date
        """
        kline_df = pd.read_sql(kline_sql, conn, params=(ts_code,))
        
        # 获取今日实时数据
        today_sql = """
            SELECT trade_date, open, high, low, price as close, volume, amount
            FROM realtime_quotes
            WHERE ts_code = %s AND trade_date = CURDATE()
        """
        today_df = pd.read_sql(today_sql, conn, params=(ts_code,))
        
        # 合并数据
        if not today_df.empty:
            kline_df = kline_df.append(today_df.iloc[0], ignore_index=True)
        
        return jsonify(kline_df.to_dict('records'))
    finally:
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