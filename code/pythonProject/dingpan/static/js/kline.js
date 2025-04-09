// K线图组件
class KlineChart {
    constructor() {
        this.chart = null;
        this.initSidePanel();
    }

    // 初始化侧边面板
    initSidePanel() {
        if ($('#side-panel').length === 0) {
            $('body').append(`
                <div id="side-panel" class="side-panel">
                    <div class="side-close-btn" title="关闭">×</div>
                    <div class="side-panel-header">
                        <h4 class="stock-name"></h4>
                        <div class="stock-info">
                            <span class="industry"></span>
                            <div class="concepts"></div>
                        </div>
                    </div>
                    <div id="kline-container"></div>
                </div>
            `);

            // 绑定关闭事件
            $('#side-panel .side-close-btn').click(() => this.hide());
        }
    }

    // 显示K线图
    async show(tsCode, name) {
        $('#side-panel').addClass('active');
        $('#side-panel .stock-name').text(name);
        
        if (!this.chart) {
            this.chart = echarts.init(document.getElementById('kline-container'));
        }

        try {
            const response = await $.get(`/api/stock_kline/${tsCode}`);
            // 显示行业信息
            $('#side-panel .industry').text(`【${response.industry}】`);
            
            // 显示概念信息
            const conceptsHtml = response.concepts
                .filter(concept => concept !== '-')  // 过滤掉 '-' 
                .map(concept => `<span class="concept-tag">${concept}</span>`)
                .join('');
            $('#side-panel .concepts').html(conceptsHtml);
            
            // 渲染K线图
            this.renderChart(response.kline);
        } catch (error) {
            console.error('Failed to load kline data:', error);
        }
    }

    // 隐藏面板
    hide() {
        $('#side-panel').removeClass('active');
    }

