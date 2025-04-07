$(document).ready(function() {
    // 页面切换
    $('.nav-link').click(function(e) {
        e.preventDefault();
        $('.nav-link').removeClass('active');
        $(this).addClass('active');
        
        const tab = $(this).data('tab');
        $('.page-content').hide();
        $(`#${tab}-page`).show();
        
        // 重新加载数据
        loadData(tab);
    });

    // 定时刷新数据
    setInterval(function() {
        const activeTab = $('.nav-link.active').data('tab');
        loadData(activeTab);
    }, 60000);  // 每分钟刷新一次

    // 初始加载
    loadData('rank');
});

function loadData(tab) {
    switch(tab) {
        case 'rank':
            loadMarketOverview();
            loadStockList();
            break;
        case 'limit':
            loadLimitUpAnalysis();
            break;
        case 'sector':
            loadSectorMap();
            break;
    }
}

function loadMarketOverview() {
    $.get('/api/market_overview', function(data) {
        updateIndexOverview(data.indices);
        updateMarketStats(data.statistics);
        updateAmountTrend(data.amount_trend);
        updateDistributionChart(data.statistics);
    });
}

function loadStockList() {
    // 构建查询参数
    const params = {};
    if (currentSortColumn) {
        params.sort_by = currentSortColumn;
        params.order = isAscending ? 'asc' : 'desc';
    }
    
    // 添加参数到URL
    const queryString = new URLSearchParams(params).toString();
    const url = `/api/stock_list${queryString ? '?' + queryString : ''}`;
    
    $.get(url, function(data) {
        updateStockList(data);
    }).fail(function(error) {
        console.error('Failed to load stock list:', error);
    });
}

function loadLimitUpAnalysis() {
    $.get('/api/limit_up_analysis', function(data) {
        updateLimitStats(data.statistics);
        updateIndustryDistribution(data.industry_distribution);
    });
}

// 更新指数行情
function updateIndexOverview(indices) {
    indices.forEach(index => {
        // 根据完整的指数代码进行匹配
        const id = index.ts_code === '000001.SH' ? 'sh' :
                  index.ts_code === '399001.SZ' ? 'sz' :
                  index.ts_code === '399006.SZ' ? 'cyb' :
                  index.ts_code === '000688.SH' ? 'kc' :
                  index.ts_code === '899050.BJ' ? 'bj' : null;
        
        if (id) {
            const price = parseFloat(index.price).toFixed(2);
            const changePct = parseFloat(index.change_pct).toFixed(2);
            const colorClass = index.change >= 0 ? 'up-color' : 'down-color';
            
            const container = $(`#${id}-index`);
            container.find('.index-price').text(price).addClass(colorClass);
            container.find('.index-change')
                    .text(`${changePct}%`)  // 只显示涨跌幅
                    .addClass(colorClass);

            // 移除旧的颜色类
            container.find('.index-price, .index-change')
                    .removeClass('up-color down-color')
                    .addClass(colorClass);
        }
    });
}

// 更新市场统计
function updateMarketStats(stats) {
    $('#up-count').text(stats.up_count);
    $('#down-count').text(stats.down_count);
    $('#total-amount').text((stats.total_amount / 100000000).toFixed(0) + '亿');
}

// 添加K线图相关函数
let klineChart = null;

function initKlineChart() {
    if (!klineChart) {
        klineChart = echarts.init(document.getElementById('kline-chart'));
    }
}

function showKline(ts_code) {
    $.get(`/api/stock_kline/${ts_code}`, function(data) {
        const dates = data.map(item => item.trade_date);
        const values = data.map(item => [item.open, item.close, item.low, item.high]);
        const volumes = data.map(item => item.volume);
        
        const option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            legend: {
                data: ['K线', '成交量']
            },
            grid: [{
                left: '10%',
                right: '10%',
                height: '60%'
            }, {
                left: '10%',
                right: '10%',
                top: '75%',
                height: '20%'
            }],
            xAxis: [{
                type: 'category',
                data: dates,
                scale: true
            }, {
                type: 'category',
                gridIndex: 1,
                data: dates,
                scale: true
            }],
            yAxis: [{
                scale: true,
                splitArea: {
                    show: true
                }
            }, {
                scale: true,
                gridIndex: 1
            }],
            dataZoom: [{
                type: 'inside',
                xAxisIndex: [0, 1],
                start: 0,
                end: 100
            }, {
                show: true,
                xAxisIndex: [0, 1],
                type: 'slider',
                bottom: '0%',
                start: 0,
                end: 100
            }],
            series: [{
                name: 'K线',
                type: 'candlestick',
                data: values
            }, {
                name: '成交量',
                type: 'bar',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: volumes
            }]
        };
        
        klineChart.setOption(option);
    });
}

// 添加排序相关变量
let currentSortColumn = null;
let isAscending = true;

