// 初始化涨停分析页面
function initLimitAnalysis() {
    // 创建涨停股票表格
    const limitStocksTable = new Tabulator("#limit-stocks-table", {
        height: "100%",  // 改为100%以充满容器
        layout: "fitColumns",
        footerElement: "<div class='tabulator-footer-records'>共 <span id='total-records'>0</span> 条记录</div>",
        dataFiltered: function(filters, rows) {
            console.log('过滤后的记录数:', rows.length);  // 添加调试日志
            document.getElementById('total-records').textContent = rows.length;
        },
        dataLoaded: function(data) {
            console.log('加载的数据条数:', data.length);  // 添加调试日志
            document.getElementById('total-records').textContent = data.length;
        },
        columns: [
            {title: "股票名称", field: "name", sorter: "string"},
            {title: "涨幅", field: "change_pct", sorter: "number", formatter: "number", formatterParams: {precision: 2}},
            {title: "连板数", field: "continuous_days", sorter: "number"},
            {title: "首次涨停", field: "first_limit_time", sorter: "string"},
            {title: "成交额(亿)", field: "amount", sorter: "number", formatter: "number", formatterParams: {precision: 2}},
            {title: "行业", field: "industry", sorter: "string"},
            {title: "概念", field: "concepts", sorter: "string", formatter: "textarea"}
        ]
    });

    // 创建概念统计表格
    const conceptStatsTable = new Tabulator("#concept-stats-table", {
        height: "auto",
        layout: "fitData",
        columns: [
            {
                title: "概念", 
                field: "concept", 
                sorter: "string", 
                width: 140,
                headerSort: true,
                headerSortStartingDir: "desc"
            },
            {
                title: "涨停", 
                field: "limit_up_count", 
                sorter: "number", 
                width: 65,
                hozAlign: "center",
                headerSort: true,
                headerSortStartingDir: "desc"
            },
            {
                title: "连板", 
                field: "continuous_count", 
                sorter: "number", 
                width: 65,
                hozAlign: "center",
                headerSort: true,
                headerSortStartingDir: "desc"
            },
            {
                title: "创业", 
                field: "gem_limit_up_count", 
                sorter: "number", 
                width: 65,
                hozAlign: "center",
                headerSort: true,
                headerSortStartingDir: "desc"
            },
            {
                title: "炸板", 
                field: "broken_count", 
                sorter: "number", 
                width: 65,
                hozAlign: "center",
                headerSort: true,
                headerSortStartingDir: "desc"
            },
            {
                title: "跌停", 
                field: "limit_down_count", 
                sorter: "number", 
                width: 65,
                hozAlign: "center",
                headerSort: true,
                headerSortStartingDir: "desc"
            }
        ],
        initialSort: [
            {column: "limit_up_count", dir: "desc"}
        ],
        rowHeight: 24,
        headerHeight: 24
    });

    // 处理侧边栏显示/隐藏
    function toggleConceptStats() {
        $('#concept-stats-sidebar').toggleClass('show');
    }

    // 按钮点击事件
    $('#toggle-concept-stats').click(toggleConceptStats);
    $('#close-concept-stats').click(toggleConceptStats);

    // 添加快捷键支持
    $(document).keydown(function(e) {
        // Alt + D
        if (e.altKey && e.keyCode === 68) {
            e.preventDefault(); // 阻止默认行为
            toggleConceptStats();
        }
    });

    // 处理概念统计显示切换
    $('#show-limit-up, #show-continuous, #show-broken, #show-limit-down').change(function() {
        const column = conceptStatsTable.getColumn($(this).attr('id').replace('show-', ''));
        column.toggle();
    });

    // 处理股票类型过滤
    function updateStockFilter() {
        const filters = [];
        if($('#filter-limit-up').prop('checked')) filters.push('limit_up');
        if($('#filter-broken').prop('checked')) filters.push('broken');
        if($('#filter-continuous').prop('checked')) filters.push('continuous');
        if($('#filter-limit-down').prop('checked')) filters.push('limit_down');
        
        // 更新表格过滤器
        limitStocksTable.setFilter(function(data) {
            // 如果没有选择任何过滤器，显示所有数据
            if (filters.length === 0) return true;
            
            return filters.some(type => {
                switch(type) {
                    case 'limit_up': return data.type === 'limit_up';
                    case 'broken': return data.type === 'broken';
                    case 'continuous': return data.continuous_days > 1;
                    case 'limit_down': return data.type === 'limit_down';
                }
            });
        });
    }

    // 初始化时设置默认过滤器
    function initStockFilter() {
        // 默认全部勾选
        $('#filter-limit-up').prop('checked', true);
        $('#filter-broken').prop('checked', true);
        $('#filter-continuous').prop('checked', true);
        $('#filter-limit-down').prop('checked', true);
        
        // 应用过滤器
        updateStockFilter();
    }

    // 绑定过滤器事件
    $('.stock-type-filter input').change(updateStockFilter);

    // 定时更新数据
    function updateLimitAnalysis() {
        $.get('/api/limit_up_analysis', function(data) {
            console.log('涨停分析数据:', data);  // 添加调试日志
            
            if(!data || data.error) {
                console.error('获取数据失败:', data.error);
                return;
            }

            // 更新统计数据
            updateLimitStats(data.statistics, data.last_trade_date_stats);

            // 更新表格数据
            if (data.limit_stocks && data.limit_stocks.length > 0) {
                console.log('更新表格数据，共', data.limit_stocks.length, '条记录');
                limitStocksTable.setData(data.limit_stocks).then(() => {
                    // 数据加载完成后更新记录数
                    const totalRows = limitStocksTable.getDataCount();
                    console.log('表格实际显示记录数:', totalRows);
                    document.getElementById('total-records').textContent = totalRows;
                });
            }
            
            conceptStatsTable.setData(data.concept_stats || []);
        }).fail(function(jqXHR, textStatus, errorThrown) {
            console.error('请求失败:', textStatus, errorThrown);
        });
    }

    // 首次加载数据
    updateLimitAnalysis();

    // 设置定时刷新
    setInterval(updateLimitAnalysis, 10000);

    // 在表格初始化后调用
    initStockFilter();
}

