import os
import sys
import json
import urllib.request
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

TEAMS_WEBHOOK_URL = os.environ.get("TEAMS_WEBHOOK_URL")

# モントリオール Bridge St. 店 (#00515) の予約トップページ
LOCATION_URL = "https://waitwhile.com/locations/costcotire-00515"

def send_teams_notification(message: str, title: str = "Costco タイヤ予約の空きを発見しました！"):
    """Teams Webhook 経由でアダプティブカード通知を送信"""
    if not TEAMS_WEBHOOK_URL:
        print("[ERROR] TEAMS_WEBHOOK_URL が設定されていません。")
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
                            "title": "今すぐ予約画面を開く",
                            "url": LOCATION_URL
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
            print(f"[SUCCESS] Teams通知送信完了 (Status: {response.status})")
    except Exception as e:
        print(f"[ERROR] Teams通知送信失敗: {e}")

def check_costco_appointments():
    print("=== Costco Tire 予約巡回チェック開始 ===")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 言語を英語に固定し、画面解像度を設定
        context = browser.new_context(
            locale="en-US",
            viewport={"width": 1280, "height": 800},
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # 1. 店舗の予約トップページへアクセス
            print(f"[1/3] 店舗トップページへアクセス中: {LOCATION_URL}")
            page.goto(LOCATION_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)

            # 2. 作業メニュー「Seasonal Exchange 4 Wheels/8 Tires」を自動クリック
            print("[2/3] 作業メニュー（Seasonal Exchange 4 Wheels/8 Tires）を選択中...")
            service_button = page.locator("text=/Seasonal Exchange|Changement de pneus/i").first
            
            if service_button.is_visible(timeout=10000):
                service_button.click()
                print("   -> 作業メニューをクリックしました。日時選択画面への遷移を待機中...")
                page.wait_for_timeout(4000)
            else:
                print("   [WARNING] 指定の作業メニューボタンが画面上に見つかりませんでした。")

            # 3. 日時選択画面での空き枠判定
            print("[3/3] カレンダー・空き枠の解析中...")
            content = page.content().lower()

            # サービス未選択エラーが発生していないか確認
            if "must have at least 1 service assigned" in content:
                print("[ERROR] サービスの自動選択に失敗しました。次回再試行します。")
                return

            # 「空きなし」を示すキーワード（英語・フランス語両対応）
            no_slots_keywords = [
                "no appointments available",
                "no available dates",
                "no times available",
                "fully booked",
                "aucun créneau disponible",
                "aucune date disponible",
                "complet"
            ]

            is_fully_booked = any(kw in content for kw in no_slots_keywords)

            if not is_fully_booked:
                print("★ 空き枠（予約可能日時）を検知しました！")
                send_teams_notification(
                    "モントリオール Bridge St. 店（Seasonal Exchange 4 Wheels/8 Tires）に予約可能な空き枠が検知されました！至急確認してください。"
                )
            else:
                print("現在、指定条件（Bridge St. / Seasonal Exchange）での空き枠はありません。")

        except PlaywrightTimeoutError:
            print("[WARNING] ページの読み込みタイムアウトが発生しました。次回実行時に再試行します。")
        except Exception as e:
            print(f"[ERROR] 実行中にエラーが発生しました: {e}")
        finally:
            browser.close()
            print("=== チェック終了 ===")

if __name__ == "__main__":
    check_costco_appointments()
if __name__ == "__main__":
    send_teams_notification("これはテスト通知です。Teams連携は正常に動作しています。", title="テスト通信成功")
    # check_costco_appointments()
