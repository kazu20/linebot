# Imports the Google Cloud client library
from google.cloud import datastore
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
from flask import Flask, request, abort

# Imports LineBot
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    ImageMessage, StickerMessage,
)
import os
import numpy as np

# Line MessagingAPI
line_bot_api = LineBotApi(os.environ.get('LINE_TOKEN'))
handler = WebhookHandler(os.environ.get('LINE_CHANNEL_SECRET'))

app = Flask(__name__)


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    # Instantiates a client
    client = language.LanguageServiceClient()

    # The text to analyze
    document = types.Document(
        content=event.message.text,
        type=enums.Document.Type.PLAIN_TEXT)

    # set profile
    userId = event.source.user_id
    profile = line_bot_api.get_profile(userId)
    timestamp = event.timestamp

    # Detects the sentiment of the text
    sentiment = client.analyze_sentiment(document=document).document_sentiment

    # Create Datastore Entity
    datastore_client = datastore.Client()
    kind = 'Sentiment'
    task_key = datastore_client.key(kind)

    Sentiment = datastore.Entity(key=task_key)
    Sentiment['sentiment'] = sentiment.score
    Sentiment['userId'] = userId
    Sentiment['user_display_name'] = profile.display_name
    Sentiment['timestamp'] = timestamp

    datastore_client.put(Sentiment)

    # 特定のキーワード（hogehoge)がきたら、メッセージのsentimentの統計を主力する
    if event.message.text == 'hogehoge':
        # sentiment > 0.5の場合はポジティブ
        # sentiiment < -0.5の場合はネガティブ
        # -0.5 < sentiment < 0.5の場合はニュートラル
        # 最新100件についての割合を出す
        query = datastore_client.query(kind='Sentiment')
        query.add_filter('userId', '=', userId)
        result = list(query.fetch())

        average = [0]
        for sentiment_list in result:
            average.append(sentiment_list['sentiment'])
        sentiment_ave = np.array(average)

        positive_num = np.sum(sentiment_ave > 0.5 )
        positive = (positive_num/sentiment_ave.size) * 100
        positive = round(positive, 1)


        negative_num = np.sum(sentiment_ave < 0.5 )
        negative = (negative_num/sentiment_ave.size) * 100
        negative = round(negative, 1)

        neutral_num = sentiment_ave.size - positive_num - negative_num
        neutral = (neutral_num/sentiment_ave.size) * 100
        neutral = round(neutral, 1)

        positive = str(positive)
        negative = str(negative)
        neutral = str(neutral)

        text = 'positive:' + positive  + 'negative: ' + negative  + 'neutral: ' + neutral
        print(text)
    else:
        # メッセージのsentimentに合わせて、応答を返す
        if sentiment.score > 0.5:
            text = 'ポジティブ:' + str(round(sentiment.score,1))
        elif sentiment.score < -0.5:
            text = 'ネガティブ:' + str(round(sentiment.score,1))
        else:
            text = 'ニュートラル:' + str(round(sentiment.score,1))

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text))


@handler.add(MessageEvent, message=StickerMessage)
def handle_sticker(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="スタンプはスタンプは使えません"))


@handler.default()
def default(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="テキストメッセージを送ってください。"))


if __name__ == "__main__":
    app.run(host='0.0.0.0')
