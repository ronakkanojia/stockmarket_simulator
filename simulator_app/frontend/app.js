// By leaving this blank, the browser automatically uses the current host 
// (your Codespace URL running on Port 8000).
const API_URL = "";

// --- 1. Fetch and Display Portfolio ---
async function fetchPortfolio() {
    try {
        const res = await fetch(`${API_URL}/portfolio`);
        const data = await res.json();

        const cashBalance = document.getElementById('cash-balance');
        const positionCount = document.getElementById('position-count');

        if (cashBalance) {
            cashBalance.innerText = `₹${data.cash.toLocaleString()}`;
        }

        if (positionCount) {
            positionCount.innerText = Array.isArray(data.positions) ? data.positions.length : 0;
        }
    } catch (error) {
        console.error("Error fetching portfolio:", error);
    }
}

// --- 2. Fetch and Display Options Chain ---
async function fetchOptionsChain(ticker, expiry) {
    const tbody = document.getElementById('options-body');
    tbody.innerHTML = "<tr><td colspan='9' style='text-align:center;'>Loading data from yfinance...</td></tr>";

    try {
        const res = await fetch(`${API_URL}/options/${encodeURIComponent(ticker)}?expiry=${expiry}`);
        if (!res.ok) throw new Error("Failed to fetch chain");
        
        const data = await res.json();
        tbody.innerHTML = ""; // Clear loading message

        // Render Calls
        data.calls.forEach(opt => appendOptionRow(opt, "CALL"));
        // Render Puts
        data.puts.forEach(opt => appendOptionRow(opt, "PUT"));

    } catch (error) {
        console.error("Error:", error);
        tbody.innerHTML = "<tr><td colspan='9' style='text-align:center; color: var(--sell-red);'>Failed to load options chain. Check ticker and valid expiry date.</td></tr>";
    }
}

function appendOptionRow(opt, type) {
    const tbody = document.getElementById('options-body');
    const tr = document.createElement('tr');
    tr.className = type === "CALL" ? "call-row" : "put-row";
    
    // Helper function to handle clicks on the row to pre-fill the order ticket
    tr.onclick = () => {
        document.getElementById('order-type').value = type;
        document.getElementById('order-strike').value = opt.strike;
        document.getElementById('order-price').value = opt.ask; // Default to asking price for buying
    };
    tr.style.cursor = "pointer";

    tr.innerHTML = `
        <td style="text-align: left; font-weight: bold; color: ${type === 'CALL' ? 'var(--buy-green)' : 'var(--sell-red)'}">${type}</td>
        <td>${opt.strike}</td>
        <td>${opt.bid.toFixed(2)}</td>
        <td>${opt.ask.toFixed(2)}</td>
        <td>${(opt.impliedVolatility * 100).toFixed(1)}%</td>
        <td>${opt.delta}</td>
        <td>${opt.gamma}</td>
        <td>${opt.theta}</td>
        <td>${opt.vega}</td>
    `;
    tbody.appendChild(tr);
}

/// --- 3. Execute Trade ---
async function submitTrade() {
    const msgDiv = document.getElementById("order-message");

    msgDiv.innerText = "Processing...";
    msgDiv.style.color = "var(--text-main)";

    const payload = {
        ticker: document.getElementById("ticker-input").value.toUpperCase(),
        strike: parseFloat(document.getElementById("order-strike").value),
        option_type: document.getElementById("order-type").value,
        expiry: document.getElementById("order-expiry").value,
        action: document.getElementById("order-action").value,
        quantity: parseInt(document.getElementById("order-qty").value),
        price: parseFloat(document.getElementById("order-price").value)
    };

    console.log("Trade Payload:", payload);

    try {
        const res = await fetch(`${API_URL}/trade`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await res.json();

        console.log("Status:", res.status);
        console.log("Response:", data);

        if (res.ok) {
            msgDiv.innerText = data.message || "Trade executed successfully.";
            msgDiv.style.color = "var(--buy-green)";
            fetchPortfolio();
            return;
        }

        let errorMessage = "Unknown error";

        if (typeof data.detail === "string") {
            errorMessage = data.detail;
        } else if (Array.isArray(data.detail)) {
            errorMessage = data.detail
                .map(err => `${err.loc.join(" → ")} : ${err.msg}`)
                .join("\n");
        } else if (data.detail) {
            errorMessage = JSON.stringify(data.detail, null, 2);
        } else {
            errorMessage = JSON.stringify(data, null, 2);
        }

        msgDiv.innerText = errorMessage;
        msgDiv.style.color = "var(--sell-red)";

    } catch (error) {
        console.error(error);

        msgDiv.innerText =
            error.message || "Connection error. Check browser console.";

        msgDiv.style.color = "var(--sell-red)";
    }
}

// --- 4. Event Listeners ---
document.addEventListener('DOMContentLoaded', () => {
    fetchPortfolio();

    document.getElementById('load-chain-btn').addEventListener('click', () => {
        const ticker = document.getElementById('ticker-input').value.toUpperCase();
        const expiry = document.getElementById('chain-expiry').value;
        if(ticker && expiry) {
            fetchOptionsChain(ticker, expiry);
        } else {
            alert("Please provide both Ticker and Expiry Date (YYYY-MM-DD)");
        }
    });

    document.getElementById('submit-order-btn').addEventListener('click', submitTrade);
});

