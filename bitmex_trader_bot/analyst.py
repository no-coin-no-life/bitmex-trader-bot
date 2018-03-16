from .slack_api import SlackApi


class Analyst(object):
    """
    指定の取引所で価格予測するクラス
    """

    def __init__(self, logger, config):
        self._logger = logger
        self._config = config
        self._slack = SlackApi()

        self.current_price = 0.0
        self.results = None

    @property
    def forecast_position(self):
        """
        予測ポジション

        :rtype: str
        :return: 予測ポジション
        """
        pass

    def forecast(self):
        """
        解析する

        :rtype: object
        :return: 解析結果
        """
        pass

    def check_position(self):
        """
        ポジション取得可能か判断する

        :rtype: str
        :return: 予測ポジション
        """
        pass
