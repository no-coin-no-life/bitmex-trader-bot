# bitmex-trader-bot

BitMEXで動作する自動トレードBotを作ってるよ！
まだ実際に注文はできないし、利益はでません。

※チャート分析は過去の価格情報を時系列解析にかけていますが、利益がでる保証はありません。


## できること

- パラメータ指定(秒)で定期実行
- XBT(BTC)/USDの価格チェック
- 時系列解析を利用してトレンド判断
- 指値・成行き注文(した気になれる)
- 現ポジションの利益確認
- 時系列解析結果のグラフをSlackへ通知
- ポジションや損益・手数料情報などをSlack通知


## やりたいこと

https://github.com/no-coin-no-life/bitmex-trader-bot/issues


##　利用方法

```
git clone git@github.com:no-coin-no-life/bitmex-trader-bot.git
pip install -r requirements.txt
pip install -e .
cp .env.sample .env
vi .env
python bin/main.py 360
```

Windowsの場合、prophetがインストールできない可能性があります。
その場合は、下記を参照。

https://facebook.github.io/prophet/docs/installation.html


## 参考にした情報(感謝感謝)

### 環境構築

#### ファイル構成

- https://qiita.com/Kensuke-Mitsuzawa/items/7717f823df5a30c27077
- http://blog.masudak.net/entry/2015/01/13/234000

#### バッチ作成

- https://qiita.com/fetaro/items/77cb5571c472eac85031

#### 設定

- https://qiita.com/hedgehoCrow/items/2fd56ebea463e7fc0f5b
- https://github.com/theskumar/python-dotenv
- https://qiita.com/suto3/items/db6f05f943cc2ea2ef5

#### テスト

- https://qiita.com/_yama3_/items/b0edf2e97d6eefd7a3e1
- https://qiita.com/FGtatsuro/items/0efebb9b58374d16c5f0
- https://qiita.com/akidroid/items/d81297c90d3a25366c2a
- https://qiita.com/mwakizaka/items/e51c604155633ccd33dd

#### 自動トレード

- https://qiita.com/reon777/items/21ed87f19cdd50f08bd9
- https://note.mu/akagami/n/n0af0a96c261f


#### 時系列解析

- https://qiita.com/shion1118/items/2979e1cd465a59aeb95c
- http://tekenuko.hatenablog.com/entry/2017/10/18/002229
- https://www.slideshare.net/hoxo_m/prophet-facebook-76285278

#### グラフ作成

- https://qiita.com/koichifukushima/items/e63e642431db92178188
- http://misaki-yuyyuyu.hatenablog.com/entry/2017/07/29/200302

#### SlackAPI

- https://qiita.com/ykhirao/items/0d6b9f4a0cc626884dbb

#### Python

- https://qiita.com/progrommer/items/abd2276f314792c359da