function updateLimitStats(currentStats, lastStats) {
    // 更新涨停统计
    $('#limit-up-count').text(currentStats.limit_up_count);
    $('#last-limit-up-count').text(`昨日: ${lastStats.limit_up_count}`);
    addChangeIndicator('limit-up-count', currentStats.limit_up_count, lastStats.limit_up_count);

    // 更新创业板涨停统计
    $('#gem-limit-up-count').text(currentStats.gem_limit_up_count);
    $('#last-gem-limit-up-count').text(`昨日: ${lastStats.gem_limit_up_count || 0}`);
    addChangeIndicator('gem-limit-up-count', currentStats.gem_limit_up_count, lastStats.gem_limit_up_count || 0);

    // 更新炸板统计
    $('#broken-limit-count').text(currentStats.broken_limit_count);
    $('#last-broken-count').text(`昨日: ${lastStats.broken_count}`);
    addChangeIndicator('broken-limit-count', currentStats.broken_limit_count, lastStats.broken_count);

    // 更新跌停统计
    $('#limit-down-count').text(currentStats.limit_down_count);
    $('#last-limit-down-count').text(`昨日: ${lastStats.limit_down_count}`);
    addChangeIndicator('limit-down-count', currentStats.limit_down_count, lastStats.limit_down_count);

    // 更新连板统计
    $('#continuous-limit-count').text(currentStats.continuous_limit_count);
    $('#last-consecutive-count').text(`昨日: ${lastStats.consecutive_count}`);
    addChangeIndicator('continuous-limit-count', currentStats.continuous_limit_count, lastStats.consecutive_count);
}

function addChangeIndicator(elementId, currentValue, lastValue) {
    const diff = currentValue - lastValue;
    const element = $(`#${elementId}`);
    
    // 移除旧的变化指示器
    element.siblings('.stat-change').remove();
    
    if (diff !== 0) {
        const changeHtml = `<div class="stat-change ${diff > 0 ? 'increase' : 'decrease'}">
            ${diff > 0 ? '↑' : '↓'} ${Math.abs(diff)}
        </div>`;
        element.after(changeHtml);
    }
}

// 显示概念详细信息
function showConceptDetail(conceptData) {
    const modal = new bootstrap.Modal(document.getElementById('concept-detail-modal'));
    
    // 更新弹窗标题
    document.querySelector('#concept-detail-modal .modal-title').textContent = 
        `${conceptData.concept} - 详细信息`;
    
    // 更新涨停股票列表
    const limitUpsHtml = conceptData.limit_ups.map(stock => 
        `<span class="stock-tag limit-up">${stock.name}</span>`
    ).join('');
    document.getElementById('concept-limit-ups').innerHTML = limitUpsHtml;
    
    // 更新连板股票列表
    const continuousHtml = conceptData.limit_ups
        .filter(stock => stock.continuous_days > 1)
        .map(stock => 
            `<span class="stock-tag continuous">${stock.name} (${stock.continuous_days}板)</span>`
        ).join('');
    document.getElementById('concept-continuous').innerHTML = continuousHtml;
    
    // 更新炸板股票列表
    const brokenHtml = conceptData.broken_limits.map(stock => 
        `<span class="stock-tag broken">${stock.name}</span>`
    ).join('');
    document.getElementById('concept-broken').innerHTML = brokenHtml;
    
    // 更新跌停股票列表
    const limitDownsHtml = conceptData.limit_downs.map(stock => 
        `<span class="stock-tag limit-down">${stock.name}</span>`
    ).join('');
    document.getElementById('concept-limit-downs').innerHTML = limitDownsHtml;
    
    modal.show();
}

// 页面加载完成后初始化
$(document).ready(function() {
    initLimitAnalysis();
}); 