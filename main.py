import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from bot import bot

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Zing AI Concierge is running!")

def start_http():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"Health server on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    print("Starting Zing...")
    t = threading.Thread(target=start_http, daemon=True)
    t.start()
    bot.run(os.getenv("DISCORD_TOKEN"))
