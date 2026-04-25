from linebot import LineBotApi, WebhookHandler

import os
from dotenv import load_dotenv

# โหลดไฟล์ .env
load_dotenv()

# --- เพิ่มส่วนนี้เพื่อเช็คค่า ---
token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
print(f"DEBUG: กำลังอ่าน TOKEN ได้ค่าคือ: {token}")

if not token:
    print("ERROR: หาค่า LINE_CHANNEL_ACCESS_TOKEN ในไฟล์ .env ไม่เจอ!")
# ----------------------------

# ส่วนที่เหลือของโค้ด...
line_bot_api = LineBotApi(token)

import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage

app = Flask(__name__)

# ตั้งค่า API
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# ตั้งค่า Google Sheets
def get_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("MeetingRoomBooking").sheet1

def save_booking(name, room, date, time):
    sheet = get_sheet()
    sheet.append_row(["", name, room, date, time])

def get_booking_status():
    sheet = get_sheet()
    data = sheet.get_all_records()
    if not data: return "ยังไม่มีรายการจองครับ"
    
    status_text = "📋 รายการจองล่าสุด:\n\n"
    for row in data[-4:]: # ดึง 4 แถวล่าสุด
        status_text += f"🏢 {row['Room']}\n📅 {row['Date']} | 🕒 {row['Time']}\n👤 {row['Name']}\n---\n"
    return status_text

def send_main_menu(event):
    flex_json = {
      "type": "bubble",
      "header": {"type": "box", "layout": "vertical", "contents": [{"type": "text", "text": "ระบบจองห้องประชุม", "weight": "bold", "color": "#ffffff"}], "backgroundColor": "#00B900"},
      "body": {"type": "box", "layout": "vertical", "contents": [
          {"type": "text", "text": "สายสีเหลือง:", "weight": "bold"},
          {"type": "button", "action": {"type": "message", "label": "Yellow - ห้อง 1", "text": "จองสายสีเหลือง ห้อง 1"}},
          {"type": "button", "action": {"type": "message", "label": "Yellow - ห้อง 2", "text": "จองสายสีเหลือง ห้อง 2"}},
          {"type": "text", "text": "สายสีชมพู:", "weight": "bold", "margin": "lg"},
          {"type": "button", "action": {"type": "message", "label": "Pink - ห้อง 1", "text": "จองสายสีชมพู ห้อง 1"}},
          {"type": "button", "action": {"type": "message", "label": "Pink - ห้อง 2", "text": "จองสายสีชมพู ห้อง 2"}},
          {"type": "separator", "margin": "lg"},
          {"type": "button", "style": "secondary", "action": {"type": "message", "label": "เช็คสถานะการจอง", "text": "เช็คสถานะ"}}
      ]}
    }
    line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="เมนูจอง", contents=flex_json))

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try: handler.handle(body, signature)
    except InvalidSignatureError: abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    if msg == "เมนู" or msg == "จองห้อง":
        send_main_menu(event)
    elif "จองสายสี" in msg:
        save_booking("คุณอวยชัย", msg.replace("จอง", ""), "25/04/2026", "10.00 น.")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"{msg.replace('จอง', '')} สำเร็จครับ!"))
    elif msg == "เช็คสถานะ":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=get_booking_status()))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="พิมพ์ 'เมนู' เพื่อเริ่มจองครับ"))

if __name__ == "__main__":
    app.run(port=5000)