import socket
import json
import sounddevice as sd
from gtts import gTTS
import soundfile as sf
import requests
import os

# URL для отправки запроса
url = "https://leingpt.ru/backend-api/v2/conversation"

# Файл для сохранения истории
history_file = "conversation_history.txt"

# Файл для сохранения токена
token_file = "api_token.txt"

def save_to_history(data):
    with open(history_file, "a", encoding="utf-8") as file:
        file.write(data + "\n")

def get_api_token():
    if os.path.exists(token_file):
        with open(token_file, "r", encoding="utf-8") as file:
            return file.read().strip()
    else:
        token = input("Пожалуйста, введите токен: ")
        with open(token_file, "w", encoding="utf-8") as file:
            file.write(token)
        return token

api_token = get_api_token()

def send_request(user_message, token):
    # Полезная нагрузка
    payload = {
        "conversation_id": token,
        "action": "_ask",
        "model": "gpt4o", #gpt-3.5-turbo
        "jailbreak": "Обычный",
        "tonegpt": "Friendly",
        "streamgen": False,
        "web_search": True,
        "rolej": "default",
        "meta": {
            "id": "7389965954683347117",
            "content": {
                "conversation": [
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                "content_type": "text",
                "parts": [
                    {
                        "content": user_message,
                        "role": "user"
                    }
                ]
            }
        }
    }

    # Заголовки запроса
    headers = {
        "Accept": "text/event-stream",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru,en;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Cookie": "_ym_uid=1720608655934219259; _ym_d=1720608655; _ym_isad=1; _ym_visorc=w",
        "Host": "leingpt.ru",
        "Origin": "https://leingpt.ru",
        "Referer": "https://leingpt.ru/chat/" + token,
        "Sec-Ch-Ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"YaBrowser\";v=\"24.4\", \"Yowser\";v=\"2.5\"",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "\"macOS\"",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 YaBrowser/24.4.0.0 Safari/537.36"
    }

    # Отправка POST-запроса
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    return response

# Создаем сокет TCP
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Связываем сокет с адресом и портом
s.bind(("127.0.0.1", 12345))

# Слушаем сокет
s.listen()

print("Сервер запущен и ожидает подключения...")

# Принимаем соединение
conn, addr = s.accept()
print(f"Подключен: {addr}")

# Получаем сообщение
data = b""
while True:
    packet = conn.recv(1024)
    if not packet or b"\n" in packet:
        data += packet
        break
    data += packet

request = data.decode("utf-8").strip()

print(request)

# Сохранение сообщения пользователя в историю
save_to_history(f"Пользователь: {request}")

# Функция для обработки и отправки запроса
def process_request(request, token):
    # Воспроизведение "generating.mp3"
    generating_data, generating_fs = sf.read("generating.mp3")
    sd.play(generating_data, generating_fs)
    
    response = send_request(request, token)
    
    # Остановка воспроизведения "generating.mp3"
    sd.stop()
    
    if response.status_code == 200:
        try:
            json_response = response.json()
            assistant_message = json_response.get("content", "Нет ответа")
        except json.JSONDecodeError:
            assistant_message = response.text
    else:
        assistant_message = f"Ошибка: {response.status_code}\n{response.text}"
    return assistant_message

# Отправка запроса и получение ответа
assistant_message = process_request(request, api_token)

if "Ошибка, повторите пожалуйста отправку сообщения" in assistant_message:
    print("Ошибка, повторите пожалуйста отправку сообщения")
    update_token = input("Хотите обновить токен? (да/нет): ").strip().lower()
    if update_token == "да":
        api_token = input("Пожалуйста, введите новый токен: ")
        with open(token_file, "w", encoding="utf-8") as file:
            file.write(api_token)
        assistant_message = process_request(request, api_token)

# выводим сообщение на экран
print(assistant_message)

# Преобразуем текст ответа в речь
tts = gTTS(assistant_message, lang='ru')

# Сохраняем речь в аудиофайл
tts.save("response.mp3")

# Загружаем аудиофайл
data, fs = sf.read("response.mp3")

# Воспроизводим аудиофайл
sd.play(data, fs)
sd.wait()

# Отправка ответа клиенту
conn.sendall(assistant_message.encode("utf-8"))

# Закрываем соединение
conn.close()
print("Соединение закрыто.")

# Закрываем сервер
s.close()
print("Сервер закрыт.")
