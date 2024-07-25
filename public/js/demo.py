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

#"20220228_110536_49_2426,20230227_100512_06_2449"
# To download
json_data2 = {
  "api_key": "PLAKabb0ed6e8a964c6591391d8e8bfa0980",
  "item_type": "PSScene",
  "item_list": "20220228_110536_49_2426",
  "geometry": "[[-4.7051044161091555, 40.665345045431366], [-4.68694032067957, 40.665611922383825], [-4.687289043836125, 40.679443353911786], [-4.705456889722511, 40.6791763474491], [-4.7051044161091555, 40.665345045431366]]",
  "order_dir": "/home/tidop/Descargas",
  "product_bundle": "analytic_sr_udm2"
}



