from flask import Flask, render_template, request
from fupan import get_market_analysis, format_change_rate, process_concept_stocks  # 直接导入
from datetime import datetime, timedelta
import tushare as ts

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