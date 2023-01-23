import requests
from typing import NamedTuple

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}


def get(url: str, endpoint: str, params: dict=dict()):
    """Performs HTTP Get Requests"""
    url = f"{url}{endpoint}"
    try:
        response = None
        if params:
            response = requests.get(url=url, headers=headers, params=params)
        else:
            response = requests.get(url=url, headers=headers)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as err:
        print(err)
        return requests.Response


def post(url: str, endpoint: str):
    """Peforms HTTP Post Requests"""
    url = f"{url}{endpoint}"
    try:
        response = requests.post(url=url, headers=headers)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as err:
        print(err)
        return requests.Response

def query(url: str, endpoint: str, params: dict):
    '''Performs a HTTP query request'''
    return  get(url, endpoint, params)
