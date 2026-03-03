/**
 * ApexCharts Implementation for Eazr Admin Dashboard
 * Replaces custom chart renderers with professional ApexCharts
 * Matches Core 2.0 Design System
 */

// Store chart instances for updates/cleanup
const chartInstances = {};

/**
 * Get current theme mode
 */
function getCurrentTheme() {
    return document.documentElement.getAttribute('data-theme') || 'light';
}

/**
 * Clean modern color palette for charts
 * Inspired by: ChatGPT, Claude, Asana, Notion
 */
const modernColors = {
    primary: '#0ea5e9',
    blue: '#3b82f6',
    green: '#10b981',
    purple: '#8b5cf6',
    orange: '#f59e0b',
    red: '#ef4444',
    teal: '#14b8a6',
    gray: '#6b7280'
};

/**
 * Base ApexCharts Configuration (Notion-Style Design)
 */
function getBaseChartOptions() {
    const theme = getCurrentTheme();

    return {
        chart: {
            fontFamily: '-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", "Roboto", sans-serif',
            toolbar: {
                show: true,
                tools: {
                    download: true,
                    selection: false,
                    zoom: false,
                    zoomin: false,
                    zoomout: false,
                    pan: false,
                    reset: false
                },
                offsetY: -10
            },
            zoom: {
                enabled: false
            },
            foreColor: theme === 'dark' ? '#b0b0b0' : '#7b7b7b',
            background: 'transparent',
            animations: {
                enabled: true,
                easing: 'easeinout',
                speed: 800,
                animateGradually: {
                    enabled: true,
                    delay: 150
                },
                dynamicAnimation: {
                    enabled: true,
                    speed: 350
                }
            }
        },
        theme: {
            mode: theme
        },
        grid: {
            borderColor: theme === 'dark' ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.04)',
            strokeDashArray: 0,
            padding: {
                left: 10,
                right: 20,
                top: 10,
                bottom: 10
            },
            xaxis: {
                lines: {
                    show: false
                }
            },
            yaxis: {
                lines: {
                    show: true
                }
            }
        },
        colors: [modernColors.primary, modernColors.blue, modernColors.green, modernColors.purple,
                 modernColors.orange, modernColors.teal, modernColors.red],
        xaxis: {
            axisBorder: {
                show: false
            },
            axisTicks: {
                show: false
            },
            labels: {
                style: {
                    fontSize: '12px',
                    fontWeight: 500,
                    colors: theme === 'dark' ? '#7b7b7b' : '#7b7b7b'
                }
            }
        },
        yaxis: {
            labels: {
                style: {
                    fontSize: '12px',
                    fontWeight: 500,
                    colors: theme === 'dark' ? '#7b7b7b' : '#7b7b7b'
                },
                formatter: function(val) {
                    if (val >= 1000000) {
                        return (val / 1000000).toFixed(1) + 'M';
                    } else if (val >= 1000) {
                        return (val / 1000).toFixed(1) + 'K';
                    }
                    return Math.round(val);
                }
            }
        },
        tooltip: {
            theme: 'light',
            style: {
                fontSize: '13px',
                fontFamily: '-apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", "Roboto", sans-serif'
            },
            y: {
                formatter: function(val) {
                    return val !== undefined ? val.toLocaleString() : '';
                }
            },
            marker: {
                show: true
            },
            x: {
                show: true
            },
            fillSeriesColor: false,
            custom: undefined
        },
        legend: {
            fontSize: '13px',
            fontWeight: 500,
            labels: {
                colors: theme === 'dark' ? '#b4b4b4' : '#787774'
            },
            markers: {
                width: 12,
                height: 12,
                radius: 3
            }
        },
        stroke: {
            width: 3,
            curve: 'smooth',
            lineCap: 'round'
        },
        markers: {
            size: 0,
            hover: {
                size: 6
            }
        },
        fill: {
            type: 'gradient',
            gradient: {
                shade: 'light',
                type: 'vertical',
                shadeIntensity: 0.1,
                opacityFrom: 0.8,
                opacityTo: 0.2,
                stops: [0, 100]
            }
        }
    };
}

/**
 * Helper: Format large numbers (millify)
 */
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'm';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k';
    }
    return num.toLocaleString();
}

/**
 * Destroy chart instance if exists
 */
function destroyChart(chartId) {
    if (chartInstances[chartId]) {
        chartInstances[chartId].destroy();
        delete chartInstances[chartId];
    }
}

/* ============================================
   1. Daily Users Chart (Bar Chart)
   ============================================ */
