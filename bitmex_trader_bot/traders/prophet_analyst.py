import requests

import json

import datetime as dt

import pandas as pd

import numpy as np

import matplotlib.pyplot as plt

from fbprophet import Prophet

from ..analyst import Analyst


class ProphetAnalyst(Analyst):
    """
    指定の取引所で時系列解析で価格予測するクラス
    """

    def __init__(self, logger, config):
        super().__init__(logger, config)
        self.__data_url = config.get("cryptowat", "url")
        self.__get_data_count = 60 * 3
        self.__periods = 10

        self.current_price = 0.0
        self.results = None

    @property
    def forecast_position(self):
        """
        予測ポジション

        :rtype: str
        :return: 予測ポジション
        """

        result = self.check_position()
        message = "forecast_position: {0}".format(result)
        self._slack.notify(message)
        self._logger.info(message)

        return result

    def forecast(self):
        """
        open,high,low,closeそれぞれの過去データから時系列解析を行う

        :rtype: object
        :return: 時系列解析結果
        """

        h_base_date_list, h_date_list, h_price_list = self.__get_price_data(
            type="high")
        l_base_date_list, l_date_list, l_price_list = self.__get_price_data(
            type="low")
        high_forecast = self.__forecast(
            type="high",
            base_date_list=h_base_date_list,
            date_list=h_date_list,
            price_list=h_price_list)
        low_forecast = self.__forecast(
            type="low",
            base_date_list=l_base_date_list,
            date_list=l_date_list,
            price_list=l_price_list)

        del h_base_date_list
        del h_date_list
        del h_price_list
        del l_base_date_list
        del l_date_list
        del l_price_list

        self.results = {
            "high": high_forecast,
            "low": low_forecast,
        }

        message = "analyst.high: {0}".format(
            self.results["high"].high_price)
        self._slack.notify(message)
        self._logger.info(message)
        message = "analyst.low: {0}".format(
            self.results["low"].low_price)
        self._slack.notify(message)
        self._logger.info(message)

        return self.results

    def check_position(self):
        """
        high,lowそれぞれの予測ポジションから
        総合的にポジション取得可能か判断する

        :rtype: str
        :return: 予測ポジション
        """

        positions = []
        for type in ["high", "low"]:
            pos = self.results[type].recommendation_position()
            positions.append(pos)

        last_pos = None
        for pos in positions:
            if last_pos is None:
                last_pos = pos
            if last_pos != pos:
                last_pos = None
                break

        return pos

    def __get_price_data(self, type="close"):
        """
        過去の価格情報を取得する

        :param str type: 価格種類(open, high, low, close)
        :rtype: object
        :return: 日付、価格リスト
        """
        if type == "open":
            type_index = 1
        if type == "high":
            type_index = 2
        if type == "low":
            type_index = 3
        if type == "close":
            type_index = 4

        now_date = dt.datetime.now()
        startDate = now_date - dt.timedelta(hours=self.__get_data_count / 60)
        endDate = now_date

        startTimestamp = startDate.timestamp()
        endTimestamp = endDate.timestamp()

        after = str(int(startTimestamp))
        before = str(int(endTimestamp))
        query = {"periods": "60", "after": after, "before": before}
        url = self.__data_url
        res = json.loads(requests.get(url, params=query).text)["result"]["60"]
        res = np.array(res)

        # 日時リスト作成
        time_stamp = res[:, 0].reshape(len(res), 1)
        time_stamp = [dt.datetime.fromtimestamp(time_stamp[i]) for i in range(
            len(time_stamp))]
        date_list = []
        base_date = dt.datetime.now() - dt.timedelta(hours=len(time_stamp))
        tmp_date = base_date
        for item in time_stamp:
            tmp_date += dt.timedelta(hours=1)
            tmp_datetime = tmp_date
            date_list.append(tmp_datetime)

        # 価格リスト作成
        price_list = res[:, type_index].reshape(len(res), 1)
        price_list = [float(price_list[i]) for i in range(len(price_list))]

        # リストをクリーンアップする
        index = 0
        remove_indexs = []
        for item in price_list:
            if item <= 0:
                remove_indexs.insert(0, index)
            index += 1
        for remove_index in remove_indexs:
            del time_stamp[remove_index]
            del price_list[remove_index]
            del date_list[remove_index]

        return time_stamp, date_list, price_list

    def __forecast(self, type, base_date_list, date_list, price_list):
        """
        日付、価格リストから時系列解析を行う
        結果のグラフをSlackの指定のチャンネルへ送信する

        :param list base_date_list: 日付リスト
        :param list date_list: 解析用に改変した日付リスト(分→日)
        :param list price_list: 価格リスト
        :rtype: object
        :return: 解析結果
        """

        # 解析には直近データを検証用に利用するため別で用意する
        periods = int(self.__periods)

        # 予測モデルを作成する
        fit_data = pd.DataFrame([date_list, price_list]).T
        fit_data.columns = ["ds", "y"]

        model = Prophet()
        model.fit(fit_data)

        # 解析する
        future_data = model.make_future_dataframe(periods=periods, freq="H")
        forecast_data = model.predict(future_data)

        # 解析データから日付と値を取得する
        forecast_dss = forecast_data.ds.values
        forecast_dss = [pd.to_datetime(forecast_dss[i]) for i in range(
            len(forecast_dss))]
        forecast_yhats = forecast_data.yhat.values
        forecast_yhats = [round(float(forecast_yhats[i])) for i in range(
            len(forecast_yhats))]

        # 時系列解析用に変更していた日時を元に戻す
        index = 0
        last_timestamp = base_date_list[-1]
        future_values = []
        for item in forecast_dss:
            if len(base_date_list) <= index:
                last_timestamp += dt.timedelta(minutes=1)
                tmp_date = last_timestamp
                base_date_list.append(tmp_date)
                price_list.append(price_list[-1])
                future_values.append(forecast_yhats[index])
            index += 1

        # 移動平均を求める
        ma25 = pd.Series(price_list).rolling(window=25).mean()

        # ボリンジャーバンドを求める
        siguma = pd.Series(price_list).rolling(window=25).std(ddof=0)
        up_borin2 = ma25 + siguma * 2
        low_borin2 = ma25 - siguma * 2

        # グラフを表示する
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(base_date_list, price_list)
        ax.plot(base_date_list, forecast_yhats, color="red")
        ax.plot(base_date_list, ma25, color="blue")
        ax.plot(base_date_list, up_borin2, linewidth=1, color="green")
        ax.plot(base_date_list, low_borin2, linewidth=1, color="green")
        ax.set_title("images/{0} XBT Price".format(type))
        ax.set_xlabel("min")
        ax.set_ylabel("{0}XBT Price[$]".format(type))
        plt.grid(fig)
        plt.savefig("images/{0}_price_data.jpg".format(type))

        model.plot(forecast_data)
        plt.savefig("images/{0}_forecast_data.jpg".format(type))
        plt.close()

        del fit_data
        del future_data
        del forecast_data
        del forecast_dss
        del forecast_yhats
        del date_list
        del price_list
        del fig
        del model

        # slackに画像送信する
        if type == "high":
            self._slack.upload_image("images/{0}_price_data.jpg".format(type))
            self._slack.upload_image("images/{0}_forecast_data.jpg".format(type))

        return AnalysisData(base_date_list, future_values)


