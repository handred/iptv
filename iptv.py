# iptv.py — IPTV-сервер с поддержкой звука (AAC) для старых Smart TV
import re
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
# Импортируем из внешнего модуля
from libs import slugify

# Настройки
PLAYLIST_FILE = "playlist.m3u"
HOST = "0.0.0.0"
PORT = 8083

def parse_m3u(file_path):
    """Парсит M3U и возвращает словарь: {safe_name.ts: url}"""
    channels = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    name = None
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            # Извлекаем имя канала после запятой
            match = re.search(r',([^,]+)$', line)
            if match:
                name = match.group(1).strip()
        elif line.startswith("http://") or line.startswith("https://"):
            if name:
                # Создаём безопасное имя файла
                safe_name = slugify(name)  # ← используем из libs.py
                channels[safe_name] = line
                name = None
    return channels

# Загружаем каналы
channels = parse_m3u(PLAYLIST_FILE)
print(f"\n[+] Загружено каналов: {len(channels)}")
for cname in channels:
    print(f"    → {cname}")
print(f"\n[▶] Сервер запускается на http://<ваш_IP>:{PORT}/")
print("    Пример: http://192.168.0.150:8083/Perviy_Kanal.ts\n")

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
                "-c:v", "copy",           # Копируем видео (без перекодирования)
                "-c:a", "aac",            # Перекодируем аудио в AAC
                "-b:a", "128k",           # Битрейт аудио
                "-ar", "48000",           # Частота дискретизации
                "-f", "mpegts",           # Формат MPEG-TS
                "-flush_packets", "1",
                "-safe", "0",
                "pipe:1"                  # Вывод в stdout
            ]

            try:
                ffmpeg = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,  # Можно изменить на.PIPE для отладки
                    bufsize=65536
                )

                def cleanup():
                    if ffmpeg.poll() is None:
                        ffmpeg.terminate()
                        try:
                            ffmpeg.wait(timeout=3)
                        except:
                            ffmpeg.kill()

                self.connection.set_close_notify_callback(cleanup)

                while True:
                    chunk = ffmpeg.stdout.read(8192)
                    if not chunk:
                        break
                    try:
                        self.wfile.write(chunk)
                        self.wfile.flush()
                    except (ConnectionResetError, BrokenPipeError):
                        break

            except Exception as e:
                print(f"[❌] Ошибка при воспроизведении {path}: {e}")
            finally:
                try:
                    if 'ffmpeg' in locals() and ffmpeg.poll() is None:
                        ffmpeg.terminate()
                except:
                    pass

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Channel not found")

if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), IPTVHandler)
    print(f"[✅] Сервер запущен на порту {PORT} (Ctrl+C для остановки)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n[🛑] Сервер остановлен пользователем.")