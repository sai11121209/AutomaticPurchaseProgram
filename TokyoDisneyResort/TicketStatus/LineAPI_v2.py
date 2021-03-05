from flask import Flask, request, abort
import regex as re
import requests as rq
import schedule
import time
import pytz
import json
import jpholiday
import calendar
import collections
import twitter
import datetime as dt
from datetime import datetime, timedelta, timezone
from GetTicketStatus import GTS
from dateutil.relativedelta import relativedelta
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    ButtonsTemplate,
    TextMessage,
    TextSendMessage,
    MessageAction,
    PostbackAction,
    TemplateSendMessage,
    PostbackEvent,
    ImagemapSendMessage,
    MessageImagemapAction,
    BaseSize,
    ImagemapArea,
)
from threading import Thread
import os


try:
    from local_settings import *
except ImportError:
    pass

app = Flask(__name__, static_folder="./static")
print(app.url_map)
# 環境変数取得
if os.getenv("YOUR_CHANNEL_ACCESS_TOKEN"):
    YOUR_CHANNEL_ACCESS_TOKEN = os.getenv("YOUR_CHANNEL_ACCESS_TOKEN")
    YOUR_CHANNEL_SECRET = os.getenv("YOUR_CHANNEL_SECRET")
    CONSUMER_KEY = os.getenv("CONSUMER_KEY")
    CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
    TOKEN = os.getenv("TOKEN")
    TOKEN_SECRET = os.getenv("TOKEN_SECRET")
# LINE Developersで設定されているアクセストークンとChannel Secretをを取得し、設定します。

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

JST = timezone(timedelta(hours=+9), "JST")

auth = twitter.OAuth(
    consumer_key=CONSUMER_KEY,
    consumer_secret=CONSUMER_SECRET,
    token=TOKEN,
    token_secret=TOKEN_SECRET,
)

t = twitter.Twitter(auth=auth)


LastExecutionTime = None
LastObservationResults = None

ObservationRestarttime = None
ObservationStatus = True
ObservationTime = 0
BaseObservationTime = 2
LowObservationTime = 5
MaintenanceObservationTime = 120

start_str = "00:00"
end_str = "12:00"
start = dt.datetime.strptime(start_str, "%H:%M")
end = dt.datetime.strptime(end_str, "%H:%M")
maintenance_start_str = "03:00"
maintenance_end_str = "05:00"
maintenance_start = dt.datetime.strptime(maintenance_start_str, "%H:%M")
maintenance_end = dt.datetime.strptime(maintenance_end_str, "%H:%M")

# 旧種別平日ランド1Dayチケット TOZZ1D20910PT [0]
# 新種別休日ランド1Dayチケット TOZZ1D21002PT [1]
# 新種別平日ランド1Dayチケット TOZZ1D21000PT [2]
# 旧種別平日シー1Dayチケット TOZZ1D20911PT [0]
# 新種別休日シー1Dayチケット TOZZ1D21003PT [1]
# 新種別平日シー1Dayチケット TOZZ1D21001PT [2]
ParksPara = {
    "ランド": ["TOZZ1D20910PT", "TOZZ1D21002PT", "TOZZ1D21000PT"],
    "シー": ["TOZZ1D20911PT", "TOZZ1D21003PT", "TOZZ1D21001PT"],
}

# チケット種別変更日
ChangeTicketTypeDate = dt.datetime(
    2021, 3, 20, 0, 0, tzinfo=pytz.timezone("Asia/Tokyo")
)
# 特別価格指定日
SpecialTicketTypeDate_start = dt.datetime(
        2021, 3, 29, 0, 0, tzinfo=pytz.timezone("Asia/Tokyo")
    )
SpecialTicketTypeDate_end = dt.datetime(
    2021, 4, 2, 23, 59, tzinfo=pytz.timezone("Asia/Tokyo")
)

ResponseTime = 0
ResponseTimeMin = 3

ExceptionInformation = None

UserData = {}


