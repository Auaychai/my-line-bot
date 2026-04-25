import gspread
from oauth2client.service_account import ServiceAccountCredentials

import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
# ส่วนนี้คือส่วนที่หายไป ทำให้เกิด Error ครับ
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv

# โหลดค่าจากไฟล์ .env
load_dotenv()

app = Flask(__name__)

# ดึงรหัสจาก environment variables
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

# ... (โค้ดส่วนที่เหลือของคุณตามปกติ)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# เพิ่มส่วนนี้ไว้ใน app.py
from linebot.models import MessageEvent, TextMessage, TextSendMessage

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    print(f"DEBUG: บอทได้รับข้อความว่า '{msg}'") # <-- ถ้าโค้ดนี้ทำงาน จะต้องเห็นบรรทัดนี้ใน CMD

    if "จองห้อง" in msg:
        print("DEBUG: พบคำว่า จองห้อง ในข้อความ!")
        try:
            save_booking("คุณอวยชัย", "ห้อง A", "25/04/2026", "10.00 น.")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="จองห้องให้คุณเรียบร้อยแล้วครับ!")
            )
        except Exception as e:
            print(f"DEBUG: Error ตอนบันทึกคือ {e}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"Error: {e}")
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="บอทได้รับข้อความของคุณแล้ว: " + msg)
        )

# --- ตั้งค่า Google Sheets ---
def get_sheet_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # ถ้าอยู่บน Render จะอ่านจาก Environment Variable
    if 'GOOGLE_CREDENTIALS' in os.environ:
        creds_dict = json.loads(os.environ['GOOGLE_CREDENTIALS'])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        # ถ้าอยู่บนเครื่องจะอ่านจากไฟล์
        creds = ServiceAccountCredentials.from_json_keyfile_name('service-account.json', scope)
        
    client = gspread.authorize(creds)
    return client.open('MeetingRoomBooking').sheet1

# --- ฟังก์ชันบันทึกข้อมูล ---
def save_booking(name, room, date, time):
    sheet = get_sheet_client()
    # ตรวจสอบหัวตาราง: Timestamp, Name, Room, Date, Time
    row = ["", name, room, date, time] # ช่องแรกเว้นไว้สำหรับสูตร Timestamp
    sheet.append_row(row)

if __name__ == "__main__":
    app.run(port=5000)