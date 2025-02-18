#!/usr/bin/env python3
import requests
import json

def fetch(url: str):
    response = requests.get(url)
    return json.loads(response.text)

if __name__ == '__main__':
    url = "https://api.example.com/data"
    data = fetch(url)
    print(json.dumps(data, indent=2))
