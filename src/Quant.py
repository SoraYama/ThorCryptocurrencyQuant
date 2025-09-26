"""
    策略会调用本地的Mongodb数据库，在运行前配置数据库
    数据库的作用是记录订单状态
    支持环境变量配置，容器化部署
"""
import ccxt
import time
import pymongo
import json
import os


class Bitmextransaction(object):
    # 初始化策略参数
    def __init__(self, order_symbol, order_type, apikey, secret, num_buy, num_sell, order_spread, order_profit, order_amonut_buy,
                 order_amonut_sell, exchange):
        self.order_symbol = order_symbol
        self.apiKey = apikey
        self.secret = secret
        self.order_type = order_type
        self.num_buy = num_buy
        self.num_sell = num_sell
        self.order_spread = order_spread
        self.order_profit = order_profit
        self.order_amonut_buy = order_amonut_buy
        self.order_amonut_sell = order_amonut_sell
        if self.order_symbol == 'BTC/USD':
            self._symbol = 'XBTUSD'
        elif self.order_symbol == 'ETH/USD':
            self._symbol = 'ETHUSD'
        else:
            self._symbol = self.order_symbol
        # 初始化交易所
        if exchange == 'bitmex':
            self.exchange = ccxt.bitmex({"apiKey": self.apiKey, "secret": self.secret})
        elif exchange == 'binance':
            self.exchange = ccxt.binance({
                "apiKey": self.apiKey,
                "secret": self.secret,
                "sandbox": False,  # 设置为 True 使用测试网
                "options": {
                    'defaultType': 'spot'  # 现货交易
                }
            })

        # 从环境变量读取数据库配置
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
        mongo_db = os.getenv('MONGO_DB', exchange)

        client = pymongo.MongoClient(mongo_uri)  # 连接数据库
        db = client[mongo_db]

        self.col = db[self.order_symbol]

    # 策略主要交易逻辑
    def start_transaction(self):
        try:
            # 撤销所有订单
            if self.exchange.id == 'bitmex':
                data_ = self.exchange.privateDeleteOrderAll({"symbol": self._symbol})
                for i in data_:
                    print(i)
            elif self.exchange.id == 'binance':
                # Binance 撤销所有订单
                open_orders = self.exchange.fetch_open_orders(self.order_symbol)
                for order in open_orders:
                    self.exchange.cancel_order(order['id'], self.order_symbol)
                    print(f"撤销订单: {order['id']}")

        except ccxt.NetworkError as e:
            print(self.exchange.id, 'network error:', str(e))
            exit()
        except ccxt.ExchangeError as e:
            print(self.exchange.id, 'exchange error:', str(e))
            exit()
        except Exception as e:
            print(self.exchange.id, str(e))
            exit()

        base_price = self.exchange.fetch_ticker(self.order_symbol)['last']
        print(base_price)
        order_price_buy = base_price - self.order_spread
        order_price_sell = base_price + self.order_spread
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        time.sleep(0.03)

        balance = self.exchange.fetch_balance()
        if self.exchange.id == 'bitmex':
            print(balance['free']['BTC'])
        elif self.exchange.id == 'binance':
            # 获取 ETH 和 USDT 余额
            eth_balance = balance['free'].get('ETH', 0)
            usdt_balance = balance['free'].get('USDT', 0)
            print(f"ETH 余额: {eth_balance}")
            print(f"USDT 余额: {usdt_balance}")
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        time.sleep(0.03)

        # 创建网格订单
        if self.exchange.id == 'bitmex':
            # BitMEX 批量下单
            orders = []
            while self.num_buy > 0:
                orders.append(
                    {'symbol': self._symbol, 'side': 'Buy', 'orderQty': self.order_amonut_buy, 'price': order_price_buy})
                self.num_buy -= 1
                order_price_buy -= self.order_spread
            while self.num_sell > 0:
                orders.append(
                    {'symbol': self._symbol, 'side': 'Sell', 'orderQty': self.order_amonut_sell, 'price': order_price_sell})
                self.num_sell -= 1
                order_price_sell += self.order_spread
            Bulk_order = self.exchange.private_post_order_bulk({'orders': json.dumps(orders)})
            if Bulk_order:
                for i in Bulk_order:
                    dict = {"order_id": i['orderID'], "order_side": i['side'], "order_price": i['price'],
                            "order_status": i['ordStatus']}
                    self.col.insert_one(dict)
                    print(dict)
        elif self.exchange.id == 'binance':
            # Binance 单个下单
            while self.num_buy > 0:
                try:
                    order = self.exchange.create_order(
                        symbol=self.order_symbol,
                        type='limit',
                        side='buy',
                        amount=self.order_amonut_buy,
                        price=order_price_buy
                    )
                    dict = {"order_id": order['id'], "order_side": order['side'], "order_price": order['price'],
                            "order_status": order['status']}
                    self.col.insert_one(dict)
                    print(dict)
                except Exception as e:
                    print(f"创建买单失败: {e}")
                self.num_buy -= 1
                order_price_buy -= self.order_spread
                time.sleep(0.1)  # 避免频率限制

            while self.num_sell > 0:
                try:
                    order = self.exchange.create_order(
                        symbol=self.order_symbol,
                        type='limit',
                        side='sell',
                        amount=self.order_amonut_sell,
                        price=order_price_sell
                    )
                    dict = {"order_id": order['id'], "order_side": order['side'], "order_price": order['price'],
                            "order_status": order['status']}
                    self.col.insert_one(dict)
                    print(dict)
                except Exception as e:
                    print(f"创建卖单失败: {e}")
                self.num_sell -= 1
                order_price_sell += self.order_spread
                time.sleep(0.1)  # 避免频率限制
        # 循环检查订单状态 订单成交或者取消 重新挂单
        while True:
            try:
                for y in self.col.find():
                    take_order_id = y['order_id']
                    take_order_side = y['order_side']
                    take_order_price = y['order_price']
                    take_order_status = y['order_status']
                    time.sleep(0.03)
                    if take_order_status in ["Filled", "closed"] and take_order_side == "Buy":
                        take_sell_order = self.exchange.create_order(symbol=self.order_symbol, type=self.order_type,
                                                              side='sell',
                                                              amount=self.order_amonut_sell,
                                                              price=take_order_price + self.order_profit)
                        if "id" in take_sell_order:
                            if self.exchange.id == 'bitmex' and len(take_sell_order['id']) > 28:
                                myquery = {"order_id": take_order_id}
                                self.col.delete_one(myquery)
                                dict = {"order_id": take_sell_order['id'], "order_side": take_sell_order['info']['side'],
                                        "order_price": take_sell_order['price'],
                                        "order_status": take_sell_order['info']['ordStatus']}
                                self.col.insert_one(dict)
                                print(dict)
                            elif self.exchange.id == 'binance':
                                myquery = {"order_id": take_order_id}
                                self.col.delete_one(myquery)
                                dict = {"order_id": take_sell_order['id'], "order_side": take_sell_order['side'],
                                        "order_price": take_sell_order['price'],
                                        "order_status": take_sell_order['status']}
                                self.col.insert_one(dict)
                                print(dict)

                    elif take_order_status in ["Filled", "closed"] and take_order_side == "Sell":
                        take_buy_order = self.exchange.create_order(symbol=self.order_symbol, type=self.order_type,
                                                             side='buy',
                                                             amount=self.order_amonut_buy,
                                                             price=take_order_price - self.order_profit)
                        if "id" in take_buy_order:
                            if self.exchange.id == 'bitmex' and len(take_buy_order['id']) > 28:
                                myquery = {"order_id": take_order_id}
                                self.col.delete_one(myquery)
                                dict = {"order_id": take_buy_order['id'], "order_side": take_buy_order['info']['side'],
                                        "order_price": take_buy_order['price'],
                                        "order_status": take_buy_order['info']['ordStatus']}
                                self.col.insert_one(dict)
                                print(dict)
                            elif self.exchange.id == 'binance':
                                myquery = {"order_id": take_order_id}
                                self.col.delete_one(myquery)
                                dict = {"order_id": take_buy_order['id'], "order_side": take_buy_order['side'],
                                        "order_price": take_buy_order['price'],
                                        "order_status": take_buy_order['status']}
                                self.col.insert_one(dict)
                                print(dict)

                    elif take_order_status in ["Canceled", "canceled"] and take_order_side == "Buy":
                        take_buy_order = self.exchange.create_order(symbol=self.order_symbol, type=self.order_type,
                                                             side='buy',
                                                             amount=self.order_amonut_buy, price=take_order_price)

                        if "id" in take_buy_order:
                            if self.exchange.id == 'bitmex' and len(take_buy_order['id']) > 28:
                                myquery = {"order_id": take_order_id}
                                self.col.delete_one(myquery)
                                dict = {"order_id": take_buy_order['id'], "order_side": take_buy_order['info']['side'],
                                        "order_price": take_buy_order['price'],
                                        "order_status": take_buy_order['info']['ordStatus']}
                                self.col.insert_one(dict)
                                print(dict)
                            elif self.exchange.id == 'binance':
                                myquery = {"order_id": take_order_id}
                                self.col.delete_one(myquery)
                                dict = {"order_id": take_buy_order['id'], "order_side": take_buy_order['side'],
                                        "order_price": take_buy_order['price'],
                                        "order_status": take_buy_order['status']}
                                self.col.insert_one(dict)
                                print(dict)

                    elif take_order_status in ["Canceled", "canceled"] and take_order_side == "Sell":
                        take_sell_order = self.exchange.create_order(symbol=self.order_symbol, type=self.order_type,
                                                              side='sell',
                                                              amount=self.order_amonut_sell, price=take_order_price)

                        if "id" in take_sell_order:
                            if self.exchange.id == 'bitmex' and len(take_sell_order['id']) > 28:
                                myquery = {"order_id": take_order_id}
                                self.col.delete_one(myquery)
                                dict = {"order_id": take_sell_order['id'], "order_side": take_sell_order['info']['side'],
                                        "order_price": take_sell_order['price'],
                                        "order_status": take_sell_order['info']['ordStatus']}
                                self.col.insert_one(dict)
                                print(dict)
                            elif self.exchange.id == 'binance':
                                myquery = {"order_id": take_order_id}
                                self.col.delete_one(myquery)
                                dict = {"order_id": take_sell_order['id'], "order_side": take_sell_order['side'],
                                        "order_price": take_sell_order['price'],
                                        "order_status": take_sell_order['status']}
                                self.col.insert_one(dict)
                                print(dict)

            except ccxt.NetworkError as e:
                print(self.exchange.id, 'network error:', str(e))
            except ccxt.ExchangeError as e:
                print(self.exchange.id, 'exchange error:', str(e))
            except Exception as e:
                print(self.exchange.id, str(e))
