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

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):

    # Create Datastore Entity
    datastore_client = datastore.Client()
    kind = 'Sentiment'
    task_key = datastore_client.key(kind)

    # set profile
    if event.source.type == 'user':
        userId = event.source.user_id
        profile = line_bot_api.get_profile(userId)
    elif event.source.type == 'room':
        userId = event.source.user_id
        roomId = event.source.room_id
        profile = line_bot_api.get_room_member_profile(roomId, userId)
    elif event.source.type == 'groop':
        userId = event.source.user_id
        groupId = event.source.group_id
        profile = line_bot_api.get_group_member_profile(groupId, userId)

    # 特定のキーワード（hogehoge)がきたら、メッセージのsentimentの統計を主力する
    if event.message.text == 'hogehoge':
        # sentiment > 0.5の場合はポジティブ
        # sentiiment < -0.5の場合はネガティブ
        # -0.5 < sentiment < 0.5の場合はニュートラル
        # 最新200件についての割合を出す
        query = datastore_client.query(kind='Sentiment')
        query.add_filter('userId', '=', userId)
        query.order = ['-timestamp']
        result = list(query.fetch(limit=200))

        # queryの結果からsentimentだけのnumpy arrayを作成
        sentiment_list = [0]
        for result_list in result:
            sentiment_list.append(result_list['sentiment'])
        sentiment_num = np.array(sentiment_list)

        # sentiment > 0.5となる要素の割合
        positive_num = np.sum(sentiment_num > 0.5)
        positive = (positive_num/sentiment_num.size) * 100
        positive = round(positive, 1)

        # sentiment < -0.5となる要素の割合
        negative_num = np.sum(sentiment_num < -0.5)
        negative = (negative_num/sentiment_num.size) * 100
        negative = round(negative, 1)

        # -0.5 < sentiment < 0.5となる要素の割合
        neutral_num = sentiment_num.size - positive_num - negative_num
        neutral = (neutral_num/sentiment_num.size) * 100
        neutral = round(neutral, 1)

        # それぞれの割合を文字列変換
        positive = str(positive)
        negative = str(negative)
        neutral = str(neutral)

        text = profile.display_name + 'さんはポジティブな発言が' + positive + '%、' + \
            'ネガティブな発言が' + negative + '%、' + 'その他の発言が' + neutral + '%でした。'

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=text))
    else:

       # Instantiates a client
        client = language.LanguageServiceClient()

        # The text to analyze
        document = types.Document(
            content=event.message.text,
            type=enums.Document.Type.PLAIN_TEXT)

        # Detects the sentiment of the text
        sentiment = client.analyze_sentiment(
            document=document).document_sentiment

        Sentiment = datastore.Entity(key=task_key)
        Sentiment['sentiment'] = sentiment.score
        Sentiment['userId'] = userId
        Sentiment['user_display_name'] = profile.display_name
        Sentiment['timestamp'] = event.timestamp

        datastore_client.put(Sentiment)


@handler.default()
def default(event):
    return 0


if __name__ == "__main__":
    app.run(host='0.0.0.0')
