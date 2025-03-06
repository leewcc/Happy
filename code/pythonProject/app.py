from flask import Flask, render_template, request, jsonify, flash, get_flashed_messages, redirect, url_for
from loaddata.daily.load_limit_daily import get_limit_stocks_page, save_core_concepts, get_limit_stocks_with_concepts
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import pymysql

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 添加这一行用于flash消息

# Tushare配置
ts.set_token('i593c24d0926bfb845f136082a335d64f71')
pro = ts.pro_api()

@app.route('/')
def index():
    """主页面，包含导航"""
    return render_template('index.html')

@app.route('/limit_stocks', methods=['GET', 'POST'])
def limit_stocks_page():
    # 获取查询日期参数，如果没有则使用今天的日期
    today = datetime.now()
    while today.weekday() > 4:  # 5是周六，6是周日
        today = today - timedelta(days=1)
        
    default_date = today.strftime('%Y%m%d')
    query_date = request.args.get('date', default_date)
    
    # 转换日期格式用于显示
    try:
        display_date = f"{query_date[:4]}-{query_date[4:6]}-{query_date[6:]}"
    except:
        display_date = today.strftime('%Y-%m-%d')
        query_date = default_date
    
    print(f"\n==== 处理涨跌停页面请求 ====")
    print(f"查询日期: {query_date}")
    
    # 处理表单提交
    if request.method == 'POST':
        try:
            print("\n==== 开始处理表单提交 ====")
            
            # 从表单中提取数据
            concepts_data = []
            
            # 首先获取所有的股票代码
            stock_codes = set()
            for key in request.form:
                if key.startswith('core_concept_'):
                    ts_code = key.split('_')[-1]
                    stock_codes.add(ts_code)
            
            # 对每个股票代码处理其核心概念
            for ts_code in stock_codes:
                concepts = []
                stock_name = request.form.get(f'name_{ts_code}', '')
                
                for i in range(1, 4):
                    concept_key = f'core_concept{i}_{ts_code}'
                    concept_value = request.form.get(concept_key, '').strip()
                    if concept_value:
                        concepts.append(concept_value)
                
                concepts_str = ','.join(concepts) if concepts else ''
                concepts_data.append({
                    'ts_code': ts_code,
                    'name': stock_name,
                    'core_concepts': concepts_str
                })
            
            # 保存核心概念
            if concepts_data:
                save_core_concepts(concepts_data, query_date)
                flash('核心概念保存成功！', 'success')
            
            # 重要：在这里直接重定向，而不是继续执行
            print("触发重定向")
            return redirect(url_for('limit_stocks_page', date=query_date))
            
        except Exception as e:
            print(f"保存核心概念失败: {str(e)}")
            flash(f'保存核心概念失败：{str(e)}', 'error')
            return redirect(url_for('limit_stocks_page', date=query_date))
    
    # 获取最新数据
    print("\n获取最新涨跌停数据")
    stocks = get_limit_stocks_page(query_date)
    print(f"获取到 {len(stocks)} 条最新股票数据")
    
    # 构建一个简单的表格HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>涨跌停股票</title>
        <style>
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .form-control {{ width: 100%; padding: 5px; }}
            .flash-message {{ 
                padding: 10px; 
                margin: 10px 0; 
                border-radius: 4px; 
            }}
            .flash-success {{ background-color: #d4edda; color: #155724; }}
            .flash-warning {{ background-color: #fff3cd; color: #856404; }}
            .flash-error {{ background-color: #f8d7da; color: #721c24; }}
        </style>
    </head>
    <body>
        <h1>涨跌停股票 ({date})</h1>
        
        <!-- 日期选择器 -->
        <div style="margin: 20px 0;">
            <form id="dateForm" style="display: flex; gap: 10px; align-items: center;">
                <input type="date" id="tradeDate" name="tradeDate" 
                       value="{today}" 
                       style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                <button type="submit" style="padding: 8px 16px;">查询</button>
            </form>
        </div>
        
        <!-- Flash消息 -->
        {flash_messages}
        
        <form method="post" action="/limit_stocks?date={raw_date}">
            <table>
                <thead>
                    <tr>
                        <th>股票名称</th>
                        <th>首次涨停时间</th>
                        <th>连板</th>
                        <th>行业</th>
                        <th>涨停原因</th>
                        <th>概念</th>
                        <th>核心概念1</th>
                        <th>核心概念2</th>
                        <th>核心概念3</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
            <div style="text-align: center; margin-top: 20px;">
                <button type="submit" style="padding: 10px 20px;">保存核心概念</button>
            </div>
        </form>
        
        <script>
            document.getElementById('dateForm').onsubmit = function(e) {{
                e.preventDefault();
                const date = document.getElementById('tradeDate').value;
                const formattedDate = date.replace(/-/g, '');
                window.location.href = `/limit_stocks?date=${{formattedDate}}`;
            }};
            
            document.addEventListener('DOMContentLoaded', function() {{
                const today = '{today}';
                document.getElementById('tradeDate').value = today;
            }});
        </script>
    </body>
    </html>
    """
    
    # 生成表格行
    rows = ""
    for stock in stocks:
        rows += f"""
        <tr>
            <td>
                {stock['name']}
                <input type="hidden" name="name_{stock['ts_code']}" value="{stock['name']}">
                <input type="hidden" name="core_concept_{stock['ts_code']}" value="1">
            </td>
            <td>{stock.get('first_time', '')}</td>
            <td>{stock.get('lbd_num', '')}</td>
            <td>{stock.get('industry', '')}</td>
            <td>{stock.get('reason', '')}</td>
            <td>{stock.get('concepts', '')}</td>
            <td><input type="text" class="form-control" name="core_concept1_{stock['ts_code']}" 
                   value="{stock.get('core_concept1', '')}" placeholder="核心概念1"></td>
            <td><input type="text" class="form-control" name="core_concept2_{stock['ts_code']}" 
                   value="{stock.get('core_concept2', '')}" placeholder="核心概念2"></td>
            <td><input type="text" class="form-control" name="core_concept3_{stock['ts_code']}" 
                   value="{stock.get('core_concept3', '')}" placeholder="核心概念3"></td>
        </tr>
        """
    
    # 生成Flash消息HTML
    flash_messages = ""
    with app.test_request_context():
        messages = get_flashed_messages(with_categories=True)
        for category, message in messages:
            flash_messages += f'<div class="flash-message flash-{category}">{message}</div>'
    
    # 填充HTML模板
    formatted_html = html.format(
        date=display_date,
        raw_date=query_date,
        rows=rows,
        flash_messages=flash_messages,
        today=display_date
    )
    
    return formatted_html


@app.route('/save_concepts', methods=['POST'])
def save_concepts():
    """保存核心概念"""
    data = request.json
    try:
        save_core_concepts(data['concepts'])
        return jsonify({"success": True, "message": "核心概念保存成功!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"保存失败: {str(e)}"})

def get_fupan_data():
    """获取复盘数据"""
    today = datetime.now()
    
    # 如果是周末，获取最近的工作日
    while today.weekday() > 4:  # 5是周六，6是周日
        today = today - timedelta(days=1)
    
    trade_date = today.strftime('%Y%m%d')
    
    try:
        # 获取指数数据
        df = pro.index_daily(ts_code='000001.SH,399001.SZ,399006.SZ', 
                           trade_date=trade_date,
                           fields='ts_code,trade_date,open,high,low,close,pct_chg,vol,amount')
        
        # 获取涨跌停数据
        limit_list = pro.limit_list(trade_date=trade_date, 
                                  fields='ts_code,trade_date,name,close,pct_chg,limit')
                                  
        # 计算涨跌停数量分布
        ranges = [-20, -10, -7, -5, -3, 0, 3, 5, 7, 10, 20]
        counts = []
        for i in range(len(ranges)-1):
            count = len(limit_list[(limit_list['pct_chg'] >= ranges[i]) & 
                                 (limit_list['pct_chg'] < ranges[i+1])])
            counts.append(count)
        
        data = {
            'indices': df.to_dict('records'),
            'range_distribution': {
                'ranges': ranges,
                'counts': counts
            }
        }
        
        return data
        
    except Exception as e:
        print(f"获取数据失败: {str(e)}")
        return None

@app.route('/fupan')
def fupan_page():
    """复盘页面"""
    data = get_fupan_data()
    return render_template('market.html', data=data)

@app.route('/test_concepts')
def test_concepts_page():
    """测试核心概念数据显示"""
    query_date = request.args.get('date', '20250303')
    
    # 获取数据
    stocks = get_limit_stocks_page(query_date)
    
    # 直接打印传递给模板的数据
    print("\n==== 测试路由 - 传递给模板的数据 ====")
    for i, stock in enumerate(stocks[:5]):  # 只打印前5条
        print(f"股票 {i+1}: {stock['name']} ({stock['ts_code']})")
        print(f"  核心概念1: '{stock['core_concept1']}'")
        print(f"  核心概念2: '{stock['core_concept2']}'")
        print(f"  核心概念3: '{stock['core_concept3']}'")
    
    # 返回一个非常简单的HTML页面 - 使用双花括号来转义CSS中的花括号
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>核心概念测试</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .stock {{ margin-bottom: 10px; padding: 10px; border: 1px solid #ccc; }}
            .debug {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>核心概念测试页面</h1>
        <p>日期: {date}</p>
        <p>股票数量: {count}</p>
        
        <div class="debug">
            <h2>调试信息</h2>
            {debug_info}
        </div>
        
        <h2>股票列表</h2>
        {stocks_html}
    </body>
    </html>
    """
    
    # 生成股票HTML
    stocks_html = ""
    debug_info = ""
    
    for i, stock in enumerate(stocks[:20]):  # 只显示前20条
        stocks_html += f"""
        <div class="stock">
            <h3>{stock['name']} ({stock['ts_code']})</h3>
            <p>行业: {stock['industry']}</p>
            <p>概念: {stock['concepts']}</p>
            <p>核心概念1: <input type="text" value="{stock['core_concept1']}" readonly> <span class="debug">({stock['core_concept1']})</span></p>
            <p>核心概念2: <input type="text" value="{stock['core_concept2']}" readonly> <span class="debug">({stock['core_concept2']})</span></p>
            <p>核心概念3: <input type="text" value="{stock['core_concept3']}" readonly> <span class="debug">({stock['core_concept3']})</span></p>
        </div>
        """
        
        # 添加到调试信息
        if i < 5:
            debug_info += f"<p>股票 {i+1}: {stock['name']} ({stock['ts_code']})<br>"
            debug_info += f"核心概念1: '{stock['core_concept1']}' (长度: {len(stock['core_concept1'])})<br>"
            debug_info += f"核心概念2: '{stock['core_concept2']}' (长度: {len(stock['core_concept2'])})<br>"
            debug_info += f"核心概念3: '{stock['core_concept3']}' (长度: {len(stock['core_concept3'])})</p>"
    
    # 填充HTML模板
    formatted_html = html.format(
        date=query_date,
        count=len(stocks),
        debug_info=debug_info,
        stocks_html=stocks_html
    )
    
    return formatted_html

if __name__ == '__main__':
    app.run(debug=True, port=5001) 