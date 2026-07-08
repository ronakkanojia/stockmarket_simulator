// Global chart variables
let chart;
let candlestickSeries;
const API_BASE = "";
let activeTicker = "SPY";
let activeTimeframe = "1D";
let refreshTimer = null;
let chartDataCache = [];

function getTimeframeConfig(timeframe) {
    switch (timeframe) {
        case "5m":
            return { period: "5d", interval: "5m" };
        case "15m":
            return { period: "5d", interval: "15m" };
        case "1D":
        default:
            return { period: "1d", interval: "1m" };
    }
}

function initChart() {
    const chartContainer = document.getElementById('tvchart');

    chart = LightweightCharts.createChart(chartContainer, {
        width: chartContainer.clientWidth,
        height: 430,
        layout: {
            background: { type: 'solid', color: '#0f172a' },
            textColor: '#d1d4dc',
        },
        grid: {
            vertLines: { color: '#243042' },
            horzLines: { color: '#243042' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        timeScale: {
            borderColor: '#243042',
        }
    });

    candlestickSeries = chart.addCandlestickSeries({
        upColor: '#16a34a',
        downColor: '#ef4444',
        borderVisible: false,
        wickUpColor: '#16a34a',
        wickDownColor: '#ef4444'
    });

    window.addEventListener('resize', () => {
        chart.resize(chartContainer.clientWidth, 430);
    });
}

function normalizeChartData(data, interval) {
    if (!Array.isArray(data)) {
        return [];
    }

    return data.map((item) => {
        const timeValue = interval && (interval.includes('m') || interval.includes('h'))
            ? Number(item.time)
            : item.time;

        return {
            ...item,
            time: timeValue
        };
    });
}

function mergeChartData(existingData, incomingData) {
    if (!incomingData.length) {
        return existingData;
    }

    if (!existingData.length) {
        return incomingData;
    }

    const merged = [...existingData];
    const seenTimes = new Set(existingData.map((item) => String(item.time)));

    incomingData.forEach((item) => {
        const key = String(item.time);
        if (seenTimes.has(key)) {
            const index = merged.findIndex((existingItem) => String(existingItem.time) === key);
            if (index >= 0) {
                merged[index] = item;
            }
        } else {
            merged.push(item);
            seenTimes.add(key);
        }
    });

    return merged.sort((a, b) => a.time - b.time);
}

async function loadChartData(ticker = activeTicker, timeframe = activeTimeframe) {
    activeTicker = ticker.toUpperCase();
    activeTimeframe = timeframe;
    const config = getTimeframeConfig(activeTimeframe);

    try {
        const response = await fetch(`${API_BASE}/history/${encodeURIComponent(activeTicker)}?period=${config.period}&interval=${config.interval}`);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(errorData.detail || 'Failed to load chart data');
        }

        const data = await response.json();
        const normalizedData = normalizeChartData(data, config.interval);

        if (!normalizedData.length) {
            throw new Error('No chart data returned');
        }

        chartDataCache = mergeChartData(chartDataCache, normalizedData);
        candlestickSeries.setData(chartDataCache);
        chart.timeScale().fitContent();
    } catch (error) {
        console.error('Error loading chart:', error);
        alert(`Failed to load chart data for ${activeTicker}. Try a different ticker or timeframe.`);
    }
}

function startAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }

    refreshTimer = setInterval(() => {
        if (activeTicker) {
            loadChartData(activeTicker, activeTimeframe);
        }
    }, 15000);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initChart();

    const timeframeSelector = document.getElementById('chart-timeframe');
    if (timeframeSelector) {
        timeframeSelector.addEventListener('change', (event) => {
            chartDataCache = [];
            loadChartData(activeTicker, event.target.value);
        });
    }

    loadChartData('SPY', activeTimeframe);
    startAutoRefresh();

    document.getElementById('load-chart-btn').addEventListener('click', () => {
        const ticker = document.getElementById('ticker-input').value.toUpperCase();
        loadChartData(ticker, activeTimeframe);
    });
});