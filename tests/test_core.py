import pytest

import os

from configparser import ConfigParser

from bitmex_trader_bot.core import Core


class TestCore(object):

    @pytest.fixture(scope='session', autouse=True)
    def config(self):
        app_home = os.path.abspath(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))
        config = ConfigParser()
        conf_path = os.path.join(app_home, "config", "test.config")
        config.read(conf_path)
        print(conf_path)
        print(config)
        print("setup before session")
        yield(config)
        print("teardown after session")

    @pytest.fixture()
    def bot(self, config):
        return Core(config)

    def test_type(self, bot):
        assert isinstance(bot, Core)

    def test_val(self, bot):
        assert bot.Loss_cutting_line == 100

        # hoge.update('hoge')
        # assert hoge.val == 'hige'


if __name__ == '__main__':
    pytest.main()