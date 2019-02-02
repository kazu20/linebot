# linebot

# 必要条件
Botを動かすのに必要な条件は以下のとおり。

## アカウント
このBotを動かすには、以下サービスのアカウントが必要になる。どちらも無料で使えるので、事前に準備をしておく。

Google Natural Language API (https://cloud.google.com/natural-language/)

LINE Developers(https://developers.line.biz/ja/)

## 動作環境
動作確認した環境はは以下のとおり。

- Ubuntu 8.04.1 LTS
- Docker 18.06.1-ce
- Docker-compose 1.23.2

# インストール
Dockerイメージをビルドする。ビルド時にGoogle Natural Language APIのアクセスキーをイメージ内にコピーをするので、事前にPrivate.jsonとしてダウンロードしておく。

```
$ git clone https://github.com/kazu20/linebot/
$ ダウンロードしたPrivate.jsonをDockerfileと同じディレクトリにコピーする。
$ docker build -t YOUR_IMAGE_NAME
```
イメージができたらdocker-compose.ymlにLINE_TOKEN、LINE_CHANNEL_SECRETを指定して、docker-compose upする。
 ```
 $ docker-compose up -d
 ```
