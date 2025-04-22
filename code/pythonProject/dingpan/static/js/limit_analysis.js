// 初始化涨停分析页面
function initLimitAnalysis() {
    // 创建涨停股票表格
    const limitStocksTable = new Tabulator("#limit-stocks-table", {
        height: "100%",  // 改为100%以充满容器
        layout: "fitColumns",  // 使用列自适应布局
        responsiveLayout: "hide",
        tooltips: true,
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
            {
                title: "股票名称", 
                field: "name", 
                width: 100,
                sorter: "string"
            },
            {
                title: "涨幅", 
                field: "change_pct", 
                width: 80,
                sorter: "number",
                formatter: function(cell) {
                    const value = cell.getValue();
                    const color = value >= 0 ? 'up-color' : 'down-color';
                    return `<span class="${color}">${value.toFixed(2)}%</span>`;
                }
            },
            {
                title: "状态", 
                field: "continuous_days", 
                width: 80,
                sorter: "number",
                formatter: function(cell) {
                    const row = cell.getRow().getData();
                    if (row.type === 'broken') {
                        return '<span class="status-tag broken">炸板</span>';
                    } else if (row.type === 'limit_down') {
                        return '<span class="status-tag limit-down">跌停</span>';
                    } else {
                        const value = cell.getValue();
                        if (value === 1) {
                            return '<span class="status-tag limit-up">首板</span>';
                        } else {
                            return `<span class="status-tag limit-up">${value}板</span>`;
                        }
                    }
                }
            },
            {
                title: "首次涨停", 
                field: "first_limit_time", 
                width: 100,
                sorter: "string"
            },
            {
                title: "成交额(亿)", 
                field: "amount", 
                width: 100,
                sorter: "number",
                formatter: function(cell) {
                    return (cell.getValue()).toFixed(2);
                }
            },
            {
                title: "行业", 
                field: "industry", 
                width: 120,
                sorter: "string"
            },
            {
                title: "概念", 
                field: "concepts", 
                sorter: "string",
                formatter: function(cell) {
                    const concepts = cell.getValue().split(',');
                    return concepts.map(concept => 
                        `<span class="concept-tag">${concept.trim()}</span>`
                    ).join(' ');
                },
                widthGrow: 3,  // 让概念列占用更多的剩余空间
                responsive: 0,  // 永不隐藏
                cssClass: "wrap-text concept-cell"  // 添加 concept-cell 类
            }
        ],
        rowClick: function(e, row) {
            const tsCode = row.getData().ts_code;
            const name = row.getData().name;
            window.klineChart.show(tsCode, name);
        }
    });

    // 创建概念统计表格
    const conceptStatsTable = new Tabulator("#concept-stats-table", {
        height: "100%",  // 改为100%以充满容器
        layout: "fitColumns",  // 改为 fitColumns 使列自动填充宽度
        columns: [
            {
                title: "概念", 
                field: "concept", 
                sorter: "string", 
                width: 150,  // 固定概念列宽度
                headerSort: true,
                headerSortStartingDir: "desc"
            },
            {
                title: "涨停", 
                field: "limit_up_count", 
                sorter: "number", 
                hozAlign: "center",
                headerSort: true,
                headerSortStartingDir: "desc"
            },
            {
                title: "连板", 
                field: "continuous_count", 
                sorter: "number", 
                hozAlign: "center",
                headerSort: true,
                headerSortStartingDir: "desc"
            },
            {
                title: "创业", 
                field: "gem_limit_up_count", 
                sorter: "number", 
                hozAlign: "center",
                headerSort: true,
                headerSortStartingDir: "desc"
            },
            {
                title: "炸板", 
                field: "broken_count", 
                sorter: "number", 
                hozAlign: "center",
                headerSort: true,
                headerSortStartingDir: "desc"
            },
            {
                title: "跌停", 
                field: "limit_down_count", 
                sorter: "number", 
                hozAlign: "center",
                headerSort: true,
                headerSortStartingDir: "desc"
            }
        ],
        initialSort: [
            {column: "limit_up_count", dir: "desc"}
        ]
    });

    // 处理侧边栏显示/隐藏
    function toggleConceptStats() {
        console.log('切换概念统计显示状态');  // 添加调试日志
        const sidebar = $('#concept-stats-sidebar');
        sidebar.toggleClass('show');
        
        // 如果侧边栏变为可见，重新调整表格大小
        if(sidebar.hasClass('show')) {
            conceptStatsTable.redraw(true);
        }
    }

    // 绑定按钮点击事件
    $(document).ready(function() {
        // 使用事件委托绑定点击事件
        $(document).on('click', '#toggle-concept-stats', function(e) {
            e.preventDefault();
            console.log('概念统计按钮被点击');  // 添加调试日志
            toggleConceptStats();
        });

        $(document).on('click', '#close-concept-stats', function(e) {
            e.preventDefault();
            console.log('关闭概念统计按钮被点击');  // 添加调试日志
            toggleConceptStats();
        });

        // 添加快捷键支持
        $(document).on('keydown', function(e) {
            // Alt + D
            if (e.altKey && e.keyCode === 68) {
                e.preventDefault(); // 阻止默认行为
                console.log('快捷键 Alt+D 被触发');  // 添加调试日志
                toggleConceptStats();
            }
        });
    });

    // 处理概念统计显示切换
    $('#show-limit-up, #show-continuous, #show-broken, #show-limit-down').change(function() {
        const column = conceptStatsTable.getColumn($(this).attr('id').replace('show-', ''));
        column.toggle();
    });

    // 处理股票类型过滤
    function updateStockFilter() {
        try {
            console.log('开始更新股票过滤器');
            const filters = [];
            if($('#filter-limit-up').prop('checked')) filters.push('limit_up');
            if($('#filter-broken').prop('checked')) filters.push('broken');
            if($('#filter-continuous').prop('checked')) filters.push('continuous');
            if($('#filter-limit-down').prop('checked')) filters.push('limit_down');
            
            console.log('选中的过滤器:', filters);
            
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

            // 手动触发 dataFiltered 回调来更新记录数
            const filteredData = limitStocksTable.getData("active");
            const totalRecordsElement = document.getElementById('total-records');
            
            // 检查元素是否存在
            if (totalRecordsElement) {
                console.log('更新记录数:', filteredData.length);
                totalRecordsElement.textContent = filteredData.length;
            } else {
                console.warn('未找到total-records元素');
            }
            
        } catch (error) {
            console.error('更新过滤器时出错:', error);
        }
    }

    // 初始化时设置默认过滤器
    function initStockFilter() {
        try {
            console.log('初始化股票过滤器');
            // 默认全部勾选
            $('#filter-limit-up').prop('checked', true);
            $('#filter-broken').prop('checked', true);
            $('#filter-continuous').prop('checked', true);
            $('#filter-limit-down').prop('checked', true);
            
            // 应用过滤器
            updateStockFilter();
        } catch (error) {
            console.error('初始化过滤器时出错:', error);
        }
    }

    // 绑定过滤器事件
    $('.stock-type-filter input').change(updateStockFilter);

    // 将 updateLimitAnalysis 函数移到全局作用域
    window.updateLimitAnalysis = function(date, isRealtime) {
        // 构建API URL
        let url = '/api/limit_up_analysis';
        if (!isRealtime && date) {
            url = `/api/limit_up_analysis/${date}`;  // 添加日期参数到URL
        }
        
        // 发起请求
        $.get(url, function(data) {
            console.log('涨停分析数据:', data);
            
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
            
            // 更新概念统计表格数据
            if (data.concept_stats) {
                conceptStatsTable.setData(data.concept_stats);
            }

        }).fail(function(jqXHR, textStatus, errorThrown) {
            console.error('请求失败:', textStatus, errorThrown);
        });
    };

    // 首次加载数据
    updateLimitAnalysis();

    // 设置定时刷新
    // setInterval(updateLimitAnalysis, 10000);

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

