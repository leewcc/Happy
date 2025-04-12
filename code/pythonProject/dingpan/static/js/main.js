$(document).ready(function() {
    console.log('页面初始化开始');
    
    // 从 localStorage 获取上次访问的页面
    const lastTab = localStorage.getItem('currentTab') || 'rank';
    console.log('上次访问的页面:', lastTab);
    
    // 激活对应的导航项
    $(`.nav-link[data-tab="${lastTab}"]`).addClass('active');
    console.log('当前激活的导航项:', $(`.nav-link[data-tab="${lastTab}"]`).length);
    
    // 显示对应的页面内容
    $('.page-content').hide();
    $(`#${lastTab}-page`).show();
    console.log('显示的页面元素:', $(`#${lastTab}-page`).length);
    
    // 初始加载数据
    loadData(lastTab);
    console.log('初始加载页面:', lastTab);
    
    // 检查导航链接是否存在
    console.log('找到的导航链接数量:', $('.nav-link').length);
    
    // 使用事件委托绑定点击事件
    $(document).on('click', '.nav-link', function(e) {
        console.log('导航链接被点击 - 事件委托');
        e.preventDefault();
        const tab = $(this).data('tab');
        console.log('点击的链接:', $(this).text());
        console.log('tab值:', tab);
        
        // 保存当前页面到 localStorage
        localStorage.setItem('currentTab', tab);
        
        // 更新导航项状态
        $('.nav-link').removeClass('active');
        $(this).addClass('active');
        
        // 切换页面内容
        $('.page-content').hide();
        $(`#${tab}-page`).show();
        console.log('切换后显示的页面元素:', $(`#${tab}-page`).length);
        
        // 加载对应页面的数据
        loadData(tab);
        console.log('加载新页面:', tab);
    });

    // 直接绑定点击事件作为备选
    $('.nav-link').click(function(e) {
        console.log('导航链接被点击 - 直接绑定');
    });

    // 添加鼠标移入事件检查元素是否存在
    $('.nav-link').hover(function() {
        console.log('鼠标移入导航链接:', $(this).text());
        console.log('该元素的data-tab值:', $(this).data('tab'));
    });

    // 检查页面结构
    console.log('页面内容元素:');
    $('.page-content').each(function() {
        console.log('- ID:', $(this).attr('id'));
        console.log('- 显示状态:', $(this).css('display'));
    });

    // 检查导航栏结构
    console.log('导航栏结构:');
    $('.navbar-nav').each(function() {
        console.log('导航栏项目数量:', $(this).find('.nav-item').length);
        $(this).find('.nav-link').each(function() {
            console.log('- 链接文本:', $(this).text());
            console.log('- data-tab:', $(this).data('tab'));
            console.log('- href:', $(this).attr('href'));
        });
    });

    // 定时刷新数据
    setInterval(function() {
        const activeTab = $('.nav-link.active').data('tab');
        console.log('定时刷新当前页面:', activeTab);
        loadData(activeTab);
    }, 10000);  // 每分钟刷新一次

    console.log('页面初始化完成');
});

// 检查页面元素
function checkPageElements() {
    console.log('导航链接数量:', $('.nav-link').length);
    $('.nav-link').each(function() {
        console.log('导航链接:', $(this).text(), '数据标签:', $(this).data('tab'));
    });
    
    console.log('页面内容数量:', $('.page-content').length);
    $('.page-content').each(function() {
        console.log('页面内容ID:', $(this).attr('id'));
    });
}

// 在页面加载完成后检查元素
$(document).ready(function() {
    console.log('开始检查页面元素');
    checkPageElements();
});

// 加载页面数据
function loadData(tab) {
    console.log('loadData被调用，tab:', tab);
    switch(tab) {
        case 'rank':
            console.log('加载涨跌排行数据');
            loadMarketOverview();
            loadStockList();
            break;
        case 'limit':
            console.log('加载涨停分析数据');
            if(typeof initLimitAnalysis === 'function') {
                initLimitAnalysis();
            } else {
                console.error('initLimitAnalysis function not found');
            }
            break;
        case 'sector':
            console.log('加载板块地图数据');
            loadSectorMap();
            break;
        default:
            console.warn('未知的页面类型:', tab);
    }
}

function loadMarketOverview() {
    // console.log('开始加载市场概览数据');
    $.get('/api/market_overview', function(data) {
        // console.log('收到市场概览数据:', data);
        if (data.indices) {
            console.log('指数数据:', data.indices);
            updateIndexOverview(data.indices);
        } else {
            console.warn('未收到指数数据');
        }
        
        if (data.statistics) {
            // console.log('市场统计数据:', data.statistics);
            updateMarketStats(data.statistics);
        }
        
        if (data.amount_trend) {
            // console.log('成交额趋势数据:', data.amount_trend);
            updateAmountTrend(data.amount_trend);
        }
        
        if (data.statistics) {
            updateDistributionChart(data.statistics);
        }
    }).fail(function(error) {
        console.error('加载市场概览数据失败:', error);
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
    console.log('开始更新指数行情');
    indices.forEach(index => {
        // 根据完整的指数代码进行匹配
        const id = index.ts_code === '000001.SH' ? 'sh' :
                  index.ts_code === '399001.SZ' ? 'sz' :
                  index.ts_code === '399006.SZ' ? 'cyb' :
                  index.ts_code === '000688.SH' ? 'kc' :
                  index.ts_code === '899050.BJ' ? 'bj' : null;
        
        console.log('处理指数:', index.ts_code, '映射ID:', id);
        
        if (id) {
            const price = parseFloat(index.price).toFixed(2);
            const changePct = parseFloat(index.change_pct).toFixed(2);
            const colorClass = index.change >= 0 ? 'up-color' : 'down-color';
            
            console.log(`更新${id}指数:`, {
                price: price,
                changePct: changePct,
                colorClass: colorClass
            });
            
            const container = $(`#${id}-index`);
            if (container.length) {
                container.find('.index-price').text(price).addClass(colorClass);
                container.find('.index-change')
                        .text(`${changePct}%`)
                        .addClass(colorClass);

                // 移除旧的颜色类
                container.find('.index-price, .index-change')
                        .removeClass('up-color down-color')
                        .addClass(colorClass);
                        
                console.log(`${id}指数更新成功`);
            } else {
                console.warn(`未找到${id}指数容器元素`);
            }
        } else {
            console.warn('未知的指数代码:', index.ts_code);
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

    // 添加表格行点击事件
    $('#stock-table tbody tr').click(function() {
        const tsCode = $(this).data('ts-code');
        const name = $(this).find('td:first').text();
        window.klineChart.show(tsCode, name);
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