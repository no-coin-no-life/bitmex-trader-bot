import time

from selenium import webdriver

from selenium.webdriver.chrome.options import Options

from PIL import Image

from ..analyst import Analyst


class InagoAnalyst(Analyst):
    """
    いなごフライヤーから情報取得してポジション取得・利確・損切りを判定するクラス
    """

    def __init__(self, logger, config):
        """
        """
        super().__init__(logger, config)
        """
        # Google Chrome
        options = Options()
        options.binary_location = "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
        options.add_argument('--headless')
        self.__driver = webdriver.Chrome(chrome_options=options,
                                         executable_path="D:\\chromedriver.exe")
        """

        # PhantomJS
        self.__driver = webdriver.PhantomJS(
            # executable_path="./node_modules/phantomjs/bin/phantomjs") # Mac
            executable_path="D:\\phantomjs-2.1.1-windows\\bin\\phantomjs.exe") # Win

        self.__driver.get("https://inagoflyer.appspot.com/btcmac")
        time.sleep(5) # いなごフライヤーが情報取得するの待ち

        self.last_price = 0.0

        # 買いボリューム
        self._ask = 0.0
        self.__ask_vols = []
        self._ask_total = 0.0

        # 売りボリューム
        self._bid = 0.0
        self.__bid_vols = []
        self._bid_total = 0.0

        # 保持しているポジション
        self.positions = None
        self._current_forecast_position = None
        self._pref_forecast_position = None

    @property
    def current_forecast_position(self):
        return self._current_forecast_position

    @current_forecast_position.setter
    def current_forecast_position(self, value):
        self._pref_forecast_position = self._current_forecast_position
        self._current_forecast_position = value
        if self._pref_forecast_position is None:
            self._pref_forecast_position = value

    @property
    def _vol_hold_count(self):
        """
        ボリューム保持数

        :rtype: int
        :return: ボリューム保持数
        """
        return 1 if len(self.positions) > 0 else 3

    @property
    def _vol_threshold(self):
        """
        ボリュームのポジション判断しきい値

        :rtype: int
        :return: ボリュームのポジション判断しきい値
        """

        return 0 if len(self.positions) > 0 else 300

    @property
    def _ask_vols(self):
        """
        買いボリュームリスト

        :rtype: int[]
        :return: 買いボリュームリスト
        """

        return self.__ask_vols[:self._vol_hold_count]

    @_ask_vols.setter
    def _ask_vols(self, value):
        self.__ask_vols.append(value)
        if len(self.__ask_vols) > self._vol_hold_count:
            del self.__ask_vols[0]

    @property
    def _bid_vols(self):
        """
        売りボリュームリスト

        :rtype: int[]
        :return: 買いボリュームリスト
        """

        return self.__bid_vols[:self._vol_hold_count]

    @_bid_vols.setter
    def _bid_vols(self, value):
        self.__bid_vols.append(value)
        if len(self.__bid_vols) > self._vol_hold_count:
            del self.__bid_vols[0]

    @property
    def forecast_position(self):
        """
        予測ポジション

        :rtype: str
        :return: 予測ポジション
        """
        return None

    def forecast(self):
        """
        いなごフライヤーのボリューム取得する
        """
        self._scraping()
        info_str = "askVol: {0} bidVol: {1} price: {2}"
        self._logger.info(info_str.format(self._ask, self._bid, self.last_price))
        self._ask_vols = self._ask
        self._bid_vols = self._bid
        self._ask_total = sum(self._ask_vols)
        self._bid_total = sum(self._bid_vols)
        info_str = "ask: {0:.2f} bid: {1:.2f} len:{2}"
        self._logger.info(info_str.format(self._ask_total,
                                          self._bid_total,
                                          len(self._ask_vols)))
        self._logger.info("-----------------")

    def check_position(self):
        """
        総合的にポジション取得可能か判断する

        :rtype: str
        :return: 予測ポジション
        """
        pref_forecast_position = self.current_forecast_position
        if len(self.positions) <= 0:
            vol_threshold = self._vol_hold_count * self._vol_threshold
            if self._ask_total > self._bid_total:
                if (self._ask_total - self._bid_total) > vol_threshold:
                    self.current_forecast_position = "long"
            elif self._ask < self._bid:
                if (self._bid_total - self._ask_total) > vol_threshold:
                    self.current_forecast_position = "short"
        else:
            if self._ask_total > self._bid_total:
                if (self._ask_total - self._bid_total) > 0:
                    if self._pref_forecast_position == "short":
                        self.current_forecast_position = "long"
            else:
                if (self._bid_total - self._ask_total) > 0:
                    if self._pref_forecast_position == "long":
                        self.current_forecast_position = "short"

        self._logger.info(self.current_forecast_position)
        self._logger.info(self._pref_forecast_position)
        self._logger.info(self._ask_vols)
        self._logger.info(self._bid_vols)
        if self.current_forecast_position != pref_forecast_position:
            return self.current_forecast_position
        return None

    def _scraping(self):
        self._ask = float(self.__driver.find_element_by_id(
            "buyVolumePerMeasurementTime").text)
        self._bid = float(self.__driver.find_element_by_id(
            "sellVolumePerMeasurementTime").text)
        self.last_price = float(self.__driver.find_element_by_id(
            "BitMEX_BTCUSD_lastprice").text)

    def upload_image(self):
        img_path = "./images/inago_snap.png"
        element = self.__driver.find_element_by_id("volume_chart")
        location = element.location
        size = element.size
        self.__driver.save_screenshot(img_path)
        im = Image.open(img_path)

        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']

        im = im.crop((left, top, right, bottom))
        im.save(img_path)
        self._slack.upload_image(img_path)