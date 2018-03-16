import logging

import pytest

import os

import sys

from configparser import ConfigParser

from bitmex_trader_bot.core import Core


class TestCore(object):

    @pytest.fixture(scope='session', autouse=True)
    def logger(self):
        # ロガーの設定

        # フォーマット
        format_str = "%(asctime)s [%(levelname)8s] %(message)s"
        log_format = logging.Formatter(format_str)

        # レベル
        result = logging.getLogger()
        result.setLevel(logging.DEBUG)

        # 標準出力へのハンドラ
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(log_format)
        result.addHandler(stdout_handler)
        yield(result)

    @pytest.fixture(scope='session', autouse=True)
    def config(self):
        app_home = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))
        result = ConfigParser()
        conf_path = os.path.join(app_home, "config", "test.config")
        result.read(conf_path)
        yield(result)

    @pytest.fixture()
    def bot(self, logger, config):
        return Core(logger=logger, config=config)

    def test_type(self, bot):
        assert isinstance(bot, Core)

    def test_val(self, bot):
        assert bot.Loss_cutting_line == 100

        # hoge.update('hoge')
        # assert hoge.val == 'hige'


if __name__ == '__main__':
    pytest.main()