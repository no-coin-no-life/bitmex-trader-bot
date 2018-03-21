from .core import Core

from .slack_api import SlackApi


class Trader(object):
    def __init__(self, config, logger):
        self._logger = logger
        self._config = config
        self._slack = SlackApi()
        self._core = Core(config=config, logger=logger)

    def start(self):
        pass