@app.route("/")
def main():
    global LastObservationResults, ExceptionInformation
    MessageLimit = int(
        rq.get(
            "https://api.line.me/v2/bot/message/quota/consumption",
            headers={"Authorization": "Bearer " + YOUR_CHANNEL_ACCESS_TOKEN},
        ).json()["totalUsage"]
    )
    Text = "<title>東京ディズニーリゾートチケット再販通知ステータス</title>"
    if ObservationStatus:
        if LastExecutionTime:
            LastExecutionTimeToStr = LastExecutionTime.strftime("%Y/%m/%d %H:%M:%S")
            Text += "<h1>ステータス: <font color='lime'>●</font></h1>"
            if ResponseTime - ResponseTimeMin <= 3:
                Text += f"<h2>現在{ObservationTime}分間隔で正常に監視を行っております。</h2>"
            elif ResponseTime - ResponseTimeMin > 3:
                Text += f"<h2>現在{ObservationTime}分間隔で監視を行っておりますが通常時に比べレスポンス時間が長くなっておりサイトの混雑が予想されます。</h2>"
            Text += f"<p>本Botは基本的に{BaseObservationTime}分間隔で再販監視を行っておりますが、サーバへの負荷を最小限に抑えるため{start_str}～{end_str}の時間帯は{LowObservationTime}分間隔で監視を行っております。</p>"
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
    Text += "<h3>Line Bot Information</h3>"
    Text += f"<p>Message Remaining: {1000-MessageLimit}</p>"
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
    except:
        pass
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
    global UserData
    UserId = event.source.user_id
    if event.message.text == "> チケットURL生成":
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(
                alt_text="Buttons template",
                template=ButtonsTemplate(
                    title="パーク選択",
                    alt_text="パーク選択",
                    text="チケットを取りたいパークを選択してください。",
                    actions=[
                        PostbackAction(
                            label="東京ディズニーランド",
                            display_text="東京ディズニーランド",
                            data=json.dumps(
                                {event.source.user_id: {"status": 0, "park": "01"}}
                            ),
                        ),
                        PostbackAction(
                            label="東京ディズニーシー",
                            display_text="東京ディズニーシー",
                            data=json.dumps(
                                {event.source.user_id: {"status": 0, "park": "02"}}
                            ),
                        ),
                    ],
                ),
            ),
        )
    p = re.compile(r"\p{Script=Han}+: [0-9]")
    try:
        search_start = datetime.now(pytz.timezone("Asia/Tokyo"))
        search_end = (
            datetime.now(pytz.timezone("Asia/Tokyo"))
            + relativedelta(months=1)
            + dt.timedelta(days=1)
        )
        now = datetime.now(pytz.timezone("Asia/Tokyo"))
        now_str = now.strftime("%Y-%m-%d")
        search_start_str = search_start.strftime("%Y-%m-%d")
        search_end_str = search_end.strftime("%Y-%m-%d")
        match = p.fullmatch(event.message.text).group().split(" ")
        if match[0] == "大人:":
            UserData[UserId]["status"] = 2
            UserData[UserId]["adult"] = int(match[1])
            imageMap(event, "中人", 5 - UserData[UserId]["adult"])
        if match[0] == "中人:":
            UserData[UserId]["status"] = 3
            UserData[UserId]["junior"] = int(match[1])
            imageMap(
                event, "小人", 5 - UserData[UserId]["adult"] - UserData[UserId]["junior"]
            )
        if match[0] == "小人:":
            UserData[UserId]["status"] = 4
            UserData[UserId]["child"] = int(match[1])
            line_bot_api.reply_message(
                event.reply_token,
                TemplateSendMessage(
                    alt_text="Buttons template",
                    template=ButtonsTemplate(
                        title="日付選択",
                        alt_text="日付選択",
                        text="チケットを取りたい日付選択してください。",
                        actions=[
                            {
                                "type": "datetimepicker",
                                "label": "日付を選択してください。",
                                "data": "action=settime",
                                "mode": "date",
                                "initial": now_str,
                                "max": search_end_str,
                                "min": search_start_str,
                            }
                        ],
                    ),
                ),
            )
    except:
        pass
    print(UserData)


