import gzip
import os
import datetime
import json
import requests
from threading import Thread
import time
import random
import sys
import doctest
from decimal import Decimal, Context, ROUND_HALF_EVEN
from exchanges_api import DEFAULT_EXCHANGE, EXCHANGES

class OrderBook(Thread):
    """This class handle read and write methods for bitcoin data.

    Args:
        price_shift (int, optional): Number of digits to shift in price. Defaults to 2.
        price_num_digits (int, optional): Max number of digits to keep in price. Defaults to None.
        amount_shift (int, optional): Number of digits to shift in amount. Defaults to 8.
        amount_num_digits (int, optional): Max number of digits to keep in amount. Defaults to 3.
        exchange (str, optional): Exchange where data comes from (needs to be inside EXCHANGES attr). Defaults to None.

    Attributes:
        price_shift (int): Number of digits to shift in price. 
        price_num_digits (int): Max number of digits to keep in price. 
        amount_shift (int): Number of digits to shift in amount.
        amount_num_digits (int): Max number of digits to keep in amount.
        orderbook_dict (dict): Dict representing a colletion of orderbooks (all bid and asks for a given timestamp).
        exchange (str): Current exchange.
        EXCHANGES (dict): Dict of available exchanges.
    """
    
    DEFAULT_EXCHANGE = DEFAULT_EXCHANGE

    EXCHANGES = EXCHANGES
    
    def __init__(self, exchange = DEFAULT_EXCHANGE, price_num_digits=8, amount_num_digits=3):
        super(OrderBook, self).__init__()
        self._keep_running = False
        self.price_num_digits = price_num_digits
        self.amount_num_digits = amount_num_digits
        self.orderbook_dict = {}
        self.exchange = exchange if exchange in self.EXCHANGES.keys() else self.DEFAULT_EXCHANGE

    def get_json(self):
        """Returns a dict representing bids/asks for the current exchange."""
        url = self.EXCHANGES[self.exchange]['url']
        params = self.EXCHANGES[self.exchange]['params']
        delay = self.EXCHANGES[self.exchange]['delay']
        return requests.get(url, params=params, timeout=delay).json() if url else ''

    def _add_orderbook(self, utcepoch, standard_orderbook):
        """Add an entry to the orderbook dict.

        Args:
            utcepoch (int): A integer representing an epoch.
            standard_orderbook (str): A standard orderbook.
        """
        self.orderbook_dict[utcepoch] = standard_orderbook

    def _convert_to_standard_orderbook(self, orderbook_json):
        """Returns a standard orderbook representing bids/asks for the current exchange."""
        asks  = self.EXCHANGES[self.exchange]['asks'](orderbook_json)
        bids  = self.EXCHANGES[self.exchange]['bids'](orderbook_json)
        return {'asks':asks, 'bids':bids}
        
    def fetch_one(self):
        """Fetch one snapshot of the current exchange's orderbook and add It to the orderbook dict."""
        try:
            orderbook_json = self.get_json()
            standard_orderbook = self._convert_to_standard_orderbook(orderbook_json)
            utctimestamp = datetime.datetime.utcnow()
            utcepoch = int(utctimestamp.strftime('%s'))
            self._add_orderbook(utcepoch, standard_orderbook)
        except Exception as err:
            print('ERR:', self.exchange, str(datetime.datetime.utcnow()), err)
        
    def _num_to_tuple(self, n, shift=0, max_num_digits=None):
        """Function to convert any number in it's normalized tuple.
        
        Args:
            n (float or str): Number to be converted.
            shift (int): Number of digits to be shifted.
            max_num_digits (int): Max number of digits to keep.
        
        Returns:
            DecimalTuple(sign, digits, exponent): A tuple representing the number.

        Examples:
            >>> c = OrderBook()
            >>> c._num_to_tuple('001')
            DecimalTuple(sign=0, digits=(1,), exponent=0)
            >>> c._num_to_tuple('00300.00')
            DecimalTuple(sign=0, digits=(3,), exponent=2)
            >>> c._num_to_tuple(008.003)
            DecimalTuple(sign=0, digits=(8, 0, 0, 3), exponent=-3)
            >>> c._num_to_tuple('500.43210000', max_num_digits=3)
            DecimalTuple(sign=0, digits=(5,), exponent=2)
            >>> c._num_to_tuple(500.43210000, max_num_digits=4, shift=1)
            DecimalTuple(sign=0, digits=(5, 0, 0, 4), exponent=0)
            >>> c._num_to_tuple('-00000000.0056000000', max_num_digits=2, shift=4)
            DecimalTuple(sign=1, digits=(5, 6), exponent=0)
            >>> c._num_to_tuple('-0000.0058064171659814651465', max_num_digits=1, shift=4)
            DecimalTuple(sign=1, digits=(6,), exponent=1)
        """
        number = Decimal(str(n)).normalize().as_tuple()
        l = len(number.digits)
        max_num_digits = max_num_digits if max_num_digits else l
        context = Context(prec=max_num_digits, rounding=ROUND_HALF_EVEN)
        digits_round = context.create_decimal((0, number.digits, -l)).normalize().as_tuple()
        return Decimal(
                (number.sign, 
                 digits_round.digits, 
                 number.exponent+digits_round.exponent+l+shift)
               ).normalize().as_tuple()
        
    def _textfy_orderbook_dict(self, epoch_list=None):
        """Returns a compressed text of the selected timestamps of a orderbook_dict.
        
        Args:
            epoch_list (list[int]): A list of valid epoch times from the orderbook keys.
        
        Returns:
            Compressed orderbook colletion(str): A text containing a compressed orderbook_dict.
        """
        price_shift = self.EXCHANGES[self.exchange]['best_shift']['price']
        amount_shift = self.EXCHANGES[self.exchange]['best_shift']['amount']
        orderbook_text = ""
        if not epoch_list:
            epoch_list = self.orderbook_dict.keys()
        epoch_list = sorted(epoch_list)
        for epoch_time in epoch_list:
            if epoch_time not in self.orderbook_dict.keys():
                continue
            orderbook_text += str(epoch_time)
            orderbook_text += '|'
            orderbook_text += str(len(self.orderbook_dict[epoch_time]['asks']))
            orderbook_text += ' '
            orderbook_text += str(len(self.orderbook_dict[epoch_time]['bids']))
            orderbook_text += '|'
            for type_order in ['asks', 'bids']:
                last_price = 0
                for order in self.orderbook_dict[epoch_time][type_order]:
                    current_price = order[0]
                    price = self._num_to_tuple(current_price-last_price, price_shift, self.price_num_digits)
                    last_price = current_price
                    amount = self._num_to_tuple(order[1], amount_shift, self.amount_num_digits)
                    orderbook_text += '-' if price.sign else ''
                    orderbook_text += ''.join(map(str,price.digits))
                    if price.exponent==0:
                        orderbook_text += ''
                    elif price.exponent==1:
                        orderbook_text += '0'
                    else:
                        orderbook_text += 'e'+str(price.exponent)
                    orderbook_text += ','
                    orderbook_text += '-' if amount.sign else ''
                    orderbook_text += ''.join(map(str,amount.digits))
                    if amount.exponent==0:
                        orderbook_text += ''
                    elif amount.exponent==1:
                        orderbook_text += '0'
                    else:
                        orderbook_text += 'e'+str(amount.exponent)
                    orderbook_text += ' '
                orderbook_text = orderbook_text[:-1] + '|'
            orderbook_text = orderbook_text[:-1] + '\n'
        return orderbook_text
    
    def _compress_bin(self, text):
        """Returns a gzip compressed binary from a text.

        Args:
            text (str): Text to be compressed.
        """
        return gzip.compress(bytes(text, 'utf-8'))
    
    def save_orderbook(self, base_path=None):
        """Save orderbook dict to a file."""
        if not base_path:
            base_path = './orderbook'
        base_path = os.path.join(base_path, self.exchange)
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        epoch_list = sorted(self.orderbook_dict.keys())
        dates_dict = {str(datetime.datetime.fromtimestamp(k).date()):[] for k in epoch_list}
        for k in epoch_list:
            tstr = str(datetime.datetime.fromtimestamp(k).date())
            dates_dict[tstr].append(k)
        for dt in dates_dict.keys():
            dt_epoch_list = dates_dict[dt]
            orderbook_text = self._textfy_orderbook_dict(dt_epoch_list)
            out = self._compress_bin(orderbook_text)
            filename = '{}.gz'.format(dt)
            file_path = os.path.join(base_path, filename)
            aw = 'ab' if os.path.exists(file_path) else 'wb'
            with open( file_path, aw ) as f:
                f.write(out)

    def _clean_orderbook_dict(self):
        """Clean the orderbook dict."""
        self.orderbook_dict = {}
    
    def flush_orderbook(self, base_path=None):
        """Save orderbook dict to a file and clean the orderbook dict."""
        self.save_orderbook(base_path)
        self._clean_orderbook_dict()
    
    def read_orderbook_files(self, filepath_list):
        """Read orderbook files and converts It to a standard orderbook.

        Args:
            filepath_list (list[str]): List of paths to valid orderbook files.
        """
        pass

    def update_exchange(self, exchange):
        """Update current exchange.
        
        Args:
            exchange (str): A valid exchange.
        """
        if exchange!=self.exchange:
            self._clean_orderbook_dict()
        self.exchange = exchange if exchange in self.EXCHANGES.keys() else self.DEFAULT_EXCHANGE

    def run(self):
        """Set thread to run and fetch orderbook for current exchange."""
        self._keep_running = True
        delay = self.EXCHANGES[self.exchange]['delay']
        time.sleep(random.randint(1, delay))
        while self._keep_running:
            print(self.exchange, '-', str(datetime.datetime.utcnow()))
            self.fetch_one()
            if random.randint(1, 100)<=10:
                print('> Saving', self.exchange)
                self.flush_orderbook()
            time.sleep(delay)
        print('Finishing', self.exchange)

    def stop(self):
        """Stop fetching orderbook."""
        self._keep_running = False
        
    def terminate(self):
        """Stop fetching orderbook and save current status."""
        self.stop()
        self.flush_orderbook()


if __name__=="__main__":
    if len(sys.argv)>1:
        orderbook_instances = {}
        for k in sys.argv[1:]:
            exchange = k if k in OrderBook.EXCHANGES.keys() else 'test'
            orderbook_instances[exchange] = OrderBook(exchange)
    else:
        orderbook_instances = {k:OrderBook(k) for k in OrderBook.EXCHANGES.keys() if k!='test'}

    print(list(orderbook_instances.keys()))
    cmd = ''
    running = False
    print('Starting:')
    try:
        while True:
            if cmd=='r' and not running:
                running = True
                print('Running all')
                for k in orderbook_instances.keys():
                    orderbook_instances[k].start()
            if cmd=='q':
                print('Exiting')
                for k in orderbook_instances.keys():
                    orderbook_instances[k].terminate()
                sys.exit()
            if cmd=='t':
                doctest.testmod(verbose=True)
            cmd = input()
    except:
        for k in orderbook_instances.keys():
            orderbook_instances[k].terminate()
        sys.exit()
