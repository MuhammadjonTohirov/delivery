// Dashboard Charts - dashboard-charts.js

class DashboardCharts {
    constructor() {
        this.charts = {};
        this.chartDefaults = {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom'
                
                },
                title: {
                    display: false,
                    text: 'Dashboard Chart'
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    intersect: false
                }
            }
        };
    }

    initializeAllCharts() {
        this.initializePieCharts();
        this.initializeLineCharts();
        this.initializeBarCharts();
    }

    initializePieCharts() {
        const pieChartOptions = {
            ...this.chartDefaults,
            cutout: '70%',
            radius: '90%'
        };

        // Initialize pie charts with proper sizing
        const charts = [
            { id: 'totalOrderChart', data: [81, 19] },
            { id: 'customerGrowthChart', data: [22, 78] },
            { id: 'totalRevenueChart', data: [45, 55] }
        ];

        charts.forEach(chart => {
            const ctx = document.getElementById(chart.id);
            if (ctx) {
                this.charts[chart.id] = new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        datasets: [{
                            data: chart.data,
                            backgroundColor: ['#4338ca', '#e5e7eb'],
                            borderWidth: 0
                        }]
                    },
                    options: pieChartOptions
                });
            }
        });
    }

    initializeLineCharts() {
        const lineChartOptions = {
            ...this.chartDefaults,
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        drawBorder: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        };

        // Initialize line charts with proper sizing
        ['orderChart', 'revenueChart'].forEach(chartId => {
            const ctx = document.getElementById(chartId);
            if (ctx) {
                this.charts[chartId] = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                        datasets: [{
                            label: chartId === 'orderChart' ? 'Orders' : 'Revenue',
                            data: [65, 59, 80, 81, 56, 55, 40],
                            fill: true,
                            backgroundColor: 'rgba(67, 56, 202, 0.1)',
                            borderColor: '#4338ca',
                            tension: 0.4
                        }]
                    },
                    options: lineChartOptions
                });
            }
        });
    }

    initializeBarCharts() {
        // Orders Count Chart
        const ordersCountCtx = document.getElementById('ordersCountChart');
        if (ordersCountCtx) {
            this.charts.ordersCount = new Chart(ordersCountCtx, {
                type: 'bar',
                data: {
                    labels: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
                    datasets: [{
                        data: [65, 85, 45, 92, 85, 35, 72],
                        backgroundColor: [
                            '#fbbf24', '#ef4444', '#fbbf24', 
                            '#ef4444', '#10b981', '#fbbf24', '#ef4444'
                        ],
                        borderRadius: 4,
                        borderSkipped: false
                    }]
                },
                options: {
                    ...this.chartDefaults,
                    scales: {
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                color: '#64748b'
                            }
                        },
                        y: {
                            grid: {
                                color: '#f1f5f9'
                            },
                            ticks: {
                                color: '#64748b'
                            }
                        }
                    }
                }
            });
        }
    }

    addCenterText(canvas, text) {
        const chart = Chart.getChart(canvas);
        if (!chart) return;

        Chart.register({
            id: 'centerText',
            beforeDraw: function(chart) {
                if (chart.canvas !== canvas) return;
                
                const ctx = chart.ctx;
                const centerX = (chart.chartArea.left + chart.chartArea.right) / 2;
                const centerY = (chart.chartArea.top + chart.chartArea.bottom) / 2;

                ctx.save();
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.font = 'bold 18px Inter';
                ctx.fillStyle = '#1e293b';
                ctx.fillText(text, centerX, centerY);
                ctx.restore();
            }
        });
    }

    updateStatsCharts(data) {
        // Update pie charts with real data
        if (this.charts.totalOrders && data.orderStats) {
            const total = data.orderStats.total || 100;
            const completed = data.orderStats.completed || 0;
            const percentage = Math.round((completed / total) * 100);
            
            this.charts.totalOrders.data.datasets[0].data = [percentage, 100 - percentage];
            this.charts.totalOrders.update();
        }

        if (this.charts.customerGrowth && data.customerGrowth) {
            const growth = data.customerGrowth.percentage || 22;
            this.charts.customerGrowth.data.datasets[0].data = [growth, 100 - growth];
            this.charts.customerGrowth.update();
        }

        if (this.charts.totalRevenue && data.revenueStats) {
            const target = data.revenueStats.target || 100;
            const achieved = data.revenueStats.achieved || 0;
            const percentage = Math.round((achieved / target) * 100);
            
            this.charts.totalRevenue.data.datasets[0].data = [percentage, 100 - percentage];
            this.charts.totalRevenue.update();
        }
    }

    updateOrderChart(weeklyData) {
        if (this.charts.orders && weeklyData) {
            this.charts.orders.data.datasets[0].data = weeklyData;
            this.charts.orders.update();
        }
    }

    updateRevenueChart(monthlyData) {
        if (this.charts.revenue && monthlyData) {
            this.charts.revenue.data.datasets.forEach((dataset, index) => {
                if (monthlyData[index]) {
                    dataset.data = monthlyData[index];
                }
            });
            this.charts.revenue.update();
        }
    }

    updateOrdersCountChart(dailyData) {
        if (this.charts.ordersCount && dailyData) {
            this.charts.ordersCount.data.datasets[0].data = dailyData.values;
            if (dailyData.colors) {
                this.charts.ordersCount.data.datasets[0].backgroundColor = dailyData.colors;
            }
            this.charts.ordersCount.update();
        }
    }

    destroyChart(chartName) {
        if (this.charts[chartName]) {
            this.charts[chartName].destroy();
            delete this.charts[chartName];
        }
    }

    destroyAllCharts() {
        Object.keys(this.charts).forEach(chartName => {
            this.destroyChart(chartName);
        });
    }

    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            chart.resize();
        });
    }

    exportChart(chartName, filename) {
        if (this.charts[chartName]) {
            const url = this.charts[chartName].toBase64Image();
            const a = document.createElement('a');
            a.href = url;
            a.download = `${filename}.png`;
            a.click();
        }
    }

    createCustomChart(elementId, type, data, options = {}) {
        const ctx = document.getElementById(elementId);
        if (!ctx) return null;

        const mergedOptions = {
            ...this.chartDefaults,
            ...options
        };

        const chart = new Chart(ctx, {
            type: type,
            data: data,
            options: mergedOptions
        });

        this.charts[elementId] = chart;
        return chart;
    }

    getChartData(chartName) {
        return this.charts[chartName]?.data || null;
    }

    updateChartColors(theme = 'light') {
        const colors = {
            light: {
                text: '#64748b',
                grid: '#f1f5f9',
                background: '#ffffff'
            },
            dark: {
                text: '#cbd5e1',
                grid: '#334155',
                background: '#1e293b'
            }
        };

        const currentColors = colors[theme];

        Object.values(this.charts).forEach(chart => {
            if (chart.options.scales) {
                Object.values(chart.options.scales).forEach(scale => {
                    if (scale.ticks) scale.ticks.color = currentColors.text;
                    if (scale.grid) scale.grid.color = currentColors.grid;
                });
            }
            chart.update();
        });
    }

    animateChart(chartName, duration = 1000) {
        if (this.charts[chartName]) {
            this.charts[chartName].update('active', {
                duration: duration,
                easing: 'easeInOutQuart'
            });
        }
    }
}

// Initialize charts when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.dashboardCharts = new DashboardCharts();
});

// Handle window resize
window.addEventListener('resize', DashboardComponents.debounce(() => {
    if (window.dashboardCharts) {
        window.dashboardCharts.resizeCharts();
    }
}, 250));

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardCharts;
}