@handler.add(PostbackEvent)
def on_postback(event):
    global UserData
    UserId = event.source.user_id
    try:
        UserData[UserId].update(status=5, date=event.postback.params["date"])
        print(UserData[UserId]["date"])
        selectday = dt.datetime.strptime(
            UserData[UserId]["date"] + "+0900", "%Y-%m-%d%z"
        )
        day_index = selectday.weekday()
        park = UserData[UserId]["park"]
        if park == "01":
            park_name = "東京ディズニーランド"
        else:
            park_name = "東京ディズニーシー"
        junior = UserData[UserId]["junior"]
        adult = UserData[UserId]["adult"]
        child = UserData[UserId]["child"]
        day = UserData[UserId]["date"].replace("-", "")
        if selectday < ChangeTicketTypeDate:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"{park_name}\n1Day\n{UserData[UserId]['date']}\n大人: {adult}人\n中人: {junior}人\n小人: {child}人\nhttps://reserve.tokyodisneyresort.jp/sp/ticket/search/?parkTicketGroupCd=01&route=2&selectParkDay1={park}&useDays=1&numOfJunior={junior}&useDateFrom={day}&parkTicketSalesForm=1&numOfAdult={adult}&numOfChild={child}"
                ),
            )
        elif (
            jpholiday.is_holiday_name(selectday)
            or calendar.day_name[day_index] == "Saturday"
            or calendar.day_name[day_index] == "Sunday"
            or SpecialTicketTypeDate_start <= selectday <= SpecialTicketTypeDate_end
        ):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"{park_name}\n休日1Day\n{UserData[UserId]['date']}\n大人: {adult}人\n中人: {junior}人\n小人: {child}人\nhttps://reserve.tokyodisneyresort.jp/sp/ticket/search/?parkTicketGroupCd=012&route=2&selectParkDay1={park}&useDays=1&numOfJunior={junior}&useDateFrom={day}&parkTicketSalesForm=1&numOfAdult={adult}&numOfChild={child}"
                ),
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"{park_name}\n平日1Day\n{UserData[UserId]['date']}\n大人: {adult}人\n中人: {junior}人\n小人: {child}人\nhttps://reserve.tokyodisneyresort.jp/sp/ticket/search/?parkTicketGroupCd=011&route=2&selectParkDay1={park}&useDays=1&numOfJunior={junior}&useDateFrom={day}&parkTicketSalesForm=1&numOfAdult={adult}&numOfChild={child}"
                ),
            )
    except:
        deepupdate(UserData, json.loads(event.postback.data))
    if UserData[UserId]["status"] == 0:
        imageMap(event, "大人", 5)


def Action(Status, Datas):
    # 4: サーバメンテナンスパラメータ
    if Status == 4:
        message = "サーバメンテナンス中のため2時間監視を停止します。\n監視再開時間等の情報を確認するには'監視ステータス確認'から確認できます。"
        messages = TextSendMessage(text=message)
        try:
            t.statuses.update(status=message)
        except:
            print("Twittererror")
        line_bot_api.broadcast(messages=messages)
    # 3: リクエストタイムアウトパラメータ
    elif Status == 3:
        message = "サーバへのリクエスト時間が非常に長くなっているため40分間監視を一時停止します。\n再販の可能性あり。\n監視再開時間等の情報を確認するには'監視ステータス確認'から確認できます。"
        messages = TextSendMessage(text=message)
        try:
            t.statuses.update(status=message)
        except:
            print("Twittererror")
        line_bot_api.broadcast(messages=messages)
    # 2: 403エラーパラメータ
    elif Status == 2:
        message = (
            "アクセス集中による403エラー回避のため1時間監視を停止します。\n監視再開時間等の情報を確認するには'監視ステータス確認'から確認できます。"
        )
        messages = TextSendMessage(text=message)
        try:
            t.statuses.update(status=message)
        except:
            print("Twittererror")
        line_bot_api.broadcast(messages=messages)
    # 1: 再販確認時パラメータ
    elif Status == 1:
        message = "再販あり\n以下直近20件\n"
        message += "￮￮/×× L S"
        mergeDatas = []
        mergeDatas.extend(Datas["ランド"])
        mergeDatas.extend(Datas["シー"])
        mergeDatas = sorted(list(set(mergeDatas)))[:20]
        count = 0
        for mergeData in mergeDatas:
            if mergeData in Datas["ランド"]:
                tdl = "○"
            else:
                tdl = "×"
            if mergeData in Datas["シー"]:
                tds = "○"
            else:
                tds = "×"
            count += 1
            if count < 20:
                message += f"\n{mergeData[5:]}{tdl}{tds}"
                line_message = message
            else:
                line_message += f"\n{mergeData[5:]}{tdl}{tds}"
        message += "\nhttps://reserve.tokyodisneyresort.jp/sp/ticket/search/"
        print(message)
        messages = TextSendMessage(text=line_message)
        try:
            t.statuses.update(status=message)
        except:
            print("Twittererror")
        line_bot_api.broadcast(messages=messages)
    # 0: 平常時パラメータ
    else:
        pass


