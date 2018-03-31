import time

from ..trader import Trader

from .inago_analyst import InagoAnalyst

from ..slack_api import SlackApi


class CustomTrader(Trader):
    def __init__(self, config=None, logger=None, sleep_second=1):
        super().__init__(config, logger)
        self.__sleep_second = sleep_second

        self._analyst = InagoAnalyst(logger, config)
        self._wait_count = 0

    def start(self):
        message = "いなごトレード開始"
        self._slack.notify(message)
        order = None
        while True:
            try:
                message = ""
                self._analyst.positions = self._core.get_positions()
                self._logger.info(self._analyst.positions)
                self._analyst.forecast()
                forecast_position = self._analyst.check_position()

                if len(self._analyst.positions) <= 0:
                    if forecast_position is not None:
                        message = "{0}を{1}".format(self._analyst.last_price, forecast_position)
                        order = self._core.order(forecast_position, 1000)
                        self._logger.info(message)
                        self._slack.notify(message)
                        self._analyst.upload_image()
                else:
                    self._wait_count+=1
                    if self._wait_count > 10:
                        message = "{0}注文{1}を維持 now:{2}".format(self._analyst.current_forecast_position,
                                                                  self._analyst.positions[-1]["price"],
                                                                  self._analyst.last_price)
                        self._slack.notify(message)
                        message = "現在損益: {0:.8f} XBT".format(self._core.current_profit)
                        self._slack.notify(message)
                        self._analyst.upload_image()
                        self._wait_count = 0

                    message = ""
                    if forecast_position is not None:
                        order_str = "{0}注文{1}をクローズ now:{2}"
                        message = order_str.format(forecast_position,
                                                   self._analyst.positions[-1]["price"],
                                                   self._analyst.last_price)
                        self._core.close_order(self._analyst.positions[-1])
                        order = None
                        self._analyst.current_forecast_position = None

                    if message != "":
                        self._logger.info(message)
                        self._slack.notify(message)
                        self._analyst.upload_image()

                    if order is None:
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

            except Exception as e:
                self._logger.exception(e)

            time.sleep(self.__sleep_second)

