import hashlib
import hmac
import json
import urllib
import requests

from urllib.parse import urlencode, quote

from .constants import *
from .helpers import *

class Client(object):
    def __init__(self, key, secret, subaccount=None, timeout=30):
        self._api_key = key
        self._api_secret = secret

    # TODO: FIDA VIP API
    def _build_headers(self, scope, method, endpoint, query=None):
        if query is None:
            query = {}

        headers = {
            'Accept': 'application/json',
            'User-Agent': 'Bonfida-Trader/1.0',
        }

        if scope.lower() == 'private':
            pass

        return headers

    def _build_url(self, scope, method, endpoint, query=None):
        if query is None:
            query = {}

        if scope.lower() == 'private':
            url = f"{PRIVATE_API_URL}/{endpoint}"
        else:
            url = f"{PUBLIC_API_URL}/{endpoint}"

        if method == 'GET':
            return f"{url}?{urlencode(query, True, '/[]')}" if len(query) > 0 else url
        else:
            return url

        if method == 'GET':
            response = requests.get(url, headers=headers)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=query)
        elif method == 'DELETE':
            if query == {}:
                response = requests.delete(url, headers=headers)
            else:
                response = requests.delete(url, headers=headers, json=query)
        else:
            raise NotImplemented("Not implemented request method '%s'" % method)

        http_code_group = str(response.status_code)[0]
        print(http_code_group)
        if http_code_group == '4' or http_code_group == '5':  # 4xx or 5xx error?
            raise ex.HTTPError(f"{response.status_code} {method} {url}", response=response)

        resp_json = response.json()

        if 'data' in resp_json:
            return resp_json['data']
        else:
            return resp_json

    # Public API
    def get_public_all_pairs(self):
        """
        https://docs.bonfida.com/#get-all-pairs

        :return: a list contains all available pairs on the Serum DEX.
        """

        return self._send_request('public', 'GET', f"pairs")


    def get_public_all_recent_trades(self):
        """
        https://serum-api.bonfida.com/trades/all/recent

        :return: a dict/list (pair/address) contains all recent trades
        """

        return self._send_request('public', 'GET', f'trades/all/recent')

    def get_public_recent_trades(self, any):
        """
        https://docs.bonfida.com/#get-recent-trades-by-market-name
        https://docs.bonfida.com/#get-recent-trades-by-market-address

        :param pair: the market pair/address to query
        :return: a dict contains recent trades
        """

        if len(any) > 15:
            endpoint = f'trades/address/{any}'
        else:
            endpoint = f'trades/{any}'

        return self._send_request('public', 'GET', endpoint)

    def get_public_volumes(self, pair):
        """
        https://docs.bonfida.com/#get-volume

        :param pair: the pair to query
        :return: a list contains market volumes
        """

        return self._send_request('public', 'GET', f'volumes/{pair}')

    def get_public_orderbooks(self, pair):
        """
        https://docs.bonfida.com/#get-orderbook

        :param pair: the pair to query
        :return: a dict contains current orderbooks
        """

        return self._send_request('public', 'GET', f'orderbooks/{pair}')

    def get_public_K_lines(self, pair, resolution, startTime=None, endTime=None, limit=1000):
        """
        https://docs.bonfida.com/#get-historical-prices

        :param pair: the pair to query
        :param resolution: window length in seconds. options: 60, 3600, 14400, 86400
        :param startTime: in ms
        :param endTime: in ms
        :param limit: default 1000 MAX 1000
        :return: a dict contains historical ohlc data
        """

        query = {
            'resolution': resolution,
            'limit': limit
        }

        if startTime is not None:
            query.update({'startTime': startTime})
        if endTime is not None:
            query.update({'endTime': endTime})

        return self._send_request('public', 'GET', f'candles/{pair}', query)

    def get_public_all_pools(self):
        """
        https://docs.bonfida.com/#get-all-pools

        :return: a list contains all pools
        """

        return self._send_request('public', 'GET', f'pools')

    def get_public_all_recent_pools(self):
        """
        https://docs.bonfida.com/#get-all-pools

        :return: a list contains all recent pools
        """

        return self._send_request('public', 'GET', f'pools-recent')

    def get_public_single_pool(self, mintA, mintB, startTime=None, endTime=None, limit=1000):
        """
        https://docs.bonfida.com/#get-pool

        :param mintA: Mint address A
        :param mintB: Mint address B
        :param startTime: in ms
        :param endTime: in ms
        :param limit: default 1000 MAX 1000
        :return: a list contains historical data about Serum pools
        """

        query = {'limit': limit}

        if startTime is not None:
            query.update({'startTime': startTime})
        if endTime is not None:
            query.update({'endTime': endTime})

        return self._send_request('public', 'GET', f'pools/{mintA}/{mintB}', query)

    def get_public_pool_trades(self, Source=None, Destination=None, both=None):
        """
        https://docs.bonfida.com/#get-pool-trades

        :param Source: Source coin of the swap
        :param Destination: Destination coin of the swap
        :param both: To retrieve trades from both directions (bool, true or false)

        :return: a list of all/single trades fills from the last 24 hours on the Serum Swap
        """

        query = {}

        if Source is not None:
            query.update({'symbolSource': Source})
        if Destination is not None:
            query.update({'symbolDestination': Destination})
        if both is not None:
            query.update({'bothDirections': both})

        return self._send_request('public', 'GET', f'pools/trades', query)

    def get_public_pools_recent_volumes(self):
        """
        https://docs.bonfida.com/#get-pools-last-24h-volume

        :return: a list of 24 hour volumes on the Serum Swap
        """

        return self._send_request('public', 'GET', f'volumes/recent')

    def get_public_pool_historical_volume(self, mintA, mintB, startTime=None, endTime=None, limit=100):
        """
        https://docs.bonfida.com/#get-pools-historical-volume

        :param mintA: Mint address A
        :param mintB: Mint address B
        :param startTime: in ms
        :param endTime: in ms
        :param limit: default 100 MAX 100
        :return: a list contains historical data about Serum pools
        """

        query = {
            'mintA': mintA,
            'mintB': mintB,
            'limit': limit
            }

        if startTime is not None:
            query.update({'startTime': startTime})
        if endTime is not None:
            query.update({'endTime': endTime})

        return self._send_request('public', 'GET', f'pools/volumes', query)

    def get_public_pool_historical_liquidity(self, mintA, mintB, startTime=None, endTime=None, limit=100):
        """
        https://docs.bonfida.com/#get-pools-historical-liquidity

        :param mintA: Mint address A
        :param mintB: Mint address B
        :param startTime: in ms
        :param endTime: in ms
        :param limit: default 100 MAX 100
        :return: a list contains historical data about Serum pools
        """

        query = {
            'mintA': mintA,
            'mintB': mintB,
            'limit': limit
            }

        if startTime is not None:
            query.update({'startTime': startTime})
        if endTime is not None:
            query.update({'endTime': endTime})

        return self._send_request('public', 'GET', f'pools/liquidity', query)
