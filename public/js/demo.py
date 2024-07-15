import requests

url = 'http://127.0.0.1:8000'

json_data = {
    "api_key": "PLAKe989a4955bb2438989b94eda796179f3",
    "geometry_json": "[[-122.38405200618716, 40.783437481832124], [-122.38379616905675, 40.81111016511891], [-122.34737496864368, 40.81090989944981], [-122.34764592468271, 40.7832374103324], [-122.38405200618716, 40.783437481832124]]",
    "item_type": "PSScene",
    "start_date": "2019-01-01",
    "end_date": "2019-01-10",
    "cloud_cover": 0.5,
    "asset": "ortho_analytic_4b_sr"}

response = requests.post(url + "/planet/search", json=json_data)
print(response.json())