def StateSwitch():
    message = "監視を再開します。"
    messages = TextSendMessage(text=message)
    try:
        t.statuses.update(status=message)
    except:
        print("Twittererror")
    line_bot_api.broadcast(messages=messages)


def job():
    global ObservationStatus, ObservationTime, LastExecutionTime, ObservationRestarttime, LastObservationResults, BaseObservationTime, ResponseTime, ResponseTimeMin, ExceptionInformation
    if ObservationStatus == False:
        ObservationStatus = True
        StateSwitch()
    Status, ResponseTime, Datas = GTS(ParksPara)
    Action(Status, Datas)
    if ResponseTime < ResponseTimeMin:
        ResponseTimeMin = ResponseTime
    if Status == 4:
        ObservationStatus = False
        ObservationTime = 120
        schedule.clear()
        schedule.every(ObservationTime).minutes.do(job)
        ObservationRestarttime = datetime.now(JST) + dt.timedelta(
            minutes=ObservationTime
        )
        ExceptionInformation = Datas
    elif Status == 3:
        ObservationStatus = False
        ObservationTime = 40
        schedule.clear()
        schedule.every(ObservationTime).minutes.do(job)
        ObservationRestarttime = datetime.now(JST) + dt.timedelta(
            minutes=ObservationTime
        )
        ExceptionInformation = Datas
    elif Status == 2:
        ObservationStatus = False
        ObservationTime = 60
        schedule.clear()
        schedule.every(ObservationTime).minutes.do(job)
        ObservationRestarttime = datetime.now(JST) + dt.timedelta(
            minutes=ObservationTime
        )
        ExceptionInformation = Datas
    else:
        LastObservationResults = Datas
        now = datetime.now(pytz.timezone("Asia/Tokyo"))
        if start.time() <= now.time() <= end.time():
            ObservationTime = LowObservationTime
        if maintenance_start.time() <= now.time() <= maintenance_end.time():
            ObservationTime = MaintenanceObservationTime
        else:
            ObservationTime = BaseObservationTime
        schedule.clear()
        schedule.every(ObservationTime).minutes.do(job)
        LastExecutionTime = datetime.now(JST)
    print(ObservationTime)


def deepupdate(dict_base, other):
    for k, v in other.items():
        if isinstance(v, collections.Mapping) and k in dict_base:
            deepupdate(dict_base[k], v)
        else:
            dict_base[k] = v


