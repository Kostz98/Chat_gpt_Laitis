import socket
import sys

def send_message(host="127.0.0.1", port=12345):
    message = " ".join(sys.argv[1:])

    # Создаем сокет TCP
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Подключаемся к серверу
    s.connect((host, port))

    # Отправляем сообщение
    s.sendall((message + "\n").encode('utf-8'))

    # Получаем ответ
    response = b""

    # Закрываем соединение
    s.close()

if __name__ == "__main__":
    send_message()