class AnalysisData(object):
    """
    時系列解析の結果を管理するクラス
    """

    def __init__(self, date_list, data_list):
        self.__date_list = date_list
        self.__price_list = data_list

    @property
    def high_price(self):
        """
        予測高値

        :rtype: float
        :return: 予測高値
        """

        return max(self.__price_list)

    @property
    def low_price(self):
        """
        予測安値

        :rtype: float
        :return: 予測安値
        """
        return min(self.__price_list)

    @property
    def high_data_list(self):
        """
        予測高値リスト(日付、価格)

        :rtype: object
        :return: 予測高値リスト(日付、価格)
        """

        return self.__get_data_list_with_price(self.high_price)

    @property
    def low_data_list(self):
        """
        予測安値リスト(日付、価格)

        :rtype: object
        :return: 予測安値リスト(日付、価格)
        """

        return self.__get_data_list_with_price(self.low_price)

    def recommendation_position(self):
        """
        予測価格から取得すべきポジションを返す

        :rtype: str
        :return: 予測ポジション(long, short, None)
        """

        open = self.__price_list[0]
        high = self.high_price
        low = self.low_price
        close = self.__price_list[-1]

        pos = None
        if open < close - 10:
            pos = "long"
            if open < low:
                pos = None
        elif open > close + 10:
            pos = "short"
            if open < high:
                pos = None
        return pos

    def __get_data_list_with_price(self, price):
        """
        指定価格の価格情報(日付、価格)を返す

        :param float price: 価格
        :rtype: object
        :return: 指定価格の価格情報(日付、価格)
        """

        result = []
        index = 0
        for item in self.__price_list:
            if item == price:
                result.append({
                    "date": self.__date_list[index],
                    "price": item
                })
            index += 1
        return result
