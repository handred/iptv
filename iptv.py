# iptv.py
# Самописный IPTV-сервер для старых Smart TV
# Поддержка: H.264 + AAC, транслит кириллицы, ретрансляция через FFmpeg

import re
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from libs import slugify

# === НАСТРОЙКИ ===
PLAYLIST_FILE = "playlist.m3u"      # Путь к вашему M3U-файлу
HOST = "0.0.0.0"                    # Слушать на всех интерфейсах
PORT = 8083                         # Порт сервера (совпадает с вашим)
# ================


def parse_m3u(file_path):
    """Парсит M3U и возвращает словарь: {имя_файла.ts: URL_потока}"""
    channels = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"[❌] Не найден файл: {file_path}")
        return {}

    name = None
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            match = re.search(r',([^,]+)$', line)
            if match:
                name = match.group(1).strip()
        elif line.startswith("http://") or line.startswith("https://"):
            if name:
                safe_name = slugify(name)
                channels[safe_name] = line
                name = None
    return channels


# Загружаем каналы
channels = parse_m3u(PLAYLIST_FILE)

print(f"\n[+] Загружено каналов: {len(channels)}")
for cname in channels:
    print(f"    → {cname}")

print(f"\n[▶] Сервер запускается на порту {PORT}...")
print("    Пример ссылки: http://192.168.0.150:8083/perviy_kanal.ts")
print("    Нажмите Ctrl+C для остановки\n")


class IPTVHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.lstrip("/")
        if path in channels:
            self.send_response(200)
            self.send_header("Content-Type", "video/mpeg")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()

            stream_url = channels[path]
            print(f"[▶] Запуск канала: {path} → {stream_url}")

            # Команда FFmpeg: копируем видео, аудио → AAC
            cmd = [
                "ffmpeg",
                "-user_agent", "Mozilla/5.0 (SmartHub; Samsung B Series) AppleWebKit/537.43",
                "-i", stream_url,
                "-c:v", "copy",           # Копируем видео без перекодирования
                "-c:a", "aac",            # Перекодируем аудио в AAC (поддерживается TV)
                "-b:a", "128k",           # Битрейт аудио
                "-ar", "48000",           # Частота дискретизации
                "-f", "mpegts",           # Формат MPEG-TS
                "-flush_packets", "1",    # Быстрая отправка
                "pipe:1"                  # Вывод в stdout
            ]

            ffmpeg = None
            try:
                ffmpeg = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,  # Используйте stderr=PIPE для отладки
                    bufsize=65536
                )

                # Потоковая передача данных
                while True:
                    chunk = ffmpeg.stdout.read(8192)
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    except (ConnectionResetError, BrokenPipeError):
                        print(f"[⏹] Клиент отключился: {path}")
                        break

            except Exception as e:
                print(f"[❌] Ошибка при воспроизведении {path}: {e}")
            finally:
                # Корректное завершение FFmpeg
                if ffmpeg and ffmpeg.poll() is None:
                    try:
                        ffmpeg.terminate()
                        try:
                            ffmpeg.wait(timeout=3)
                        except subprocess.TimeoutExpired:
                            ffmpeg.kill()
                    except:
                        pass
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Channel not found")


if __name__ == "__main__":
    try:
        server = HTTPServer((HOST, PORT), IPTVHandler)
        print(f"[✅] Сервер запущен на http://{HOST}:{PORT}")
        print("[ℹ] Для остановки нажмите Ctrl+C\n")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[🛑] Сервер остановлен пользователем.")
    except Exception as e:
        print(f"[🔥] Ошибка сервера: {e}")