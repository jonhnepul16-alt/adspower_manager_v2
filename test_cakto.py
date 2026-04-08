import requests

url = "https://web-production-373eb.up.railway.app/api/webhook/cakto"
payload = {
    "event": "payment.approved",
    "data": {
        "customer": {
            "email": "jcmendes608@gmail.com"
        }
    }
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response JSON: {response.text}")
except Exception as e:
    print(f"Connection Error: {e}")
