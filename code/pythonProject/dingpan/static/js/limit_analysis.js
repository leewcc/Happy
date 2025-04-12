// 初始化涨停分析页面
function initLimitAnalysis() {
    // 创建概念统计表格
    const conceptStatsTable = new Tabulator("#concept-stats-table", {
        height: "400px",
        layout: "fitColumns",
        columns: [
            {title: "概念", field: "concept", sorter: "string"},
            {title: "涨停数", field: "limit_up_count", sorter: "number", visible: true},
            {title: "连板数", field: "continuous_count", sorter: "number", visible: false},
            {title: "炸板数", field: "broken_count", sorter: "number", visible: false},
            {title: "跌停数", field: "limit_down_count", sorter: "number", visible: false}
        ]
    });

    // 创建涨停股票表格
    const limitStocksTable = new Tabulator("#limit-stocks-table", {
        height: "400px",
        layout: "fitColumns",
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
            return filters.some(type => {
                switch(type) {
                    case 'limit_up': return data.change_pct >= 9.8;
                    case 'broken': return data.is_broken;
                    case 'continuous': return data.continuous_days > 1;
                    case 'limit_down': return data.change_pct <= -9.8;
                }
            });
        });
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
            conceptStatsTable.setData(data.concept_stats || []);
            limitStocksTable.setData(data.limit_stocks || []);
        }).fail(function(jqXHR, textStatus, errorThrown) {
            console.error('请求失败:', textStatus, errorThrown);
        });
    }

    // 首次加载数据
    updateLimitAnalysis();

    // 设置定时刷新
    setInterval(updateLimitAnalysis, 10000);
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

// 页面加载完成后初始化
$(document).ready(function() {
    initLimitAnalysis();
}); 