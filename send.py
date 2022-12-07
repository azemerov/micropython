import urequests
import ujson


def send_data(temp):
    url =  'https://data.mongodb-api.com/app/data-blzil/endpoint/data/beta/action/insertOne'
    api_key = 'Z6p51gsY6CrdyGkhmLCy3uYHJJCmRWVvoVZHOZqPSfbxTX8u64tZg916BfdWLqXN'
    data = ujson.dumps({"collection": "temperature", "database": "weatherDb", "dataSource": "VespaCluster", "document": {
        "ts": "2022-05-01", "temp": temp}})

    headers = {
            "content-type": "application/json",
            "api-key": api_key,
            "Access-Control-Request-Headers": "*",
            }

    res = urequests.post(url, headers=headers, data=data) #.json()
    return res #['code']

