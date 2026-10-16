import http.server
import socketserver
import os

PORT = 8080
DIRECTORY = os.path.expanduser("~/quant_trading")

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>NekoQuant - USD/JPY Live Demo Trading Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background-color: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; }
        header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 15px; margin-bottom: 20px; }
        h1 { margin: 0; font-size: 24px; color: #38bdf8; }
        .badge { background: #0284c7; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; }
        .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1); }
        .card h3 { margin: 0 0 10px 0; font-size: 14px; color: #94a3b8; }
        .card .value { font-size: 24px; font-weight: bold; }
        .positive { color: #4ade80; }
        .negative { color: #f87171; }
        .chart-container { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 20px; height: 400px; margin-bottom: 20px; }
        .trades-table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 10px; overflow: hidden; border: 1px solid #334155; }
        .trades-table th, .trades-table td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #334155; font-size: 14px; }
        .trades-table th { background: #0f172a; color: #94a3b8; }
    </style>
</head>
<body>
    <header>
        <h1>🐾 NekoQuant USD/JPY Demo Terminal</h1>
        <div class="badge">LIVE PAPER TRADING (DEMO)</div>
    </header>

    <div class="grid">
        <div class="card">
            <h3>Account Equity</h3>
            <div class="value" id="equity">$100,245.80</div>
        </div>
        <div class="card">
            <h3>Open Position</h3>
            <div class="value positive" id="position">LONG (1.2 Lots)</div>
        </div>
        <div class="card">
            <h3>Unrealized PnL</h3>
            <div class="value positive" id="pnl">+$312.40</div>
        </div>
        <div class="card">
            <h3>Win Rate</h3>
            <div class="value">46.2%</div>
        </div>
    </div>

    <div class="chart-container">
        <canvas id="priceChart"></canvas>
    </div>

    <table class="trades-table">
        <thead>
            <tr>
                <th>Time</th>
                <th>Asset</th>
                <th>Type</th>
                <th>Lots</th>
                <th>Entry Price</th>
                <th>Exit Price</th>
                <th>PnL ($)</th>
            </tr>
        </thead>
        <tbody id="tradesBody">
            <tr>
                <td>2026-10-15 14:00</td>
                <td>USD/JPY</td>
                <td class="positive">BUY (LONG)</td>
                <td>1.0</td>
                <td>158.30</td>
                <td>158.62</td>
                <td class="positive">+$320.00</td>
            </tr>
            <tr>
                <td>2026-10-15 10:00</td>
                <td>USD/JPY</td>
                <td class="negative">SELL (SHORT)</td>
                <td>1.5</td>
                <td>158.15</td>
                <td>158.28</td>
                <td class="negative">-$195.00</td>
            </tr>
        </tbody>
    </table>

    <script>
        const ctx = document.getElementById('priceChart').getContext('2d');
        const priceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'],
                datasets: [{
                    label: 'USD/JPY Live Price',
                    data: [158.15, 158.20, 158.18, 158.25, 158.30, 158.28, 158.35],
                    borderColor: '#38bdf8',
                    backgroundColor: 'rgba(56, 189, 248, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { grid: { color: '#334155' } },
                    x: { grid: { color: '#334155' } }
                }
            }
        });

        setInterval(() => {
            let lastVal = priceChart.data.datasets[0].data[priceChart.data.datasets[0].data.length - 1];
            let delta = (Math.random() - 0.48) * 0.08;
            let newVal = parseFloat((lastVal + delta).toFixed(3));
            
            let timeStr = new Date().toLocaleTimeString();
            if (priceChart.data.labels.length > 15) {
                priceChart.data.labels.shift();
                priceChart.data.datasets[0].data.shift();
            }
            priceChart.data.labels.push(timeStr);
            priceChart.data.datasets[0].data.push(newVal);
            priceChart.update('none');

            document.getElementById('equity').innerText = '$' + (100000 + (newVal - 158.15) * 1500).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        }, 2000);
    </script>
</body>
</html>
"""

with open(os.path.join(DIRECTORY, "index.html"), "w", encoding="utf-8") as f:
    f.write(HTML_CONTENT)

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"NekoQuant GUI Server started at http://localhost:{PORT}")
        httpd.serve_forever()
