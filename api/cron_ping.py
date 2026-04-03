import requests
from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # The Render backend URL to keep awake
        BACKEND_URL = "https://finance-api-docker.onrender.com/"
        
        try:
            # Ping the backend
            response = requests.get(BACKEND_URL, timeout=10)
            status_code = response.status_code
            message = "Render backend pinged successfully"
        except Exception as e:
            status_code = 500
            message = f"Failed to ping Render backend: {str(e)}"

        # Prepare JSON response for Vercel logs
        data = {
            "message": message,
            "status": status_code,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
        return