function updateStockList(stocks) {
    if (!stocks || !stocks.length) {
        console.log('No stock data received');
        return;
    }

    let html = `
        <table class="table table-hover">
            <thead>
                <tr>
                    <th>股票名称</th>
                    <th class="sortable ${currentSortColumn === 'change_pct' ? (isAscending ? 'asc' : 'desc') : ''}" 
                        data-sort="change_pct">涨幅</th>
                    <th class="sortable ${currentSortColumn === 'amount' ? (isAscending ? 'asc' : 'desc') : ''}" 
                        data-sort="amount">成交额(亿)</th>
                    <th class="sortable ${currentSortColumn === 'bid_amount' ? (isAscending ? 'asc' : 'desc') : ''}" 
                        data-sort="bid_amount">竞价金额(亿)</th>
                    <th class="sortable ${currentSortColumn === 'non_bid_amount' ? (isAscending ? 'asc' : 'desc') : ''}" 
                        data-sort="non_bid_amount">早盘未竞价(亿)</th>
                    <th>所属行业</th>
                    <th>概念</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    stocks.forEach(stock => {
        const changePctClass = stock.change_pct >= 0 ? 'up-color' : 'down-color';
        const amount = stock.amount ? (stock.amount/100000000).toFixed(2) : '0.00';
        const bidAmount = stock.bid_amount ? (stock.bid_amount/100000000).toFixed(2) : '0.00';
        const nonBidAmount = stock.non_bid_amount ? (stock.non_bid_amount/100000000).toFixed(2) : '0.00';
        
        html += `
            <tr data-ts-code="${stock.ts_code}">
                <td>${stock.name || '-'}</td>
                <td class="${changePctClass}">${(stock.change_pct || 0).toFixed(2)}%</td>
                <td>${amount}</td>
                <td>${bidAmount}</td>
                <td>${nonBidAmount}</td>
                <td>${stock.industry || '-'}</td>
                <td>${stock.concepts || '-'}</td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    $('#stock-table').html(html);
    
    // 添加排序列的点击事件
    $('.sortable').click(function() {
        const column = $(this).data('sort');
        
        // 如果点击的是当前排序列，则反转排序方向
        if (column === currentSortColumn) {
            isAscending = !isAscending;
        } else {
            currentSortColumn = column;
            isAscending = false;  // 新列默认降序
        }
        
        // 重新加载数据
        loadStockList();
    });
}

// 更新成交额趋势图
function updateAmountTrend(data) {
    const amountChart = echarts.init(document.getElementById('amount-trend'));
    
    const option = {
        title: {
            text: '成交额趋势',
            textStyle: {
                fontSize: 13
            }
        },
        grid: {
            top: 30,
            right: 10,
            bottom: 20,
            left: 40
        },
        tooltip: {
            trigger: 'axis',
            formatter: params => {
                const value = (params[0].value / 100000000).toFixed(0);
                return `${params[0].name}<br/>成交额: ${value}亿`;
            }
        },
        xAxis: {
            type: 'category',
            data: data.map(item => item.trade_date),
            axisLabel: {
                interval: 'auto',
                fontSize: 11
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                formatter: value => (value / 100000000).toFixed(0),
                fontSize: 11
            }
        },
        series: [{
            data: data.map(item => item.total_amount),
            type: 'line',
            smooth: true,
            symbol: 'none'
        }]
    };
    
    amountChart.setOption(option);
}

// 更新涨跌分布图
function updateDistributionChart(stats) {
    const distChart = echarts.init(document.getElementById('distribution-chart'));
    
    // 构建涨跌分布数据
    const ranges = [
        {min: 11, max: Infinity, label: '>11%'},
        {min: 7, max: 11, label: '7~11%'},
        {min: 3, max: 7, label: '3~7%'},
        {min: 0, max: 3, label: '0~3%'},
        {min: -3, max: 0, label: '-3~0%'},
        {min: -7, max: -3, label: '-7~-3%'},
        {min: -11, max: -7, label: '-11~-7%'},
        {min: -Infinity, max: -11, label: '<-11%'}
    ];

    // 计算每个区间的股票数量
    const data = ranges.map(range => {
        const count = stats.stocks.filter(stock => 
            stock.change_pct >= range.min && stock.change_pct < range.max
        ).length;
        return {
            value: count,
            itemStyle: {
                color: range.min >= 0 ? '#f55' : '#0c0'
            }
        };
    });

    const option = {
        title: {
            text: '涨跌分布',
            textStyle: {
                fontSize: 14
            }
        },
        tooltip: {
            trigger: 'axis',
            axisPointer: {
                type: 'shadow'
            },
            formatter: '{b}: {c}只'
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '15%',  // 增加底部空间，防止标签显示不全
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: ranges.map(r => r.label),
            axisLabel: {
                interval: 0,
                fontSize: 11,
                rotate: 45
            }
        },
        yAxis: {
            type: 'value',
            axisLabel: {
                fontSize: 11
            }
        },
        series: [{
            type: 'bar',
            data: data,
            barWidth: '60%',
            label: {
                show: true,
                position: 'top',
                fontSize: 11
            }
        }]
    };
    
    distChart.setOption(option);
} 