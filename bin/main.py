import importlib

import sys

import os

from optparse import OptionParser

from configparser import ConfigParser

import logging

from dotenv import load_dotenv, find_dotenv


def main(config):
    """
    指定時間ごとにBotを実行してトレードを行う

    :param object config: 設定情報
    """

    # ログ出力
    logger.info("start")

    # オプション取得
    logger.info(options.debug)

    # 環境変数設定
    load_dotenv(find_dotenv())

    trade_name = config.get("trade", "name")
    module = importlib.import_module(trade_name)
    trade = module.ProphetTrade(config=config, logger=logger,
                                sleep_second=sleep_second)
    trade.start()


if __name__ == "__main__":
    # 自身の名前から拡張子を除いてプログラム名(${prog_name})にする
    prog_name = os.path.splitext(os.path.basename(__file__))[0]

    # 親ディレクトリをアプリケーションのホーム(${app_home})に設定
    app_home = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "../"))

    # オプションのパース
    usage = "usage: %prog (sleep_second) [amount]"
    parser = OptionParser(usage=usage)
    parser.add_option("-d", "--debug", dest="debug",
                      action="store_true", help="debug", default=False)

    # オプションと引数を格納し分ける
    (options, args) = parser.parse_args()

    # 設定ファイルを読む
    config = ConfigParser()
    env = "production"
    if options.debug:
        env = "development"
    config_file_name = "{0}.config".format(env)
    conf_path = os.path.join(app_home, "config", config_file_name)
    config.read(conf_path)

    # 引数のチェック
    if len(args) != 1:
        sys.stderr.write("argument error. use -h or --help option\n")
        sys.exit(1)
    else:
        sleep_second = int(args[0])

    # ロガーの設定

    # フォーマット
    log_format = logging.Formatter("%(asctime)s [%(levelname)8s] %(message)s")

    # レベル
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 標準出力へのハンドラ
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_format)
    logger.addHandler(stdout_handler)

    # ログファイルへのハンドラ
    file_name = "{0}.log".format(prog_name)
    file_handler = logging.FileHandler(
        os.path.join(app_home, "log", file_name), "a+")
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)

    try:
        main(config)
    except Exception as e:
        # キャッチして例外をログに記録
        logger.exception(e)
        sys.exit(1)
