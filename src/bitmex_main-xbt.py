"""
运行策略入口文件，支持多交易所交易对
支持环境变量配置，容器化部署
策略运行后 直接远程查看数据库  就可观察订单状态

"""

import os
from bitmex_websocket._websocket import BitmexWebsocket
from Quant import Bitmextransaction

if __name__ == '__main__':

    # 从环境变量读取配置，如果没有则使用默认值
    exchange = os.getenv('EXCHANGE', 'binance')
    apiKey = os.getenv('API_KEY', '')
    secret = os.getenv('API_SECRET', '')
    order_symbol = os.getenv('ORDER_SYMBOL', 'ETH/USDT')  # 交易品种
    order_type = os.getenv('ORDER_TYPE', 'limit')  # 平仓时挂单方式
    num_buy = int(os.getenv('NUM_BUY', '3'))  # 买网格数量
    num_sell = int(os.getenv('NUM_SELL', '1'))  # 卖网格数量
    order_spread = float(os.getenv('ORDER_SPREAD', '0.5'))  # 网格步长
    order_profit = float(os.getenv('ORDER_PROFIT', '0.5'))  # 利润
    order_amonut_buy = int(os.getenv('ORDER_AMOUNT_BUY', '30'))  # 买单挂单数量
    order_amonut_sell = int(os.getenv('ORDER_AMOUNT_SELL', '30'))  # 卖单挂单数量

    # 打印配置信息
    print(f"交易所: {exchange}")
    print(f"交易对: {order_symbol}")
    print(f"买网格数量: {num_buy}")
    print(f"卖网格数量: {num_sell}")
    print(f"网格步长: {order_spread}")
    print(f"利润目标: {order_profit}")
    print(f"买单数量: {order_amonut_buy}")
    print(f"卖单数量: {order_amonut_sell}")

    # 检查 API 密钥
    if not apiKey or not secret:
        print("错误: 请设置 API_KEY 和 API_SECRET 环境变量")
        exit(1)

    bitmex_ws = BitmexWebsocket(host="wss://www.bitmex.com/realtime", ping_interval=1, key=apiKey, secret=secret,
                                _symbol=order_symbol, db_exchange=exchange)
    bitmex_ws.start()
    start_ = Bitmextransaction(order_symbol, order_type, apiKey, secret, num_buy, num_sell, order_spread, order_profit,
                               order_amonut_buy, order_amonut_sell, exchange=exchange)
    start_.start_transaction()
