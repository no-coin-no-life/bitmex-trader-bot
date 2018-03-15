import sys

import os

from optparse import OptionParser

from configparser import ConfigParser

import logging

import time

import gc

from dotenv import load_dotenv, find_dotenv

from bitmex_trader_bot.core import Core

from bitmex_trader_bot.slack_api import SlackApi


def main(config):
    """
    指定時間ごとにBotを実行してトレードを行う

    :param object config: 設定情報
    """

    # ログ出力
    logger.info("start")

    # オプション取得
    logger.info(options.debug)

    # ライブラリ呼び出し
    bot = Core(config)
    slack = SlackApi()

    # 環境変数設定
    load_dotenv(find_dotenv())

    while True:
        try:
            # 取引所情報を取得する
            # bitmex = bot.get_exchange()
            current_ticker = bot.get_ticker()
            close_price = current_ticker["last"]

            # 予測情報を取得する
            forecast_data = bot.get_forecast()
            recommend_pos = bot.forecast_position(forecast_data)

            message = "現在価格: {0}".format(close_price)
            slack.notify(message)
            logger.info(message)
            message = "forecast.high: {0}".format(
                forecast_data["high"].high_price)
            slack.notify(message)
            logger.info(message)
            message = "forecast.low: {0}".format(
                forecast_data["low"].low_price)
            slack.notify(message)
            logger.info(message)
            message = "recommend_pos: {0}".format(recommend_pos)
            slack.notify(message)
            logger.info(message)

            # ポジションを持っているかチェックする
            positions = bot.get_positions()
            logger.info("positions: {0}".format(positions))
            if len(positions) <= 0:
                result = bot.do_order_check(recommend_pos, forecast_data)
                if result:
                    message = "{0}から{1}で注文する！".format(
                        close_price, recommend_pos)
                    slack.notify(message)
                    logger.info(message)
                    order = bot.order(recommend_pos, 1000)
                    logger.info("order: {0}".format(order))
                else:
                    message = "ポジションを取らない！"
                    slack.notify(message)
            else:
                message = "現在損益: {0:.8f} XBT".format(bot.current_profit)
                slack.notify(message)

                result = bot.release_check(recommend_pos)
                if result:
                    order = bot.close_order(positions[-1])
                    logger.info("order: {0}".format(order))
                    message = """
                    ポジションを解消！
                    損益: {0:.8f} XBT
                    手数料: {1:.8f} XBT
                    トレード回数: {2} 回
                    最大利益: {3:.8f} XBT
                    最大損失: {4:.8f} XBT
                    """.format(
                        bot.total_profit,
                        bot.total_tax,
                        len(bot.profits),
                        max(bot.profits),
                        min(bot.profits))
                    slack.notify(message)
                else:
                    message = "ポジションを維持！"
                    slack.notify(message)

            del forecast_data
            gc.collect()

        except Exception as e:
            logger.exception(e)

        time.sleep(sleep_second)


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
