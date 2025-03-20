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
    # 获取日期参数
    target_date = request.args.get('date')
    print('收到请求:', {
        'stock_code': stock_code,
        'target_date': target_date,
        'all_args': request.args,
        'headers': dict(request.headers),
        'url': request.url,
        'full_path': request.full_path
    })

    if not target_date:
        print('未提供日期参数')
        return {'code': 1, 'msg': '请提供日期参数'}, 400

    if not stock_code:
        print('未提供股票代码')
        return {'code': 1, 'msg': '股票代码不能为空'}, 400
    
    try:
        config = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'database': 'happy',
            'raise_on_warnings': True,
            'auth_plugin': 'mysql_native_password'
        }
        
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        print(f"正在查询股票代码: {stock_code} 的K线数据")
        
        # 从指定日期开始获取最近120天的日线数据
        kline_query = """
        SELECT dd.trade_date, dd.open_price, dd.close_price, dd.low_price, dd.high_price, 
               dd.turnover_amount, dd.ma_5, dd.ma_10, dd.ma_20, dd.ma_60,
               dd.boll_up, dd.boll_mid, dd.boll_low
        FROM daily_data dd
        WHERE dd.stock_code = %s
        AND dd.trade_date <= %s
        ORDER BY dd.trade_date DESC
        LIMIT 120
        """
        
        cursor.execute(kline_query, (stock_code, target_date))
        data = cursor.fetchall()
        data = list(reversed(data))  # 反转数据，使其按日期升序
        
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
                'ma_60': float(row[9]) if row[9] else None,
                'boll_up': float(row[10]) if row[10] else None,
                'boll_mid': float(row[11]) if row[11] else None,
                'boll_low': float(row[12]) if row[12] else None
            })
        
        cursor.close()
        connection.close()
        
        result = {'code': 0, 'data': kline_data}
        return result
        
    except Exception as e:
        print(f"发生错误: {str(e)}") # 调试日志
        return {'code': 1, 'msg': str(e)}

@app.route('/index_kline/<index_code>')
def index_kline(index_code):
    if not index_code:
        return {'code': 1, 'msg': '指数代码不能为空'}, 400
    
    try:
        config = {
            'user': 'root',
            'password': 'root',
            'host': 'localhost',
            'database': 'happy',
            'raise_on_warnings': True,
            'auth_plugin': 'mysql_native_password'
        }
        
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        # 获取最近120天的日线数据
        kline_query = """
        WITH recent_dates AS (
            SELECT trade_date
            FROM index_daily_data 
            WHERE ts_code = %s
            ORDER BY trade_date DESC
            LIMIT 120
        )
        SELECT idd.trade_date, idd.open, idd.close, idd.low, idd.high, 
               idd.amount,
               idd.ma_5, idd.ma_10, idd.ma_20, idd.ma_60,
               idd.boll_up, idd.boll_mid, idd.boll_low
        FROM index_daily_data idd
        JOIN recent_dates rd ON idd.trade_date = rd.trade_date
        WHERE idd.ts_code = %s
        ORDER BY idd.trade_date ASC
        """
        
        cursor.execute(kline_query, (index_code, index_code))
        data = cursor.fetchall()
        
        # 格式化数据
        kline_data = []
        for row in data:
            trade_date = row[0]
            # 将 trade_date 从字符串格式 (如 "20250309") 转换为 "2025-03-09" 格式
            formatted_date = f"{trade_date[:4]}-{trade_date[4:6]}-{trade_date[6:]}"
            
            kline_data.append({
                'trade_date': formatted_date,
                'open': float(row[1]) if row[1] is not None else None,
                'close': float(row[2]) if row[2] is not None else None,
                'low': float(row[3]) if row[3] is not None else None,
                'high': float(row[4]) if row[4] is not None else None,
                'amount': round(float(row[5]) / 100000, 2) if row[5] is not None else None,  # 从千元转换为亿元
                'ma_5': float(row[6]) if row[6] is not None else None,
                'ma_10': float(row[7]) if row[7] is not None else None,
                'ma_20': float(row[8]) if row[8] is not None else None,
                'ma_60': float(row[9]) if row[9] is not None else None,
                'boll_up': float(row[10]) if row[10] is not None else None,
                'boll_mid': float(row[11]) if row[11] is not None else None,
                'boll_low': float(row[12]) if row[12] is not None else None
            })
        
        cursor.close()
        connection.close()
        
        return {'code': 0, 'data': kline_data}
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
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