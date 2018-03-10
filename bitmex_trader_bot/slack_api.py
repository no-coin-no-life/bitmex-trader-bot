import requests

import slackweb

import os


class SlackApi(object):
    """
    Slack APIを操作するクラス
    """

    def notify(self, text):
        """
        slackのWebhookを利用して通知する

        :param str text: 通知内容
        """

        url = os.environ["BITMEX_TRADER_BOT_SLACK_WEBHOOK_URL"]
        slack = slackweb.Slack(url=url)
        slack.notify(text=text)

    def upload_image(self, file_path):
        """
        指定のslackチャンネルへ画像をアップロードする

        :param str file_path: アップロードするファイルパス
        """

        url = "https://slack.com/api/files.upload"
        token = os.environ["BITMEX_TRADER_BOT_SLACK_TOKEN"]
        files = {"file": open(file_path.format(type), "rb")}
        param = {"token": token}
        requests.post(url=url, params=param, files=files)
