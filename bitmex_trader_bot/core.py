import ccxt

from .forecast_price import ForecastPrice

from .forecast_checker import ForecastChecker

from .slack_api import SlackApi


class Core(object):
    """
    取引所へアクセスしてトレードするBotクラス
    """

    def __init__(self, config):
        """
        :param object config: 設定情報
        """

        self.__data_url = config.get("cryptowat", "url")
        self.exchange = None
        self.symbol = "BTC/USD"
        self.current_ticker = None
        self.positions = []

        # 損切りライン(USD)
        # TODO: XBTに変更する
        self.Loss_cutting_line = 100

        # 手数料
        # TODO: 取引所から情報取得する
        self.tax_rate = 0.075

        # 前回損益
        self.before_profit = 0.0

        # トータル損益
        # TODO: リスト管理に変更する
        self.total_profit = 0.0

        # トータル手数料
        # TODO: リスト管理に変更する
        self.total_tax = 0.0

    @property
    def current_profit(self):
        """
        現在損益

        :rtype: float
        :return: 現在損益
        """

        result = 0.0
        price = self.current_ticker["close"]
        if len(self.positions) > 0:
            order = self.positions[0]
            amount = order["amount"]
            pref_price = order["price"]
            pref_price_xbt = round(amount / pref_price, 8)
            price_xbt = round(amount / price, 8)
            if order["type"] == "buy":
                result = pref_price_xbt - price_xbt
            else:
                result = price_xbt - pref_price_xbt
        return result

    def get_exchange(self):
        """
        取引所情報を取得する

        :rtype: object
        :return: 取引所情報
        """

        if self.exchange is None:
            self.exchange = ccxt.bitmex()
        return self.exchange

    def get_ticker(self):
        """
        現在情報を取得する

        :rtype: object
        :return: 現在情報
        """

        if self.exchange is None:
            self.exchange = ccxt.bitmex()
        self.current_ticker = self.exchange.fetch_ticker(self.symbol)
        return self.current_ticker

    def get_positions(self):
        """
        現在ポジションを持っているか確認する
        持っている場合、注文情報を返す

        :rtype: object
        :return: 注文情報
        """

        # TODO: アクティブな注文を取得する
        return self.positions

    def do_order_check(self, recommend_pos, forecast_data):
        """
        注文するか判断する
        注文する場合、Trueを返す

        :param str recommend_pos: 予測したポジション
        :param object amount: 予測価格情報
        :rtype: bool
        :return: 判断結果
        """

        price = self.current_ticker["close"]
        forecast_high = forecast_data["high"].high_price
        forecast_low = forecast_data["high"].low_price
        if recommend_pos is not None:
            if recommend_pos == "long":
                if price < forecast_low:
                    return True
            if recommend_pos == "short":
                if price > forecast_high:
                    return True
        return False

    def release_check(self, recommend_pos):
        """
        利確・損切りするか判断する
        利確・損切りする場合、Trueを返す

        :param str recommend_pos: 予測したポジション
        :rtype: bool
        :return: 判断結果
        """

        if len(self.positions) == 0:
            return False

        close = self.current_ticker["close"]
        order = self.positions[0]
        type = order["type"]
        order_price = order["price"]
        order_pos = "long" if type == "buy" else "sell"
        if order_pos != recommend_pos:
            return True
        if order_pos == "long":
            if order_price > close + self.Loss_cutting_line:
                return True
        elif order_pos == "short":
            if order_price < close - self.Loss_cutting_line:
                return True
        else:
            return True

        return False

    def get_forecast(self):
        """
        価格推移を予想する

        :rtype: object
        :return: 予想結果
        """

        forecast_price = ForecastPrice(self.__data_url)
        return forecast_price.forecast()

    def forecast_position(self, forecast_data):
        """
        時系列解析結果のポジションを返す

        :param str forecast_data: 予測したポジション
        :rtype: srt
        :return: 予測ポジション
        """

        close = self.current_ticker["close"]
        checker = ForecastChecker(close, forecast_data)
        return checker.check_position()

    def order(self, position, amount, price=0):
        """
        注文する

        :param float amount: 数量
        :param float price: 価格
        :rtype: object
        :return: 注文情報
        """

        if price == 0:
            price = self.current_ticker["close"]
        if position == "long":
            type = "buy"
        if position == "short":
            type = "sell"
        self.before_profit = 0.0
        price_xbt = round(amount / price, 8)
        self.before_tax = round(price_xbt * float(self.tax_rate / 100), 8)
        order = {
            "type": type,
            "amount": amount,
            "price": price,
            "tax": self.before_tax
        }

        self.positions.append(order)
        self.total_tax += self.before_tax

        return order

    def close_order(self, pref_order):
        """
        前回注文を解消する注文を入れる

        :param object: 前回注文情報
        :rtype: object
        :return: 注文情報
        """

        price = self.current_ticker["close"]
        amount = pref_order["amount"]
        type = "buy"
        if pref_order["type"] == "buy":
            type = "sell"
        amount_xbt = round(amount / price, 8)
        self.before_tax = round(amount_xbt * float(self.tax_rate / 100), 8)
        if len(self.positions) > 0:
            self.positions = []
        order = {
            "type": type,
            "amount": amount,
            "price": price,
            "tax": self.before_tax
        }

        pref_xbt = round(amount / pref_order["price"], 8)
        close_xbt = round(amount / price, 8)
        self.before_profit = 0.0
        self.before_tax = 0.0
        if type == "buy":
            self.before_profit = close_xbt - pref_xbt
            message = "{0} {1:.8f} - {2:.8f}: {3:.8f}".format(
                type,
                close_xbt,
                pref_xbt,
                self.before_profit
            )
        else:
            self.before_profit = pref_xbt - close_xbt
            message = "{0} {1:.8f} - {2:.8f}: {3:.8f}".format(
                type,
                pref_xbt,
                close_xbt,
                self.before_profit
            )

        SlackApi().notify(message)
        self.total_profit += self.before_profit
        self.total_tax += self.before_tax

        return order
