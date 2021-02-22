from flask import Flask, request, abort
import requests as rq
import schedule
import time
import datetime as dt
from datetime import datetime, timedelta, timezone
from GetTicketStatus import GTS
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
)
from threading import Thread
import os


try:
    from local_settings import *
except ImportError:
    pass

app = Flask(__name__)

# 環境変数取得
if os.getenv("YOUR_CHANNEL_ACCESS_TOKEN"):
    YOUR_CHANNEL_ACCESS_TOKEN = os.getenv("YOUR_CHANNEL_ACCESS_TOKEN")
    YOUR_CHANNEL_SECRET = os.getenv("YOUR_CHANNEL_SECRET")
# LINE Developersで設定されているアクセストークンとChannel Secretをを取得し、設定します。

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

JST = timezone(timedelta(hours=+9), "JST")

LastExecutionTime = None
LastObservationResults = None

ObservationRestarttime = None
ObservationStatus = True
ObservationTime = 0
BaseObservationTime = 1
LowObservationTime = 5

start_str = '00:00:00'
end_str = '12:00:00'
start = dt.datetime.strptime(start_str, '%H:%M:%S')
end = dt.datetime.strptime(end_str, '%H:%M:%S')

ResponseTime = 0
ResponseTimeMin = 99999999

ExceptionInformation=None


@app.route("/")
def main():
    global LastObservationResults, ExceptionInformation
    Text = "<title>東京ディズニーリゾートチケット再販通知ステータス</title>"
    if ObservationStatus:
        if LastExecutionTime:
            LastExecutionTimeToStr = LastExecutionTime.strftime("%Y/%m/%d %H:%M:%S")
            Text += "<h1>ステータス: <font color='lime'>●</font></h1>"
            if ResponseTimeMin - ResponseTime <= 3:
                Text += f"<h2>現在{ObservationTime}分間隔で正常に監視を行っております。</h2>"
            elif ResponseTimeMin - ResponseTime >= 20:
                Text += f"<h2>現在{ObservationTime}分間隔で監視を行っておりますが通常時に比べレスポンス時間が長くなっておりサイトの混雑が予想されます。</h2>"
            Text += f"<p>本Botは基本的に{BaseObservationTime}分間隔で再販監視を行っておりますが、サーバへの負荷を最小限に抑えるため{start_str}～{end_str}は{LowObservationTime}分間隔で監視を行っております。</p>"
            Text += f"<p>現在{BaseObservationTime}分間隔で監視を行っておりますが通常時に比べレスポンス時間が長くなっておりサイトの混雑が予想されます。</p>"
            Text += f"<h3>最終監視時刻: {LastExecutionTimeToStr}</h3>"
            Text += "<h3>Response Information</h3>"
            Text += f"<p>Response Time: {ResponseTime}<br>"
            Text += f"Minimum Response Time: {ResponseTimeMin}<br>"
            Text += f"Response Time Differential: {ResponseTime - ResponseTimeMin}</p>"
            Text += "<h3>Response Details</h3>"
            if type(LastObservationResults) != str:
                for Key, Values in LastObservationResults.items():
                    Text += f"<h4>{Key}</h4>"
                    for Value in Values:
                        Text += f"<p>{Value}</p>"
            else:
                Text += f"<p>{LastObservationResults}</p>"
        else:
            Text += "<h1>ステータス: <font color='gray'>●</font></h1>"
            Text += "<h2>現在起動中です。</h2>"
    else:
        ObservationRestarttimeToStr = ObservationRestarttime.strftime(
            "%Y/%m/%d %H:%M:%S"
        )
        if ObservationTime == 120:
            Text += "<h1>ステータス: <font color='red'>▲</font></h1>"
            Text += "<h2>現在東京ディズニーリゾートオンライン予約・購入サイトのメンテナンスのため監視を一時停止しております。</h2>"
            Text += f"<h2>監視再開予定時刻: {ObservationRestarttimeToStr}\n</h2>"
            if LastExecutionTime:
                LastExecutionTimeToStr = LastExecutionTime.strftime("%Y/%m/%d %H:%M:%S")
                Text += f"<h3>最終監視時刻: {LastExecutionTimeToStr}</h3>"
            Text += "<h3>Response Details</h3>"
            Text += f"<p> {ExceptionInformation}</p>"
        elif ObservationTime == 20:
            Text += "<h1>ステータス: <font color='red'>▲</font></h1>"
            Text += "<h2>現在東京ディズニーリゾートオンライン予約・購入サイトへのリクエスト時間が長くなっているため監視を一時停止しております。再販の可能性もあるため予約・購入サイトへのアクセスをおすすめします。</h2>"
            Text += f"<h2>監視再開予定時刻: {ObservationRestarttimeToStr}\n</h2>"
            if LastExecutionTime:
                LastExecutionTimeToStr = LastExecutionTime.strftime("%Y/%m/%d %H:%M:%S")
                Text += f"<h3>最終監視時刻: {LastExecutionTimeToStr}</h3>"
            Text += "<h3>Response Details</h3>"
            Text += f"<p> {ExceptionInformation}</p>"
        else:
            Text += "<h1>ステータス: <font color='red'>✖︎</font></h1>"
            Text += (
                "<h2>現在東京ディズニーリゾートオンライン予約・購入サイトへのアクセス集中による403エラー回避のため一時停止しております。</h2>"
            )
            Text += f"<h2>監視再開予定時刻: {ObservationRestarttimeToStr}</h2>"
            if LastExecutionTime:
                LastExecutionTimeToStr = LastExecutionTime.strftime("%Y/%m/%d %H:%M:%S")
                Text += f"<h3>最終監視時刻: {LastExecutionTimeToStr}</h3>"
            Text += "<h3>Response Details</h3>"
            Text += f"<p> {ExceptionInformation}</p>"
    return Text