    // 渲染K线图
    renderChart(data) {
        // 计算默认展示范围
        const totalDays = data.length;
        const defaultDays = 90;
        const start = Math.max(0, ((totalDays - defaultDays) / totalDays) * 100);
        const end = 100;

        const option = {
            animation: true,
            animationDuration: 300,
            animationEasing: 'quadraticInOut',
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                }
            },
            legend: {
                data: ['K线', 'MA5', 'MA10', 'MA20', 'MA60', 'BOLL上轨', 'BOLL中轨', 'BOLL下轨'],
                top: 25
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
                data: data.map(item => item.trade_date),
                scale: true,
                boundaryGap: false,
                axisLine: { onZero: false },
                splitLine: { show: false },
                axisLabel: {
                    show: true,
                    fontSize: 10
                }
            }, {
                type: 'category',
                gridIndex: 1,
                data: data.map(item => item.trade_date),
                axisLabel: { show: false }
            }],
            yAxis: [{
                scale: true,
                splitArea: { show: true }
            }, {
                scale: true,
                gridIndex: 1,
                splitNumber: 2,
                axisLabel: { show: false }
            }],
            dataZoom: [{
                type: 'inside',
                xAxisIndex: [0, 1],
                start: start,
                end: end,
                minValueSpan: 10,
                maxValueSpan: 240,
                zoomLock: false,
                throttle: 100,        // 设置节流阈值
                rangeMode: ['value', 'value'],
                moveOnMouseMove: true,  // 允许鼠标移动时触发移动
                preventDefaultMouseMove: true  // 阻止默认鼠标事件
            }, {
                show: true,
                xAxisIndex: [0, 1],
                type: 'slider',
                bottom: '0%',
                start: start,
                end: end,
                minValueSpan: 10,
                maxValueSpan: 240,
                realtime: true,      // 拖动时实时更新
                throttle: 100,       // 设置节流阈值
                labelFormatter: (value) => {
                    const idx = Math.floor((data.length - 1) * (value / 100));
                    return data[idx]?.trade_date || '';
                },
                textStyle: {
                    color: '#333'
                },
                handleStyle: {      // 手柄样式
                    color: '#fff',
                    borderColor: '#ACB8D1'
                },
                borderColor: '#ddd',
                backgroundColor: '#f7f7f7',
                fillerColor: 'rgba(47,69,84,0.1)',
                emphasis: {         // 高亮样式
                    handleStyle: {
                        borderColor: '#8FB0F7'
                    }
                }
            }],
            series: [{
                name: 'K线',
                type: 'candlestick',
                data: data.map(item => [item.open, item.close, item.low, item.high]),
                itemStyle: {
                    color: '#ef232a',
                    color0: '#14b143',
                    borderColor: '#ef232a',
                    borderColor0: '#14b143'
                }
            }, {
                name: 'MA5',
                type: 'line',
                data: data.map(item => item.ma_5),
                smooth: true,
                showSymbol: false,
                lineStyle: {
                    opacity: 0.6,
                    color: '#000000',      // 黑色
                    width: 1
                }
            }, {
                name: 'MA10',
                type: 'line',
                data: data.map(item => item.ma_10),
                smooth: true,
                showSymbol: false,
                lineStyle: {
                    opacity: 0.6,
                    color: '#800080',      // 紫色
                    width: 1
                }
            }, {
                name: 'MA20',
                type: 'line',
                data: data.map(item => item.ma_20),
                smooth: true,
                showSymbol: false,
                lineStyle: {
                    opacity: 0.6,
                    color: '#FFD700',      // 黄色
                    width: 1
                }
            }, {
                name: 'MA60',
                type: 'line',
                data: data.map(item => item.ma_60),
                smooth: true,
                showSymbol: false,
                lineStyle: {
                    opacity: 0.6,
                    color: '#FF0000',      // 红色
                    width: 1
                }
            }, {
                name: 'BOLL上轨',
                type: 'line',
                data: data.map(item => item.boll_up),
                smooth: true,
                showSymbol: false,
                lineStyle: {
                    opacity: 0.6,
                    color: '#FF0000',     // 红色
                    width: 1,
                    type: 'solid'
                }
            }, {
                name: 'BOLL中轨',
                type: 'line',
                data: data.map(item => item.boll_mid),
                smooth: true,
                showSymbol: false,
                lineStyle: {
                    opacity: 0.6,
                    color: '#800080',     // 紫色
                    width: 1,
                    type: 'solid'
                }
            }, {
                name: 'BOLL下轨',
                type: 'line',
                data: data.map(item => item.boll_low),
                smooth: true,
                showSymbol: false,
                lineStyle: {
                    opacity: 0.6,
                    color: '#00FF00',     // 绿色
                    width: 1,
                    type: 'solid'
                }
            }, {
                name: '成交额',
                type: 'bar',
                xAxisIndex: 1,
                yAxisIndex: 1,
                data: data.map(item => item.amount),
                itemStyle: {
                    color: function(params) {
                        const k = data[params.dataIndex];
                        return k.close >= k.open ? '#f56c6c' : '#67c23a';  // 收盘价>=开盘价用红色，否则用绿色
                    }
                }
            }]
        };

        this.chart.setOption(option);
        
        // 监听缩放事件并使用防抖
        let timer = null;
        this.chart.on('datazoom', (params) => {
            if (timer) clearTimeout(timer);
            timer = setTimeout(() => {
                const {start, end} = params.batch[0];
                this.chart.setOption({
                    dataZoom: [{
                        start: start,
                        end: end
                    }, {
                        start: start,
                        end: end
                    }]
                });
            }, 50);  // 50ms 的防抖延迟
        });

        // 监听窗口大小变化
        window.addEventListener('resize', () => {
            this.chart.resize();
        });
    }

    // 格式化数字
    formatNumber(value) {
        return value ? value.toLocaleString() : '-';
    }

    // 格式化金额（转为亿）
    formatAmount(value) {
        if (!value) return '-';
        return (value / 100000000).toFixed(2) + '亿';
    }
}

// 导出实例
window.klineChart = new KlineChart(); 