// 添加一些CSS样式
const style = document.createElement('style');
style.textContent = `
    #limit-stocks-table {
        height: 100% !important;
    }
    .card-body {
        height: 100%;
        padding: 0;
    }
    .tabulator {
        height: 100% !important;
        max-height: none !important;
    }
    .tabulator-row {
        cursor: pointer;
    }
    .tabulator-row:hover {
        background-color: #f5f5f5 !important;
    }
    .up-color {
        color: #f55;
    }
    .down-color {
        color: #0c0;
    }
    .continuous-days {
        color: #f55;
        font-weight: bold;
    }
    .concept-cell {
        overflow-wrap: break-word;  /* 允许在任意字符间换行 */
        word-wrap: break-word;  /* 兼容性写法 */
        word-break: break-all;  /* 允许在单词内换行 */
        flex-grow: 1;  /* 允许单元格伸展 */
    }
    .concept-tag {
        display: inline-block;
        padding: 2px 6px;
        margin: 2px;
        background: #f0f0f0;
        border-radius: 4px;
        font-size: 12px;
        white-space: normal;  /* 允许换行 */
        box-sizing: border-box;  /* 包含内边距和边框 */
    }
    .wrap-text {
        white-space: normal !important;  /* 强制允许换行 */
        height: auto !important;  /* 允许高度自适应 */
    }
    .tabulator-cell {
        height: auto !important;  /* 允许单元格高度自适应 */
        padding: 8px !important;  /* 增加一些内边距 */
        vertical-align: top !important;  /* 顶部对齐 */
    }
    .tabulator-footer-records {
        padding: 10px;
        text-align: right;
        color: #666;
    }
`;
document.head.appendChild(style);

// 添加相关的CSS样式
const sidebarStyle = document.createElement('style');
sidebarStyle.textContent = `
    #concept-stats-sidebar {
        position: fixed;
        top: 0;
        right: -600px;
        width: 600px;
        height: 100vh;
        background: #fff;
        box-shadow: -2px 0 5px rgba(0,0,0,0.1);
        transition: right 0.3s ease;
        z-index: 1050;
    }
    
    #concept-stats-sidebar.show {
        right: 0;
    }
    
    .sidebar-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem;
        border-bottom: 1px solid #eee;
    }
    
    .sidebar-content {
        padding: 1rem;
        height: calc(100% - 60px);
        overflow-y: auto;
    }
    
    .shortcut-tip {
        font-size: 12px;
        color: #666;
        margin-right: 10px;
    }
`;
document.head.appendChild(sidebarStyle); 