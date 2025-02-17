import os
import requests
import redis
from flask import Flask, request, render_template, jsonify

app = Flask(__name__)

# Fetch API keys from environment variables
IP_GEOLOCATION_API_KEY = os.getenv("IP_GEOLOCATION_API_KEY")
WHOIS_API_KEY = os.getenv("WHOIS_API_KEY")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def get_ip_geolocation(ip):
    """Fetch IP geolocation data with caching."""
    if cache.exists(ip):
        data = cache.get(ip)
        return {**eval(data), "cached": "Yes"}

    url = f"https://api.ipgeolocation.io/ipgeo?apiKey={IP_GEOLOCATION_API_KEY}&ip={ip}"
    response = requests.get(url)
    data = response.json()
    data["cached"] = "No"
    
    # Store in cache
    cache.set(ip, str(data), ex=3600)  # Cache for 1 hour
    return data

def get_whois_data(ip):
    """Fetch Whois data."""
    url = f"https://api.apilayer.com/whois/query?domain={ip}"
    headers = {"apikey": WHOIS_API_KEY}
    response = requests.get(url, headers=headers)
    return response.json()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        ip = request.form.get("ip")
        if ip:
            return render_template("result.html", data=get_ip_geolocation(ip), whois=get_whois_data(ip))
    return render_template("index.html")

@app.route("/api/<ip>")
def api_lookup(ip):
    return jsonify({"geolocation": get_ip_geolocation(ip), "whois": get_whois_data(ip)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

