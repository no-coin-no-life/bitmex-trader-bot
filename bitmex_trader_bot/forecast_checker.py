class ForecastChecker(object):
    """
    時系列解析結果からポジション取得するか判断するクラス
    """

    def __init__(self, close_price, forecast_data):
        self.__close_price = close_price
        self.__forecast_data = forecast_data

    def check_position(self):
        """
        open,high,low,closeそれぞれの予測ポジションから
        総合的にポジション取得可能か判断する

        :rtype: str
        :return: 予測ポジション
        """

        positions = []
        for type in ["open", "high", "low", "close"]:
            pos = self.__forecast_data[type].recommendation_position()
            positions.append(pos)

        last_pos = None
        for pos in positions:
            if last_pos is None:
                last_pos = pos
            if last_pos != pos:
                last_pos = None
                break

        return pos