## 1 ##
# Webhookからのリクエストをチェックします。
@app.route("/callback", methods=["POST"])
def callback():
    # リクエストヘッダーから署名検証のための値を取得します。
    signature = request.headers["X-Line-Signature"]

    # リクエストボディを取得します。
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    # 署名を検証し、問題なければhandleに定義されている関数を呼び出す。
    try:
        handler.handle(body, signature)
    # 署名検証で失敗した場合、例外を出す。
    except InvalidSignatureError:
        abort(400)
    # handleの処理を終えればOK
    return "OK"


def run():
    app.run(host="0.0.0.0", port=8080)


## 2 ##
###############################################
# LINEのメッセージの取得と返信内容の設定(オウム返し)
###############################################

# LINEでMessageEvent（普通のメッセージを送信された場合）が起こった場合に、
# def以下の関数を実行します。
# reply_messageの第一引数のevent.reply_tokenは、イベントの応答に用いるトークンです。
# 第二引数には、linebot.modelsに定義されている返信用のTextSendMessageオブジェクトを渡しています。


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text=event.message.text)
    )  # ここでオウム返しのメッセージを返します。
    # line_bot_api.broadcast()


def Action(Status, Datas):
    # 4: サーバメンテナンスパラメータ
    if Status == 4:
        messages = TextSendMessage(text="サーバメンテナンス中のため2時間監視を停止します。")
        line_bot_api.broadcast(messages=messages)
    # 3: リクエストタイムアウトパラメータ
    elif Status == 3:
        messages = TextSendMessage(text="サーバへのリクエスト時間が非常に長くなっています。再販の可能性あり。")
        line_bot_api.broadcast(messages=messages)
    # 2: 403エラーパラメータ
    elif Status == 2:
        messages = TextSendMessage(text="アクセス集中による403エラー回避のため1時間監視を停止します。")
        line_bot_api.broadcast(messages=messages)
    # 1: 再販確認時パラメータ
    elif Status == 1:
        message = "再販あり\n"
        for Key in Datas.keys():
            if len(Datas[Key]):
                message += f"東京ディズニー{Key}: {len(Datas[Key])}件\n"
            for Data in Datas[Key]:
                message += f"{Data}\n"
        messages = TextSendMessage(text=message)
        line_bot_api.broadcast(messages=messages)
    # 0: 平常時パラメータ
    else:
        pass


def StateSwitch():
    messages = TextSendMessage(text="監視を再開します。")
    line_bot_api.broadcast(messages=messages)


def job():
    global ObservationStatus, ObservationTime, LastExecutionTime, ObservationRestarttime, LastObservationResults, BaseObservationTime,ResponseTime, ResponseTimeMin, ExceptionInformation
    if ObservationStatus == False:
        ObservationStatus = True
        StateSwitch()
    Status, ResponseTime, Datas = GTS()
    Action(Status, Datas)
    if ResponseTime < ResponseTimeMin:
        ResponseTimeMin = ResponseTime
    if Status == 4:
        ObservationStatus = False
        ObservationTime = 120
        schedule.clear()
        schedule.every(ObservationTime).minutes.do(job)
        ObservationRestarttime = datetime.now(JST) + dt.timedelta(minutes=ObservationTime)
        ExceptionInformation = Datas
    elif Status == 3:
        ObservationStatus = False
        ObservationTime = 20
        schedule.clear()
        schedule.every(ObservationTime).minutes.do(job)
        ObservationRestarttime = datetime.now(JST) + dt.timedelta(minutes=ObservationTime)
        ExceptionInformation = Datas
    elif Status == 2:
        ObservationStatus = False
        ObservationTime = 60
        schedule.clear()
        schedule.every(ObservationTime).minutes.do(job)
        ObservationRestarttime = datetime.now(JST) + dt.timedelta(minutes=ObservationTime)
        ExceptionInformation = Datas
    else:
        LastObservationResults = Datas
        now = dt.datetime.now()
        if start.time() <= now.time() <= end.time():
            ObservationTime = LowObservationTime
        else:
            ObservationTime = BaseObservationTime
        schedule.clear()
        schedule.every(ObservationTime).minutes.do(job)
        LastExecutionTime = datetime.now(JST)



# ポート番号の設定
if __name__ == "__main__":
    server = Thread(target=run)
    server.start()

    job()
    ObservationTime = BaseObservationTime
    messages = TextSendMessage(text=f"再販監視が開始されました。(監視周期: {ObservationTime}分)")
    line_bot_api.broadcast(messages=messages)
    # 1分ごとに実行
    schedule.every(ObservationTime).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
