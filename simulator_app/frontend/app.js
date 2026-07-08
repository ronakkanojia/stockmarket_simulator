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

// --- 2. Fetch Valid Expiries for a Ticker and Populate the Dropdown ---
async function fetchExpiries(ticker) {
    const select = document.getElementById('chain-expiry');
    select.innerHTML = "<option value=''>Loading expiries...</option>";
    select.disabled = true;

    try {
        const res = await fetch(`${API_URL}/options/${encodeURIComponent(ticker)}/expiries`);
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Failed to fetch expiries");
        }

        if (!data.expiries || data.expiries.length === 0) {
            select.innerHTML = "<option value=''>No expiries found</option>";
            return;
        }

        select.innerHTML = data.expiries
            .map(date => `<option value="${date}">${date}</option>`)
            .join("");
        select.disabled = false;

        // Auto-load the chain for the nearest expiry
        fetchOptionsChain(ticker, data.expiries[0]);
    } catch (error) {
        console.error("Error fetching expiries:", error);
        select.innerHTML = "<option value=''>Failed to load expiries</option>";
    }
}

// --- 3. Fetch and Display Options Chain ---
async function fetchOptionsChain(ticker, expiry) {
    const tbody = document.getElementById('options-body');

    if (!expiry) {
        tbody.innerHTML = "<tr><td colspan='9' style='text-align:center;'>Pick an expiry date above.</td></tr>";
        return;
    }

    tbody.innerHTML = "<tr><td colspan='9' style='text-align:center;'>Loading data from yfinance...</td></tr>";

    try {
        const res = await fetch(`${API_URL}/options/${encodeURIComponent(ticker)}?expiry=${expiry}`);
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || "Failed to fetch chain");
        }

        tbody.innerHTML = ""; // Clear loading message

        if (data.calls.length === 0 && data.puts.length === 0) {
            tbody.innerHTML = "<tr><td colspan='9' style='text-align:center;'>No strikes returned for this expiry.</td></tr>";
            return;
        }

        // Render Calls
        data.calls.forEach(opt => appendOptionRow(opt, "CALL"));
        // Render Puts
        data.puts.forEach(opt => appendOptionRow(opt, "PUT"));

    } catch (error) {
        console.error("Error:", error);
        tbody.innerHTML = `<tr><td colspan='9' style='text-align:center; color: var(--sell-red);'>${error.message || "Failed to load options chain."}</td></tr>`;
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

    // Greeks can be null now (illiquid strikes with no usable IV) — show a dash instead of crashing.
    const fmt = (v, digits = 2) => (v === null || v === undefined) ? "—" : Number(v).toFixed(digits);
    const ivDisplay = (opt.impliedVolatility === null || opt.impliedVolatility === undefined)
        ? "—"
        : `${(opt.impliedVolatility * 100).toFixed(1)}%`;

    tr.innerHTML = `
        <td style="text-align: left; font-weight: bold; color: ${type === 'CALL' ? 'var(--buy-green)' : 'var(--sell-red)'}">${type}</td>
        <td>${opt.strike}</td>
        <td>${fmt(opt.bid)}</td>
        <td>${fmt(opt.ask)}</td>
        <td>${ivDisplay}</td>
        <td>${fmt(opt.delta, 3)}</td>
        <td>${fmt(opt.gamma, 4)}</td>
        <td>${fmt(opt.theta, 3)}</td>
        <td>${fmt(opt.vega, 3)}</td>
    `;
    tbody.appendChild(tr);
}

/// --- 4. Execute Trade ---
async function submitTrade() {
    const msgDiv = document.getElementById("order-message");

    msgDiv.innerText = "Processing...";
    msgDiv.style.color = "var(--text-main)";

    const payload = {
        ticker: document.getElementById("ticker-input").value.toUpperCase(),
        strike: parseFloat(document.getElementById("order-strike").value),
        option_type: document.getElementById("order-type").value,
        expiry: document.getElementById("chain-expiry").value,
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

// --- 5. Event Listeners ---
document.addEventListener('DOMContentLoaded', () => {
    fetchPortfolio();

    document.getElementById('load-chain-btn').addEventListener('click', () => {
        const ticker = document.getElementById('ticker-input').value.toUpperCase();
        if (!ticker) {
            alert("Please provide a ticker first.");
            return;
        }
        fetchExpiries(ticker);
    });

    document.getElementById('chain-expiry').addEventListener('change', () => {
        const ticker = document.getElementById('ticker-input').value.toUpperCase();
        const expiry = document.getElementById('chain-expiry').value;
        if (ticker && expiry) {
            fetchOptionsChain(ticker, expiry);
        }
    });

    document.getElementById('submit-order-btn').addEventListener('click', submitTrade);
});