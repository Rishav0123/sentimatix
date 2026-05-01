
import requests
import json

URL = "https://mcp-pv1u.onrender.com/call"
API_KEY = "dev-key-12345"

def test_post():
    print(f"Testing POST to {URL} with api_key param...")
    try:
        payload = {
            "name": "explain_price_change", # Dummy call
            "arguments": {
                "symbol": "TCS",
                "start_date": "2024-01-01",
                "end_date": "2024-01-04"
            }
        }
        response = requests.post(f"{URL}?api_key={API_KEY}", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        print(f"Headers: {response.headers}")
    except Exception as e:
        print(f"Error: {e}")

def test_options():
    print(f"\nTesting OPTIONS to {URL}...")
    try:
        response = requests.options(URL)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
    except Exception as e:
        print(f"Error: {e}")

    test_post()
    test_options()

def test_health():
    print(f"\nTesting GET to {URL.replace('/call', '/health')}...")
    try:
        response = requests.get(URL.replace('/call', '/health'))
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

    test_health()
    # test_post()
    # test_options()

def test_schema():
    print(f"\nTesting GET to {URL.replace('/call', '/openapi.json')}...")
    try:
        response = requests.get(URL.replace('/call', '/openapi.json'))
        print(f"Status Code: {response.status_code}")
        try:
            print(f"Response Keys: {response.json().keys()}")
            print(f"Paths: {json.dumps(response.json().get('paths', {}), indent=2)}")
        except:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_schema()
    test_health()
