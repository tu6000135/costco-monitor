import os
import sys
import json
import urllib.request
from playwright.sync_api import sync_playwright

TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK_URL")

def send_teams_notification(message: str, title: str = "Costco タイヤ予約の空きを発見しました！"):
    if not TEAMS_WEBHOOK_URL:
        print("ERROR: TEAMS_WEBHOOK_URL 環境変数が設定されていません。")
        return

    payload = {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "contentUrl": None,
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": title,
                            "weight": "Bolder",
                            "size": "Large",
                            "color": "Good"
                        },
                        {
                            "type": "TextBlock",
                            "text": message,
                            "wrap": True
                        },
                        {
                            "type": "FactSet",
                            "facts": [
                                {"title": "店舗:", "value": "Montreal Bridge St. (#00515)"},
                                {"title": "作業:", "value": "Seasonal Exchange 4 Wheels/8 Tires"},
                                {"title": "対象期間:", "value": "今後21日間"}
                            ]
                        }
                    ],
                    "actions": [
                        {
                            "type": "Action.OpenUrl",
                            "title": "予約サイトを開く",
                            "url": "https://costcotireappointments.ca/"
                        }
                    ]
                }
            }
        ]
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        TEAMS_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req) as response:
            print(f"Teams通知送信完了 (Status: {response.status})")
    except Exception as e:
        print(f"Teams通知送信失敗: {e}")

def check_costco_appointments():
    print("Costco Tire アポイントメントの巡回チェックを開始します...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            page.goto("https://costcotireappointments.ca/", wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)

            content = page.content()

            if "no appointments available" not in content.lower() and "no available dates" not in content.lower():
                print("空き枠を検知しました！")
                send_teams_notification(
                    "モントリオール Bridge St. 店にて Seasonal Exchange の予約可能枠が検知されました。至急確認してください。"
                )
            else:
                print("現在、指定条件での空き枠はありません。")

        except Exception as e:
            print(f"スクリプト実行中にエラーが発生しました: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    check_costco_appointments()
