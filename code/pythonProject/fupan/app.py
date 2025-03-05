from flask import Flask, render_template, request
from fupan import get_market_analysis, format_change_rate, process_concept_stocks  # 直接导入
from datetime import datetime, timedelta
import tushare as ts
import mysql.connector

app = Flask(__name__)

# Tushare配置
ts.set_token('i593c24d0926bfb845f136082a335d64f71')
pro = ts.pro_api()

@app.route('/')
def index():
    # 获取日期参数，如果没有则使用默认值
    today = request.args.get('today', datetime.now().strftime('%Y-%m-%d'))
    yesterday = request.args.get('yesterday', (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
    pre_day = request.args.get('pre_day', (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'))
    
    # 转换日期格式
    dates = {
        'today': today,
        'yesterday': yesterday,
        'pre_day': pre_day
    }

    market_data = get_market_analysis(today, yesterday, pre_day)
    
    # 处理概念统计
    if 'all_limit_stocks' in market_data:
        concept_stats = process_concept_stocks(market_data['all_limit_stocks'])
        market_data['concept_stats'] = concept_stats
    
    return render_template('market.html', 
                         data=market_data, 
                         format_change_rate=format_change_rate,
                         dates=dates)

@app.route('/stock_kline/')  # 添加一个处理空路径的路由
def stock_kline_error():
    return {'code': 1, 'msg': '请提供股票代码'}, 400

@app.route('/stock_kline/<stock_code>')
def stock_kline(stock_code):
    print("123")
    if not stock_code:  # 添加参数验证
        print("code 为空")
        return {'code': 1, 'msg': '股票代码不能为空'}, 400
    
    try:
        # 添加数据库配置
        config = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'database': 'happy',
            'raise_on_warnings': True
        }
        
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        print(f"正在查询股票代码: {stock_code} 的K线数据") # 调试日志
        
        # 获取最近120天的日线数据，按日期降序排序后取120条，再按日期升序输出
        kline_query = """
        WITH recent_dates AS (
            SELECT trade_date
            FROM daily_data 
            WHERE stock_code = %s
            ORDER BY trade_date DESC
            LIMIT 120
        )
        SELECT dd.trade_date, dd.open_price, dd.close_price, dd.low_price, dd.high_price, 
               dd.turnover_amount, dd.ma_5, dd.ma_10, dd.ma_20, dd.ma_60
        FROM daily_data dd
        JOIN recent_dates rd ON dd.trade_date = rd.trade_date
        WHERE dd.stock_code = %s
        ORDER BY dd.trade_date ASC
        """
        
        cursor.execute(kline_query, (stock_code, stock_code))
        data = cursor.fetchall()
        
        print(f"查询到 {len(data)} 条数据") # 调试日志
        if len(data) > 0:
            print(f"第一条数据: {data[0]}") # 调试日志
        
        # 格式化数据
        kline_data = []
        for row in data:
            kline_data.append({
                'trade_date': row[0].strftime('%Y-%m-%d'),
                'open': float(row[1]),
                'close': float(row[2]),
                'low': float(row[3]),
                'high': float(row[4]),
                'amount': round(float(row[5]) / 100000, 2),  # 转换为亿元并保留两位小数
                'ma_5': float(row[6]) if row[6] else None,
                'ma_10': float(row[7]) if row[7] else None,
                'ma_20': float(row[8]) if row[8] else None,
                'ma_60': float(row[9]) if row[9] else None
            })
        
        cursor.close()
        connection.close()
        
        result = {'code': 0, 'data': kline_data}
        print(f"返回数据: {result}") # 调试日志
        return result
        
    except Exception as e:
        print(f"发生错误: {str(e)}") # 调试日志
        return {'code': 1, 'msg': str(e)}

def format_change_rate(code, rate):
    """格式化涨跌幅"""
    # 如果是字符串，先转换为数字
    if isinstance(rate, str):
        try:
            rate = float(rate.strip('%').strip('+'))
        except (ValueError, AttributeError):
            return rate
    
    # 如果是 None，返回 0%
    if rate is None:
        return '0.00%'
        
    try:
        if rate > 0:
            return f'<span class="text-red">+{rate:.2f}%</span>'
        elif rate < 0:
            return f'<span class="text-green">{rate:.2f}%</span>'
        return f'{rate:.2f}%'
    except:
        return '0.00%'

# 注册模板过滤器
app.jinja_env.filters['format_change_rate'] = format_change_rate

if __name__ == '__main__':
    app.run(debug=True) 