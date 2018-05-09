import requests

DEFAULT_EXCHANGE = 'bitstamp'

EXCHANGES = {
    'bitstamp':{
        'url':'http://www.bitstamp.net/api/order_book/',
        'params':None,
        'best_shift':{'price':2, 'amount':8},
        'delay':180,
        'pair':{'BTC','USD'},
        'asks':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['asks']]),
        'bids':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['bids']], reverse=True),
    },
    'mercado_bitcoin':{
        'url':'https://www.mercadobitcoin.com.br/api/orderbook/',
        'params':None,
        'best_shift':{'price':5, 'amount':5},
        'delay':300,
        'pair':{'BTC','BRL'},
        'asks':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['asks']]),
        'bids':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['bids']], reverse=True),
    },
    'okcoin':{
        'url':'https://www.okcoin.com/api/v1/depth.do',
        'params':{'symbol':'btc_usd'},
        'best_shift':{'price':2, 'amount':8},
        'delay':180,
        'pair':{'BTC','USD'},
        'asks':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['asks']]),
        'bids':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['bids']], reverse=True),
    },
    'korbit':{
        'url':'https://api.korbit.co.kr/v1/orderbook',
        'params':None,
        'best_shift':{'price':-2, 'amount':5},
        'delay':180,
        'pair':{'BTC','KRW'},
        'asks':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['asks']]),
        'bids':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['bids']], reverse=True),
    },
    'itbit':{
        'url':'https://api.itbit.com/v1/markets/XBTUSD/order_book',
        'params':None,
        'best_shift':{'price':2, 'amount':4},
        'delay':180,
        'pair':{'BTC','USD'},
        'asks':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['asks']]),
        'bids':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['bids']], reverse=True),
    },
    'bitfinex':{
        'url':'https://api.bitfinex.com/v1/book/btcusd',
        'params':None,
        'best_shift':{'price':2, 'amount':4},
        'delay':180,
        'pair':{'BTC','USD'},
        'asks':lambda d:sorted([[float(t['price']), float(t['amount'])] for t in d['asks']]),
        'bids':lambda d:sorted([[float(t['price']), float(t['amount'])] for t in d['bids']], reverse=True),
    },
    'hitbtc':{
        'url':'https://api.hitbtc.com/api/1/public/BTCUSD/orderbook',
        'params':None,
        'best_shift':{'price':2, 'amount':2},
        'delay':180,
        'pair':{'BTC','USD'},
        'asks':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['asks']]),
        'bids':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['bids']], reverse=True),
    },
    'poloniex':{#poloniex has much more pairs!, problem of decimals on price
        'url':'https://poloniex.com/public',
        'params':{'command':'returnOrderBook',
                'currencyPair':'USDT_BTC',
                'depth':'6000'},
        'best_shift':{'price':2, 'amount':8},
        'delay':120,
        'pair':{'BTC','USD'},
        'asks':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['asks']]),
        'bids':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['bids']], reverse=True),
    },
    'kraken':{#kraken has much more pairs!
        'url':'https://api.kraken.com/0/public/Depth',
        'params':{'pair':'XBTUSD'},
        'best_shift':{'price':2, 'amount':3},
        'delay':180,
        'pair':{'BTC','USD'},
        'asks':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['result']['XXBTZUSD']['asks']]),
        'bids':lambda d:sorted([[float(t[0]), float(t[1])] for t in d['result']['XXBTZUSD']['bids']], reverse=True),
    },
    'coindesk':{#NOT ORDERBOOK! ONLY LAST TICK
        'url':'https://api.coindesk.com/v1/bpi/currentprice/btcusd',
        'params':None,
        'best_shift':{'price':4, 'amount':0},
        'delay':120,
        'pair':{'BTC','USD'},
        'asks':lambda d:sorted([[float(d['bpi']['USD']['rate_float']), 1.0]]),
        'bids':lambda d:sorted([[float(d['bpi']['USD']['rate_float']), 1.0]]),
    },
    'test':{
        'url':None,
        'params':None,
        'best_shift':{'price':2, 'amount':8},
        'delay':2,
        'pair':{'BTC','USD'},
        'asks':lambda d:[[6563.59, 1.61],[6563.62, 1.5],[6571.79, 1.8],[6571.8, 0.01]],
        'bids':lambda d:[[6559.9, 0.02],[6559.62, 0.02],[6559.61, 0.2],[6558.1, 0.01]],
    },
}

def get_json(exchange):
    """Returns a dict representing bids/asks for the current exchange."""
    url = EXCHANGES[exchange]['url']
    params = EXCHANGES[exchange]['params']
    delay = EXCHANGES[exchange]['delay']
    return requests.get(url, params=params, timeout=delay).json() if url else ''
