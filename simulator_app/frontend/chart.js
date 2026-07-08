// ===============================
// Terminal Simulator Chart Engine
// ===============================

let chart;
let candlestickSeries;

const API_BASE = "";

let activeTicker = "NIFTY";
let activeTimeframe = "1D";
let refreshTimer = null;
let chartDataCache = [];

// --------------------------------
// Timeframe Mapping
// --------------------------------
function getTimeframeConfig(timeframe) {
    switch (timeframe) {
        case "5m":
            return {
                period: "5d",
                interval: "5m"
            };

        case "15m":
            return {
                period: "5d",
                interval: "15m"
            };

        case "1D":
        default:
            return {
                period: "1mo",
                interval: "1d"
            };
    }
}

// --------------------------------
// Create Chart
// --------------------------------
function initChart() {

    const chartContainer = document.getElementById("tvchart");

    chart = LightweightCharts.createChart(chartContainer, {

        width: chartContainer.clientWidth,
        height: 430,

        layout: {
            background: {
                type: "solid",
                color: "#0f172a"
            },
            textColor: "#d1d4dc"
        },

        grid: {
            vertLines: {
                color: "#243042"
            },
            horzLines: {
                color: "#243042"
            }
        },

        crosshair: {
            mode: LightweightCharts.CrosshairMode.Normal
        },

        timeScale: {
            borderColor: "#243042"
        }

    });

    candlestickSeries = chart.addCandlestickSeries({

        upColor: "#16a34a",
        downColor: "#ef4444",

        wickUpColor: "#16a34a",
        wickDownColor: "#ef4444",

        borderVisible: false

    });

    window.addEventListener("resize", () => {

        chart.resize(
            chartContainer.clientWidth,
            430
        );

    });

}

// --------------------------------
// Normalize Backend Data
// --------------------------------
function normalizeChartData(data, interval) {

    if (!Array.isArray(data))
        return [];

    return data.map(candle => ({

        time:
            interval.includes("m") || interval.includes("h")
                ? Number(candle.time)
                : candle.time,

        open: Number(candle.open),
        high: Number(candle.high),
        low: Number(candle.low),
        close: Number(candle.close)

    }));

}

// --------------------------------
// Load Chart
// --------------------------------
async function loadChartData(
    ticker = activeTicker,
    timeframe = activeTimeframe
) {

    activeTicker = ticker.toUpperCase();
    activeTimeframe = timeframe;

    const config = getTimeframeConfig(activeTimeframe);

    chartDataCache = [];

    try {

        const response = await fetch(
            `${API_BASE}/history/${encodeURIComponent(activeTicker)}?period=${config.period}&interval=${config.interval}`
        );

        if (!response.ok) {

            const errorText = await response.text();

            console.error(errorText);

            throw new Error(errorText);

        }

        const data = await response.json();

        const normalized =
            normalizeChartData(data, config.interval);

        if (normalized.length === 0) {

            throw new Error(
                "Backend returned no candles."
            );

        }

        chartDataCache = normalized;

        candlestickSeries.setData(chartDataCache);

        chart.timeScale().fitContent();

    }

    catch (error) {

        console.error(error);

        alert(

`Chart Loading Failed

Ticker : ${activeTicker}

${error.message}`

        );

    }

}

// --------------------------------
// Auto Refresh
// --------------------------------
function startAutoRefresh() {

    if (refreshTimer)
        clearInterval(refreshTimer);

    refreshTimer = setInterval(() => {

        loadChartData(
            activeTicker,
            activeTimeframe
        );

    }, 15000);

}

// --------------------------------
// Startup
// --------------------------------
document.addEventListener("DOMContentLoaded", () => {

    initChart();

    document
        .getElementById("chart-timeframe")
        .addEventListener("change", (e) => {

            loadChartData(
                activeTicker,
                e.target.value
            );

        });

    document
        .getElementById("load-chart-btn")
        .addEventListener("click", () => {

            const ticker =
                document
                .getElementById("ticker-input")
                .value
                .trim()
                .toUpperCase();
                console.log("Selected:", ticker);

            if (!ticker) {

                alert("Enter a ticker.");

                return;

            }

            loadChartData(
                ticker,
                activeTimeframe
            );

        });

    loadChartData(activeTicker);

    startAutoRefresh();

});