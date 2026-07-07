// Global chart variables
let chart;
let candlestickSeries;
const API_BASE = "";

function initChart() {
    const chartContainer = document.getElementById('tvchart');
    
    // Create the Lightweight Chart
    chart = LightweightCharts.createChart(chartContainer, {
        width: chartContainer.clientWidth,
        height: 400,
        layout: {
            background: { type: 'solid', color: '#131a26' },
            textColor: '#d1d4dc',
        },
        grid: {
            vertLines: { color: '#2a2e39' },
            horzLines: { color: '#2a2e39' },
        },
        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal,
        },
        timeScale: {
            borderColor: '#2a2e39',
        }
    });

    candlestickSeries = chart.addCandlestickSeries({
        upColor: '#089981',
        downColor: '#f23645',
        borderVisible: false,
        wickUpColor: '#089981',
        wickDownColor: '#f23645'
    });

    // Handle window resizing
    window.addEventListener('resize', () => {
        chart.resize(chartContainer.clientWidth, 400);
    });
}

async function loadChartData(ticker) {
    try {
        const response = await fetch(`${API_BASE}/history/${ticker}`);
        const data = await response.json();
        
        // Lightweight charts expects data in ascending time order
        candlestickSeries.setData(data);
    } catch (error) {
        console.error("Error loading chart:", error);
        alert("Failed to load chart data. Ensure backend is running.");
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initChart();
    // Default load SPY chart
    loadChartData('SPY');

    document.getElementById('load-chart-btn').addEventListener('click', () => {
        const ticker = document.getElementById('ticker-input').value.toUpperCase();
        loadChartData(ticker);
    });
});