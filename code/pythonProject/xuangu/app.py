from flask import Flask, render_template, jsonify, request
from xuangu_logic import get_stock_list, filter_stocks, get_industries, get_concepts

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

if __name__ == '__main__':
    app.run(debug=True, port=5002) 