function renderDailyUsersChart(data) {
    const chartId = 'dailyUsersChart';
    destroyChart(chartId);

    const options = {
        ...getBaseChartOptions(),
        chart: {
            ...getBaseChartOptions().chart,
            type: 'bar',
            height: 296,
            animations: {
                enabled: true,
                easing: 'easeinout',
                speed: 800
            }
        },
        series: [{
            name: 'Users',
            data: data.map(d => d.users)
        }],
        plotOptions: {
            bar: {
                borderRadius: 8,
                columnWidth: '65%',
                distributed: false,
                dataLabels: {
                    position: 'top'
                }
            }
        },
        colors: [modernColors.primary],
        dataLabels: {
            enabled: false
        },
        xaxis: {
            ...getBaseChartOptions().xaxis,
            categories: data.map(d => d.date ? d.date.substring(5) : d.name),
            labels: {
                ...getBaseChartOptions().xaxis.labels,
                rotate: 0
            }
        },
        tooltip: {
            ...getBaseChartOptions().tooltip,
            custom: function({ series, seriesIndex, dataPointIndex, w }) {
                const value = series[seriesIndex][dataPointIndex];
                return `
                    <div class="chart-tooltip">
                        <div style="opacity: 0.8; margin-bottom: 2px;">Users</div>
                        <div style="font-weight: 700;">${formatNumber(value)}</div>
                    </div>
                `;
            }
        }
    };

    const chart = new ApexCharts(document.querySelector(`#${chartId}`), options);
    chart.render();
    chartInstances[chartId] = chart;
}

/* ============================================
   2. Message Volume Chart (Bar Chart)
   ============================================ */
function renderMessageVolumeChart(data) {
    const chartId = 'messageVolumeChart';
    destroyChart(chartId);

    const options = {
        ...getBaseChartOptions(),
        chart: {
            ...getBaseChartOptions().chart,
            type: 'bar',
            height: 296
        },
        series: [{
            name: 'Messages',
            data: data.map(d => d.messages)
        }],
        plotOptions: {
            bar: {
                borderRadius: 8,
                columnWidth: '65%'
            }
        },
        colors: [modernColors.blue],
        dataLabels: {
            enabled: false
        },
        xaxis: {
            ...getBaseChartOptions().xaxis,
            categories: data.map(d => d.date ? d.date.substring(5) : d.name)
        },
        tooltip: {
            ...getBaseChartOptions().tooltip,
            custom: function({ series, seriesIndex, dataPointIndex }) {
                return `
                    <div class="chart-tooltip">
                        <div style="opacity: 0.8; margin-bottom: 2px;">Messages</div>
                        <div style="font-weight: 700;">${formatNumber(series[seriesIndex][dataPointIndex])}</div>
                    </div>
                `;
            }
        }
    };

    const chart = new ApexCharts(document.querySelector(`#${chartId}`), options);
    chart.render();
    chartInstances[chartId] = chart;
}

/* ============================================
   3. Session Distribution Chart (Donut)
   ============================================ */
function renderSessionDistChart(data) {
    const chartId = 'sessionDistChart';
    destroyChart(chartId);

    const total = data.reduce((sum, item) => sum + item.count, 0);

    const options = {
        ...getBaseChartOptions(),
        chart: {
            ...getBaseChartOptions().chart,
            type: 'donut',
            height: 350
        },
        series: data.map(d => d.count),
        labels: data.map(d => d.status),
        colors: [modernColors.primary, modernColors.blue, modernColors.purple],
        plotOptions: {
            pie: {
                donut: {
                    size: '65%',
                    labels: {
                        show: true,
                        name: {
                            show: true,
                            fontSize: '14px',
                            fontWeight: 600,
                            color: 'var(--text-primary)'
                        },
                        value: {
                            show: true,
                            fontSize: '24px',
                            fontWeight: 800,
                            color: 'var(--text-primary)',
                            formatter: function(val) {
                                return val.toLocaleString();
                            }
                        },
                        total: {
                            show: true,
                            label: 'Total Sessions',
                            fontSize: '14px',
                            fontWeight: 500,
                            color: 'var(--text-secondary)',
                            formatter: function() {
                                return total.toLocaleString();
                            }
                        }
                    }
                }
            }
        },
        legend: {
            ...getBaseChartOptions().legend,
            position: 'bottom',
            horizontalAlign: 'center',
            fontSize: '14px',
            markers: {
                width: 12,
                height: 12,
                radius: 3
            }
        },
        dataLabels: {
            enabled: false
        },
        tooltip: {
            ...getBaseChartOptions().tooltip,
            y: {
                formatter: function(val) {
                    const percentage = ((val / total) * 100).toFixed(1);
                    return `${val.toLocaleString()} (${percentage}%)`;
                }
            }
        }
    };

    const chart = new ApexCharts(document.querySelector(`#${chartId}`), options);
    chart.render();
    chartInstances[chartId] = chart;
}

