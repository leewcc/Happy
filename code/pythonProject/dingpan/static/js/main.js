$(document).ready(function() {
    console.log('页面初始化开始');
    
    // 日期选择和实时数据控制
    const realtimeCheckbox = $('#realtime-data');
    const datePicker = $('#date-picker');
    const queryBtn = $('#query-btn');
    
    // 设置日期选择器的最大值为今天
    const today = new Date();
    const dateStr = today.toISOString().split('T')[0];
    datePicker.attr('max', dateStr);
    datePicker.val(dateStr);
    
    // 监听实时数据复选框变化
    realtimeCheckbox.change(function() {
        console.log('实时数据复选框状态改变:', this.checked);
        
        if (this.checked) {
            datePicker.prop('disabled', true);
            queryBtn.prop('disabled', true);
            // 恢复实时数据更新
            startRealTimeUpdate();
            console.log('启用实时数据更新');
        } else {
            datePicker.prop('disabled', false);
            queryBtn.prop('disabled', false);
            // 停止实时数据更新
            stopRealTimeUpdate();
            console.log('禁用实时数据更新');
        }
    });
    
    // 监听查询按钮点击
    queryBtn.click(function() {
        if (!realtimeCheckbox.prop('checked')) {
            const selectedDate = datePicker.val();
            loadHistoricalData(selectedDate);
        }
    });
    
    // 监听日期选择器回车事件
    datePicker.keypress(function(e) {
        if (e.which == 13 && !realtimeCheckbox.prop('checked')) {
            const selectedDate = $(this).val();
            loadHistoricalData(selectedDate);
        }
    });
    
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

    // 初始化时启动实时更新
    startRealTimeUpdate();

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
function loadData(tab, date = null) {
    if (date) {
        loadHistoricalData(date);
        return;
    }
    
    console.log('loadData被调用，tab:', tab);
    switch(tab) {
        case 'rank':
            console.log('加载涨跌排行数据');
            loadMarketOverview();
            loadStockList();
            break;
        case 'limit':
            console.log('加载涨停分析数据');
            if(typeof updateLimitAnalysis === 'function') {
                updateLimitAnalysis();
            } else {
                console.error('updateLimitAnalysis function not found');
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
    // 获取当前的排序状态
    const sortColumn = $('.sortable.asc, .sortable.desc').data('sort');
    const order = $('.sortable.asc').length > 0 ? 'asc' : 'desc';
    
    // 构建查询参数
    const params = {};
    if (sortColumn) {
        params.sort_by = sortColumn;
        params.order = order;
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

// 处理表格排序
$(document).on('click', '.sortable', function() {
    const sortBy = $(this).data('sort');
    const currentOrder = $(this).hasClass('asc') ? 'desc' : 'asc';
    
    // 更新排序状态
    $('.sortable').removeClass('asc desc');
    $(this).addClass(currentOrder);
    
    // 获取当前日期
    const selectedDate = $('#date-picker').val();
    const isRealtime = $('#realtime-data').prop('checked');
    
    // 根据是否是实时数据决定使用哪个API
    if (isRealtime) {
        // 实时数据排序
        $.get(`/api/stock_list?sort_by=${sortBy}&order=${currentOrder}`, function(data) {
            updateStockList(data);
        });
    } else {
        // 历史数据排序，保持日期参数
        const formattedDate = selectedDate.replace(/-/g, '');
        $.get(`/api/stock_list/${formattedDate}?sort_by=${sortBy}&order=${currentOrder}`, function(data) {
            updateStockList(data);
        });
    }
});

// 更新股票列表显示
function updateStockList(data) {
    // 获取当前的排序状态
    const currentSortColumn = $('.sortable.asc, .sortable.desc').data('sort');
    const isAscending = $('.sortable.asc').length > 0;
    
    // 构建表头
    const tableHeader = `
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
    `;
    
    let html = tableHeader + '<tbody>';
    
    data.forEach(stock => {
        const changePctClass = stock.change_pct >= 0 ? 'up-color' : 'down-color';
        const amount = stock.amount ? (stock.amount/100000000).toFixed(2) : '0.00';
        const bidAmount = stock.bid_amount ? (stock.bid_amount/100000000).toFixed(2) : '0.00';
        const nonBidAmount = stock.non_bid_amount ? (stock.non_bid_amount/100000000).toFixed(2) : '0.00';
        
        // 处理概念标签的展示，使用rank-前缀的类名
        const concepts = stock.concepts ? stock.concepts.split(',').map(concept => 
            `<span class="rank-concept-tag">${concept.trim()}</span>`
        ).join('') : '-';
        
        html += `
            <tr data-ts-code="${stock.ts_code}">
                <td>${stock.name || '-'}</td>
                <td class="${changePctClass}">${(stock.change_pct || 0).toFixed(2)}%</td>
                <td>${amount}</td>
                <td>${bidAmount}</td>
                <td>${nonBidAmount}</td>
                <td>${stock.industry || '-'}</td>
                <td class="rank-concept-cell">${concepts}</td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    $('#stock-table').html(html);
    
    // 添加表格行点击事件
    $('#stock-table tbody tr').click(function() {
        const tsCode = $(this).data('ts-code');
        const name = $(this).find('td:first').text();
        window.klineChart.show(tsCode, name);
    });
}

// 添加涨跌排行特定的CSS样式
const rankStyle = document.createElement('style');
rankStyle.textContent = `
    .rank-concept-cell {
        max-width: 600px;
        overflow-wrap: break-word;
        word-wrap: break-word;
        word-break: break-all;
        white-space: normal;
        line-height: 1.5;
    }
    
    .rank-concept-tag {
        display: inline-block;
        padding: 2px 6px;
        margin: 2px;
        background: #f0f0f0;
        border-radius: 4px;
        font-size: 12px;
        white-space: normal;
    }
    
    #stock-table td {
        vertical-align: middle;
        padding: 8px;
    }
`;
document.head.appendChild(rankStyle);

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
    console.log('开始更新涨跌分布图，数据:', stats);
    
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

    // 确保 stocks 是数组且 change_pct 是数字
    const stocks = Array.isArray(stats.stocks) ? stats.stocks : [];
    console.log('处理的股票数量:', stocks.length);

    // 计算每个区间的股票数量
    const data = ranges.map(range => {
        const count = stocks.filter(stock => {
            const pct = parseFloat(stock.change_pct);
            return !isNaN(pct) && pct >= range.min && pct < range.max;
        }).length;
        
        console.log(`区间 ${range.label}: ${count}只`);
        
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
            bottom: '15%',
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
    
    console.log('设置图表选项:', option);
    distChart.setOption(option);
}

// 停止实时更新
function stopRealTimeUpdate() {
    console.log('尝试停止实时更新');
    console.log('当前定时器ID:', window.dataRefreshInterval);
    
    if (window.dataRefreshInterval) {
        clearInterval(window.dataRefreshInterval);
        window.dataRefreshInterval = null;
        console.log('已停止实时更新');
    } else {
        console.log('没有找到活动的定时器');
    }
}

// 开始实时更新
function startRealTimeUpdate() {
    console.log('尝试启动实时更新');
    
    stopRealTimeUpdate();
    
    const activeTab = $('.nav-link.active').data('tab');
    loadData(activeTab);
    
    window.dataRefreshInterval = setInterval(function() {
        const activeTab = $('.nav-link.active').data('tab');
        console.log('定时刷新当前页面:', activeTab);
        
        if (activeTab === 'limit' && typeof updateLimitAnalysis === 'function') {
            updateLimitAnalysis(null, true);  // null 和 true 表示实时数据
        } else {
            loadData(activeTab);
        }
    }, 10000);
    
    console.log('已启动实时更新，定时器ID:', window.dataRefreshInterval);
}

// 加载历史数据
function loadHistoricalData(date) {
    const activeTab = $('.nav-link.active').data('tab');
    const formattedDate = date.replace(/-/g, '');  // 转换日期格式 YYYY-MM-DD 到 YYYYMMDD
    
    switch(activeTab) {
        case 'rank':
            $.get(`/api/market_overview/${formattedDate}`, function(data) {
                if (data.indices) {
                    updateIndexOverview(data.indices);
                }
                if (data.statistics) {
                    updateMarketStats(data.statistics);
                    updateDistributionChart(data.statistics);
                }
                if (data.amount_trend) {
                    updateAmountTrend(data.amount_trend);
                }
            });
            
            $.get(`/api/stock_list/${formattedDate}`, function(data) {
                updateStockList(data);
            });
            break;
            
        case 'limit':
            if (typeof updateLimitAnalysis === 'function') {
                updateLimitAnalysis(formattedDate, false);  // false 表示非实时数据
            } else {
                console.error('updateLimitAnalysis function not found');
            }
            break;
            
        case 'sector':
            loadSectorMap(formattedDate);
            break;
            
        default:
            console.warn('未知的页面类型:', activeTab);
    }
} 