def imageMap(event, type, n):
    # http://drive.google.com/uc?export=view&id={id}
    if n == 5:
        url = "https://AutomaticPurchaseProgram.sai11121209.repl.co/static/imagemap_number_of_people_5"
        action = [
            MessageImagemapAction(
                text=f"{type}: 0", area=ImagemapArea(x=0, y=0, width=346, height=520)
            ),
            MessageImagemapAction(
                text=f"{type}: 1", area=ImagemapArea(x=347, y=0, width=346, height=520)
            ),
            MessageImagemapAction(
                text=f"{type}: 2", area=ImagemapArea(x=694, y=0, width=346, height=520)
            ),
            MessageImagemapAction(
                text=f"{type}: 3", area=ImagemapArea(x=0, y=520, width=346, height=520)
            ),
            MessageImagemapAction(
                text=f"{type}: 4",
                area=ImagemapArea(x=347, y=520, width=346, height=520),
            ),
            MessageImagemapAction(
                text=f"{type}: 5",
                area=ImagemapArea(x=693, y=520, width=346, height=520),
            ),
        ]
    elif n == 4:
        url = "https://AutomaticPurchaseProgram.sai11121209.repl.co/static/imagemap_number_of_people_4"
        action = [
            MessageImagemapAction(
                text=f"{type}: 0", area=ImagemapArea(x=0, y=0, width=346, height=520)
            ),
            MessageImagemapAction(
                text=f"{type}: 1", area=ImagemapArea(x=347, y=0, width=346, height=520)
            ),
            MessageImagemapAction(
                text=f"{type}: 2", area=ImagemapArea(x=694, y=0, width=346, height=520)
            ),
            MessageImagemapAction(
                text=f"{type}: 3", area=ImagemapArea(x=0, y=520, width=346, height=520)
            ),
            MessageImagemapAction(
                text=f"{type}: 4",
                area=ImagemapArea(x=347, y=520, width=346, height=520),
            ),
        ]
    elif n == 3:
        url = "https://AutomaticPurchaseProgram.sai11121209.repl.co/static/imagemap_number_of_people_3"
        action = [
            MessageImagemapAction(
                text=f"{type}: 0", area=ImagemapArea(x=0, y=0, width=346, height=520)
            ),
            MessageImagemapAction(
                text=f"{type}: 1", area=ImagemapArea(x=347, y=0, width=346, height=520)
            ),
            MessageImagemapAction(
                text=f"{type}: 2", area=ImagemapArea(x=694, y=0, width=346, height=520)
            ),
            MessageImagemapAction(
                text=f"{type}: 3", area=ImagemapArea(x=0, y=520, width=346, height=520)
            ),
        ]
    elif n == 2:
        url = "https://AutomaticPurchaseProgram.sai11121209.repl.co/static/imagemap_number_of_people_2"
        action = [
            MessageImagemapAction(
                text=f"{type}: 0", area=ImagemapArea(x=0, y=0, width=346, height=520)
            ),
            MessageImagemapAction(
                text=f"{type}: 1", area=ImagemapArea(x=347, y=0, width=346, height=520)
            ),
            MessageImagemapAction(
                text=f"{type}: 2", area=ImagemapArea(x=694, y=0, width=346, height=520)
            ),
        ]
    elif n == 1:
        url = "https://AutomaticPurchaseProgram.sai11121209.repl.co/static/imagemap_number_of_people_1"
        action = [
            MessageImagemapAction(
                text=f"{type}: 0", area=ImagemapArea(x=0, y=0, width=346, height=520)
            ),
            MessageImagemapAction(
                text=f"{type}: 1", area=ImagemapArea(x=347, y=0, width=346, height=520)
            ),
        ]
    elif n == 0:
        url = "https://AutomaticPurchaseProgram.sai11121209.repl.co/static/imagemap_number_of_people_0"
        action = [
            MessageImagemapAction(
                text=f"{type}: 0", area=ImagemapArea(x=0, y=0, width=346, height=520)
            ),
        ]
    print(url)
    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text=f"{type}の人数を選択してください。"),
            ImagemapSendMessage(
                base_url=url,
                alt_text=f"{type}の人数を選択してください。",
                base_size=BaseSize(height=1040, width=1040),
                actions=action,
            ),
        ],
    )


# ポート番号の設定
if __name__ == "__main__":
    server = Thread(target=run)
    server.start()

    messages = TextSendMessage(text=f"再販監視が開始されました")
    # line_bot_api.broadcast(messages=messages)
    job()
    ObservationTime = ObservationTime
    # {ObservationTime}分ごとに実行
    schedule.every(ObservationTime).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