/* ============================================
   4. Policy Status Chart (Donut)
   ============================================ */
function renderPolicyStatusChart(data) {
    const chartId = 'policyStatusChart';
    destroyChart(chartId);

    const colorMap = {
        'Pending': modernColors.orange,
        'Completed': modernColors.green,
        'Rejected': modernColors.red
    };

    const total = data.reduce((sum, item) => sum + item.count, 0);
    const colors = data.map(d => colorMap[d.status] || modernColors.primary);

    const options = {
        ...getBaseChartOptions(),
        chart: {
            ...getBaseChartOptions().chart,
            type: 'donut',
            height: 350
        },
        series: data.map(d => d.count),
        labels: data.map(d => d.status),
        colors: colors,
        plotOptions: {
            pie: {
                donut: {
                    size: '65%',
                    labels: {
                        show: true,
                        name: {
                            show: true,
                            fontSize: '14px',
                            fontWeight: 600
                        },
                        value: {
                            show: true,
                            fontSize: '24px',
                            fontWeight: 800,
                            formatter: function(val) {
                                return val.toLocaleString();
                            }
                        },
                        total: {
                            show: true,
                            label: 'Total Policies',
                            fontSize: '14px',
                            fontWeight: 500,
                            color: 'var(--text-secondary)',
                            formatter: function() {
                                return total.toLocaleString();
                            }
                        }
                    }
                }
            }
        },
        legend: {
            ...getBaseChartOptions().legend,
            position: 'bottom',
            horizontalAlign: 'center'
        },
        dataLabels: {
            enabled: false
        }
    };

    const chart = new ApexCharts(document.querySelector(`#${chartId}`), options);
    chart.render();
    chartInstances[chartId] = chart;
}

/* ============================================
   5. Peak Hours Chart (Horizontal Bar)
   ============================================ */
function renderPeakHoursChart(data) {
    const chartId = 'peakHoursChart';
    destroyChart(chartId);

    // Filter only hours with activity
    const activeHours = data.filter(d => d.activity > 0);

    const options = {
        ...getBaseChartOptions(),
        chart: {
            ...getBaseChartOptions().chart,
            type: 'bar',
            height: 300
        },
        series: [{
            name: 'Activity',
            data: activeHours.map(d => d.activity)
        }],
        plotOptions: {
            bar: {
                horizontal: true,
                borderRadius: 4,
                barHeight: '70%'
            }
        },
        colors: [modernColors.green],
        dataLabels: {
            enabled: false
        },
        xaxis: {
            ...getBaseChartOptions().xaxis,
            categories: activeHours.map(d => d.hour)
        },
        tooltip: {
            ...getBaseChartOptions().tooltip,
            x: {
                formatter: function(val) {
                    return 'Hour: ' + val;
                }
            },
            y: {
                formatter: function(val) {
                    return val.toLocaleString() + ' activities';
                }
            }
        }
    };

    const chart = new ApexCharts(document.querySelector(`#${chartId}`), options);
    chart.render();
    chartInstances[chartId] = chart;
}

/* ============================================
   6. Top Users Chart (Bar)
   ============================================ */
function renderTopUsersChart(data) {
    const chartId = 'topUsersChart';
    destroyChart(chartId);

    const options = {
        ...getBaseChartOptions(),
        chart: {
            ...getBaseChartOptions().chart,
            type: 'bar',
            height: 296
        },
        series: [{
            name: 'Messages',
            data: data.map(d => d.messages)
        }],
        plotOptions: {
            bar: {
                borderRadius: 8,
                columnWidth: '70%'
            }
        },
        colors: [modernColors.teal],
        dataLabels: {
            enabled: false
        },
        xaxis: {
            ...getBaseChartOptions().xaxis,
            categories: data.map((d, index) => `User ${d.user_id}`),
            labels: {
                ...getBaseChartOptions().xaxis.labels,
                rotate: -45,
                rotateAlways: true
            }
        },
        tooltip: {
            ...getBaseChartOptions().tooltip,
            custom: function({ series, seriesIndex, dataPointIndex, w }) {
                const userId = data[dataPointIndex].user_id;
                const messages = series[seriesIndex][dataPointIndex];
                return `
                    <div class="chart-tooltip">
                        <div style="opacity: 0.8; margin-bottom: 2px;">User ${userId}</div>
                        <div style="font-weight: 700;">${formatNumber(messages)} messages</div>
                    </div>
                `;
            }
        }
    };

    const chart = new ApexCharts(document.querySelector(`#${chartId}`), options);
    chart.render();
    chartInstances[chartId] = chart;
}

