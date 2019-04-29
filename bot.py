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

    # メッセージのsentimentに合わせて、応答を返す
    if sentiment.score > 0.8:
        text = "激嬉"
    elif sentiment.score > 0.3:
        text = "嬉"
    elif sentiment.score < -0.3:
        text = "怒"
    else:
        text = "普通"

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
