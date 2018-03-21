import time

from ..trader import Trader

from .prophet_analyst import ProphetAnalyst


class CustomTrader(Trader):
    def __init__(self, config=None, logger=None, sleep_second=60):
        super().__init__(config, logger)
        self.__sleep_second = sleep_second

    def start(self):
        while True:
            try:
                # 取引所情報を取得する
                # bitmex = self._core.get_exchange()
                current_ticker = self._core.get_ticker()
                self._core.current_price = current_ticker["last"]

                # 予測情報を取得する
                self._core.analyst = ProphetAnalyst(self._logger, self._config)
                self._core.analyst.forecast()

                message = "現在価格: {0}".format(self._core.current_price)
                self._slack.notify(message)
                self._logger.info(message)

                # ポジションを持っているかチェックする
                positions = self._core.get_positions()
                self._logger.info("positions: {0}".format(positions))
                if len(positions) <= 0:
                    is_do_order, position = self._core.do_order_check()
                    if is_do_order:
                        message = "{0}から{1}で注文する！".format(
                            self._core.current_price, position)
                        self._slack.notify(message)
                        self._logger.info(message)
                        order = self._core.order(position, 1000)
                        self._logger.info("order: {0}".format(order))
                    else:
                        message = "ポジションを取らない！"
                        self._slack.notify(message)
                else:
                    message = "現在損益: {0:.8f} XBT".format(
                        self._core.current_profit)
                    self._slack.notify(message)

                    is_release_order = self._core.release_check()
                    if is_release_order:
                        order = self._core.close_order(positions[-1])
                        self._logger.info("order: {0}".format(order))
                        message = """
                        ポジションを解消！
                        損益: {0:.8f} XBT
                        手数料: {1:.8f} XBT
                        トレード回数: {2} 回
                        最大利益: {3:.8f} XBT
                        最大損失: {4:.8f} XBT
                        """.format(
                            self._core.total_profit,
                            self._core.total_tax,
                            len(self._core.profits),
                            max(self._core.profits),
                            min(self._core.profits))
                        self._slack.notify(message)
                    else:
                        message = "ポジションを維持！"
                        self._slack.notify(message)

            except Exception as e:
                self._logger.exception(e)

            time.sleep(self.__sleep_second)