/* ============================================
   7. Dashboard Users Chart (Bar - Gradient)
   ============================================ */
function renderDashboardUsersChart(data) {
    const chartId = 'dashboardUsersChart';
    destroyChart(chartId);

    const options = {
        ...getBaseChartOptions(),
        chart: {
            ...getBaseChartOptions().chart,
            type: 'bar',
            height: 276,
            sparkline: {
                enabled: false
            }
        },
        series: [{
            name: 'Users',
            data: data.map(d => d.users)
        }],
        plotOptions: {
            bar: {
                borderRadius: 8,
                columnWidth: '65%'
            }
        },
        colors: [modernColors.primary],
        fill: {
            type: 'gradient',
            gradient: {
                shade: 'light',
                type: 'vertical',
                shadeIntensity: 0.3,
                gradientToColors: [modernColors.blue],
                inverseColors: false,
                opacityFrom: 1,
                opacityTo: 0.8,
                stops: [0, 100]
            }
        },
        dataLabels: {
            enabled: false
        },
        xaxis: {
            ...getBaseChartOptions().xaxis,
            categories: data.map(d => d.date ? d.date.substring(5) : d.name)
        },
        tooltip: {
            ...getBaseChartOptions().tooltip,
            custom: function({ series, seriesIndex, dataPointIndex }) {
                return `
                    <div class="chart-tooltip">
                        ${formatNumber(series[seriesIndex][dataPointIndex])}
                    </div>
                `;
            }
        }
    };

    const chart = new ApexCharts(document.querySelector(`#${chartId}`), options);
    chart.render();
    chartInstances[chartId] = chart;
}

/* ============================================
   8. Dashboard Session Chart (Progress Bars)
   ============================================ */
function renderDashboardSessionChart(data) {
    const container = document.getElementById('dashboardSessionChart');
    if (!container) return;

    const total = data.reduce((sum, item) => sum + item.count, 0);

    let html = '<div style="padding: 20px;">';

    const statusColors = {
        'Active': modernColors.green,
        'Inactive': modernColors.gray,
        'Pending': modernColors.orange
    };

    data.forEach(item => {
        const percentage = total > 0 ? Math.round((item.count / total) * 100) : 0;
        const color = statusColors[item.status] || modernColors.primary;

        html += `
            <div class="progress-container" style="margin-bottom: 24px;">
                <div class="progress-label" style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                    <span class="progress-label-text" style="font-size: 14px; font-weight: 600; color: var(--text-primary);">${item.status}</span>
                    <span class="progress-label-value" style="font-size: 14px; font-weight: 500; color: var(--text-secondary);">${item.count} (${percentage}%)</span>
                </div>
                <div class="progress-track" style="height: 10px; background: var(--bg-cream); border-radius: 10px; overflow: hidden;">
                    <div class="progress-fill" style="width: ${percentage}%; height: 100%; background: ${color}; border-radius: 10px; transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);"></div>
                </div>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

/* ============================================
   Theme Change Handler
   ============================================ */
function updateChartsTheme(newTheme) {
    Object.keys(chartInstances).forEach(chartId => {
        if (chartInstances[chartId] && chartInstances[chartId].updateOptions) {
            chartInstances[chartId].updateOptions({
                theme: {
                    mode: newTheme
                }
            });
        }
    });
}

/* ============================================
   Export for global use
   ============================================ */
window.renderDailyUsersChart = renderDailyUsersChart;
window.renderMessageVolumeChart = renderMessageVolumeChart;
window.renderSessionDistChart = renderSessionDistChart;
window.renderPolicyStatusChart = renderPolicyStatusChart;
window.renderPeakHoursChart = renderPeakHoursChart;
window.renderTopUsersChart = renderTopUsersChart;
window.renderDashboardUsersChart = renderDashboardUsersChart;
window.renderDashboardSessionChart = renderDashboardSessionChart;
window.updateChartsTheme = updateChartsTheme;
window.chartInstances = chartInstances;
