from flask import Flask, request, abort
from threading import Thread

app = Flask("")


@app.route("/")
def main():
    return "Bot is aLive!"


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    server = Thread(target=run)
    server.start()


# ポート番号の設定
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
