import os
import json
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import date as dt_date
from ai_handler import get_usage_stats
from database import DB_PATH, get_guilds_count, reset_data

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Zing Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f0f1a; color: #e0e0e0; padding: 20px; }
.container { max-width: 1200px; margin: 0 auto; }
h1 { font-size: 28px; margin-bottom: 8px; color: #fff; }
.subtitle { color: #888; margin-bottom: 24px; }
.range-bar { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
.range-btn { background: #1a1a2e; border: 1px solid #2a2a4a; color: #aaa; padding: 8px 18px; border-radius: 8px; cursor: pointer; font-size: 13px; transition: all .15s; }
.range-btn:hover { border-color: #60a5fa; color: #fff; }
.range-btn.active { background: #60a5fa; color: #fff; border-color: #60a5fa; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
.card { background: #1a1a2e; border-radius: 12px; padding: 20px; border: 1px solid #2a2a4a; }
.card h3 { font-size: 13px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
.card .value { font-size: 32px; font-weight: 700; color: #fff; }
.card .value.green { color: #4ade80; }
.card .value.yellow { color: #fbbf24; }
.card .value.red { color: #f87171; }
.card .value.blue { color: #60a5fa; }
.card .sub { font-size: 12px; color: #666; margin-top: 4px; }
.charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 16px; margin-bottom: 24px; }
.chart-box { background: #1a1a2e; border-radius: 12px; padding: 20px; border: 1px solid #2a2a4a; }
.chart-box h3 { font-size: 14px; color: #aaa; margin-bottom: 12px; }
table { width: 100%; border-collapse: collapse; }
table th { text-align: left; padding: 10px 12px; font-size: 12px; color: #888; text-transform: uppercase; border-bottom: 1px solid #2a2a4a; }
table td { padding: 10px 12px; border-bottom: 1px solid #1a1a2e; font-size: 14px; }
table tr:hover { background: #1a1a2e; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; }
.badge.new { background: #1e3a5f; color: #60a5fa; }
.badge.chatting { background: #1e3a2f; color: #4ade80; }
.badge.greeting { background: #3a2e1e; color: #fbbf24; }
.badge.dm_blocked { background: #3a1e1e; color: #f87171; }
</style>
</head>
<body>
<div class="container">
<h1>Zing Dashboard</h1>
<p class="subtitle" id="subtitle">Loading...</p>
<div class="range-bar">
  <button class="range-btn" onclick="setRange('today')">Today</button>
  <button class="range-btn" onclick="setRange('7d')">7 Days</button>
  <button class="range-btn active" onclick="setRange('14d')">14 Days</button>
  <button class="range-btn" onclick="setRange('30d')">30 Days</button>
</div>
<div class="cards" id="cards"></div>
<div class="charts" id="charts"></div>
<h2 style="margin-bottom:12px;font-size:18px;color:#aaa;">Recent Leads</h2>
<div style="background:#1a1a2e;border-radius:12px;border:1px solid #2a2a4a;overflow-x:auto;" id="leads-table"></div>
<div style="margin-top:24px;display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
  <button onclick="resetData('today')" style="background:#3a1e1e;border:1px solid #f87171;color:#f87171;padding:10px 24px;border-radius:8px;cursor:pointer;font-size:13px;">Reset Today Stats</button>
  <button onclick="resetData('full')" style="background:#3a1e1e;border:1px solid #f87171;color:#f87171;padding:10px 24px;border-radius:8px;cursor:pointer;font-size:13px;">Full Reset (all data)</button>
</div>
</div>
<script>
let chart1, chart2, currentRange = '14d';
async function load() {
  const r = await fetch('/api/stats?range=' + currentRange);
  const d = await r.json();
  document.getElementById('subtitle').textContent = 'Last updated: ' + new Date().toLocaleString();
  renderCards(d);
  renderCharts(d);
  renderLeads(d.leads || []);
}
function setRange(r) {
  currentRange = r;
  document.querySelectorAll('.range-btn').forEach(b => b.classList.toggle('active', b.textContent.replace(' ','') === ({today:'Today', '7d':'7Days', '14d':'14Days', '30d':'30Days'})[r]));
  load();
}
function renderCards(d) {
  const cards = [
    { label: 'AI Calls Today', value: d.usage?.today || 0, cls: 'blue', sub: 'out of ~1500 daily limit' },
    { label: 'Tokens Used Today', value: (d.usage?.tokens || 0).toLocaleString(), cls: 'green', sub: '~' + Math.round((d.usage?.tokens || 0) * 0.00025) + '¢ cost' },
    { label: 'Errors Today', value: d.usage?.errors || 0, cls: d.usage?.errors > 0 ? 'red' : 'green', sub: 'last 24h' },
    { label: 'Total Leads', value: d.totalLeads || 0, cls: 'blue', sub: 'all time' },
    { label: 'Active Conversations', value: d.activeChats || 0, cls: 'yellow', sub: 'chatting stage' },
    { label: 'Servers', value: d.servers || 0, cls: 'blue', sub: 'connected guilds' },
  ];
  document.getElementById('cards').innerHTML = cards.map(c =>
    `<div class="card"><h3>${c.label}</h3><div class="value ${c.cls}">${c.value}</div><div class="sub">${c.sub}</div></div>`
  ).join('');
}
function renderCharts(d) {
  const logs = d.logs || [];
  const hourly = {};
  const daily = {};
  logs.forEach(l => {
    if (l.timestamp) {
      daily[l.timestamp.slice(0,10)] = (daily[l.timestamp.slice(0,10)] || 0) + 1;
      hourly[l.timestamp.slice(11,13)] = (hourly[l.timestamp.slice(11,13)] || 0) + 1;
    }
  });
  const hours = Array.from({length:24},(_,i)=>String(i).padStart(2,':00'));
  const hv = hours.map(h => hourly[h.slice(0,2)] || 0);
  const days = Object.keys(daily);
  const dv = days.map(d => daily[d] || 0);
  const rangeLabel = {today:'Today', '7d':'7 Days', '14d':'14 Days', '30d':'30 Days'}[currentRange] || 'Period';

  document.getElementById('charts').innerHTML =
    '<div class="chart-box"><h3>Requests by Hour — ' + rangeLabel + '</h3><canvas id="chart-hourly"></canvas></div>' +
    '<div class="chart-box"><h3>Daily Requests — ' + rangeLabel + '</h3><canvas id="chart-daily"></canvas></div>';

  setTimeout(() => {
    if (chart1) chart1.destroy();
    if (chart2) chart2.destroy();
    chart1 = new Chart(document.getElementById('chart-hourly'), {
      type: 'bar', data: { labels: hours, datasets: [{ label: 'Requests', data: hv, backgroundColor: '#60a5fa', borderRadius: 4 }] },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: '#2a2a4a' } }, x: { grid: { display: false }, ticks: { maxRotation: 0, font: { size: 10 } } } } }
    });
    chart2 = new Chart(document.getElementById('chart-daily'), {
      type: 'line', data: { labels: days, datasets: [{ label: 'Requests', data: dv, borderColor: '#4ade80', backgroundColor: 'rgba(74,222,128,0.1)', fill: true, tension: 0.3 }] },
      options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, grid: { color: '#2a2a4a' } }, x: { grid: { display: false } } } }
    });
  }, 100);
}
function renderLeads(leads) {
  if (!leads.length) { document.getElementById('leads-table').innerHTML = '<p style="padding:20px;color:#666;">No leads yet</p>'; return; }
  document.getElementById('leads-table').innerHTML =
    '<table><thead><tr><th>User</th><th>Stage</th><th>Score</th><th>Interest</th><th>Joined</th></tr></thead><tbody>' +
    leads.map(l => '<tr><td>' + (l.username||'?') + '</td><td><span class="badge ' + (l.stage||'new').replace(' ','').toLowerCase() + '">' + (l.stage||'new') + '</span></td><td>' + (l.score||'—') + '</td><td>' + (l.interest||'—') + '</td><td>' + (l.joined_at||'').slice(0,10) + '</td></tr>').join('') +
    '</tbody></table>';
}
async function resetData(mode) {
  if (!confirm(mode === 'full' ? 'Delete ALL data? This cannot be undone!' : 'Reset today\\'s stats?')) return;
  await fetch('/api/reset', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({mode}) });
  load();
}
load();
setInterval(load, 30000);
</script>
</body>
</html>"""

class DashboardHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/health":
            self._send_text(200, "text/plain", b"Zing AI Concierge is running!")
        elif self.path.startswith("/dashboard"):
            self._send_text(200, "text/html; charset=utf-8", DASHBOARD_HTML.encode("utf-8"))
        elif self.path.startswith("/api/stats"):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            range_days = {"today": 1, "7d": 7, "14d": 14, "30d": 30}.get((qs.get("range") or ["14d"])[0], 1)
            self._send_json(self._build_stats(range_days))
        else:
            self._send_text(404, "text/plain", b"Not found")

    def do_POST(self):
        if self.path == "/api/reset":
            from ai_handler import usage, _usage_log
            from datetime import date as dt_date
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length) if length else b"{}"
            try:
                data = json.loads(body)
            except:
                data = {}
            mode = data.get("mode", "today")
            reset_data(mode)
            usage.update({"today": 0, "tokens": 0, "errors": 0, "date": str(dt_date.today())})
            _usage_log.clear()
            self._send_json({"ok": True, "mode": mode})
        else:
            self._send_text(404, "text/plain", b"Not found")

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

    def _send_text(self, code, content_type, body):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, data):
        body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self._send_text(200, "application/json; charset=utf-8", body)

    def _build_stats(self, range_days=14):
        usage, logs = get_usage_stats(range_days)
        stats = {"usage": usage, "logs": logs, "totalLeads": 0, "activeChats": 0, "servers": 0, "leads": [], "range": range_days}
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            stats["totalLeads"] = conn.execute("SELECT COUNT(*) as c FROM leads").fetchone()["c"]
            stats["activeChats"] = conn.execute("SELECT COUNT(*) as c FROM leads WHERE stage='chatting' OR stage='engaged'").fetchone()["c"]
            stats["servers"] = get_guilds_count()
            rows = conn.execute("SELECT * FROM leads ORDER BY updated_at DESC LIMIT 20").fetchall()
            stats["leads"] = [dict(r) for r in rows]
            conn.close()
        except:
            pass
        return stats

def start_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DashboardHandler)
    print(f"Dashboard: http://0.0.0.0:{port}/dashboard")
    server.serve_forever()
