import os
import requests
import json
import redis
from flask import Flask, request, render_template

app = Flask(__name__)
redis_client = redis.Redis(host="redis", port=6379, decode_responses=True)

def get_geolocation(ip):
    api_key = os.getenv("IPGEO_API_KEY")
    url = f"https://api.ipgeolocation.io/ipgeo?apiKey={api_key}&ip={ip}"
    response = requests.get(url)
    return response.json()

def get_whois(domain):
    api_key = os.getenv("WHOIS_API_KEY")
    url = f"https://api.apilayer.com/whois/check?domain={domain}"
    headers = {"apikey": api_key}
    response = requests.get(url, headers=headers)
    data = response.json()
    return {
        "domain_name": data.get("domain_name", "N/A"),
        "registrar": data.get("registrar", "N/A"),
        "expiry_date": data.get("expiry_date", "N/A"),
        "raw": json.dumps(data, indent=4)
    }

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        query = request.form["query"]
        lookup_type = request.form["lookup_type"]
        cache_key = f"{lookup_type}:{query}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            data = json.loads(cached_result)
            data["cached"] = "True"
        else:
            if lookup_type == "geolocation":
                data = get_geolocation(query)
            else:
                data = {"whois": get_whois(query)}
            redis_client.setex(cache_key, 3600, json.dumps(data))
            data["cached"] = "False"
        data["query"] = query
        data["lookup_type"] = lookup_type
        return render_template("result.html", data=data)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)

