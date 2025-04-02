from flask import Flask, render_template, jsonify, request
from xuangu_logic import get_stock_list, filter_stocks, get_industries, get_concepts, get_db_connection
import pandas as pd
import mysql.connector
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def index():
    industries = get_industries()
    concepts = get_concepts()
    return render_template('xuangu.html', industries=industries, concepts=concepts)

@app.route('/api/stocks', methods=['POST'])
def get_stocks():
    filters = request.json
    filtered_stocks = filter_stocks(filters)
    return jsonify(filtered_stocks)

@app.route('/stock_kline/<stock_code>')
def get_stock_kline(stock_code):
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
        # 转换日期格式为 YYYY-MM-DD
        if isinstance(target_date, str):
            try:
                # 尝试解析不同格式的日期
                for fmt in ['%Y-%m-%d', '%a, %d %b %Y %H:%M:%S GMT', '%Y%m%d']:
                    try:
                        parsed_date = datetime.strptime(target_date, fmt)
                        # 向后推5天
                        parsed_date = parsed_date + timedelta(days=5)
                        target_date = parsed_date.strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue
            except Exception as e:
                print(f"日期解析失败: {str(e)}")
                return {'code': 1, 'msg': '日期格式错误'}, 400

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
        
        print(f"正在查询股票代码: {stock_code} 的K线数据，日期: {target_date}")
        
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

@app.route('/deviation')
def deviation_page():
    return render_template('deviation.html')

@app.route('/api/deviation/<stock_code>')
def get_deviation(stock_code):
    try:
        query = """
        WITH ranked_prices AS (
            SELECT 
                stock_code,
                stock_name,
                close_price,
                trade_date,
                ROW_NUMBER() OVER (ORDER BY trade_date DESC) as rn
            FROM daily_data 
            WHERE stock_code = %(stock_code)s
            ORDER BY trade_date DESC
            LIMIT 31
        )
        SELECT 
            a.stock_code,
            a.stock_name,
            a.close_price as current_price,
            b.close_price as price_10_days,
            c.close_price as price_30_days,
            ROUND(((a.close_price - b.close_price) / b.close_price * 100), 2) as change_10_days,
            ROUND(((a.close_price - c.close_price) / c.close_price * 100), 2) as change_30_days
        FROM ranked_prices a
        LEFT JOIN ranked_prices b ON b.rn = 11  # 10天前的价格
        LEFT JOIN ranked_prices c ON c.rn = 31  # 30天前的价格
        WHERE a.rn = 1  # 最新价格
        """
        
        engine = get_db_connection()
        df = pd.read_sql(query, engine, params={'stock_code': stock_code})
        
        if df.empty:
            return jsonify({'code': 1, 'msg': '未找到股票数据'})
            
        result = df.to_dict('records')[0]
        return jsonify({'code': 0, 'data': result})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'code': 1, 'msg': str(e)})

@app.route('/api/latest_trade_date')
def get_latest_trade_date():
    """获取最新交易日期"""
    try:
        engine = get_db_connection()
        query = "SELECT MAX(trade_date) as latest_date FROM daily_data"
        df = pd.read_sql(query, engine)
        latest_date = df.iloc[0]['latest_date'].strftime('%Y-%m-%d')
        return jsonify({'code': 0, 'latest_date': latest_date})
    except Exception as e:
        logger.error(f"获取最新交易日期失败: {str(e)}")
        return jsonify({'code': 1, 'msg': '获取最新交易日期失败'})

if __name__ == '__main__':
    app.run(debug=True, port=5002) 