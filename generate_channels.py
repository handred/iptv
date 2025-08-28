# generate_channels.py
import re
import json
import urllib.parse
# Импортируем из внешнего модуля
from libs import slugify

# --- НАСТРОЙКИ ---
INPUT_M3U = "playlist.m3u"           # Ваш исходный M3U
OUTPUT_JSON = "channels.json"        # Выходной JSON для виджета
SERVER_IP = "192.168.0.150"          # Ваш сервер
SERVER_PORT = 8083
BASE_URL = f"http://{SERVER_IP}:{SERVER_PORT}"
# ---------------


def parse_m3u(file_path):
    channels = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    channel = {}
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            # Извлекаем атрибуты
            tvg_id = re.search(r'tvg-id=["\']?([^"\'\s,]+)', line)
            tvg_name = re.search(r'tvg-name=["\']?([^"\'\s,]+)', line)
            tvg_logo = re.search(r'tvg-logo=["\']?([^"\'\s,]+)', line)
            group_title = re.search(r'group-title=["\']?([^"\'\s,]+)', line)
            name_match = re.search(r',[^\s].*$', line)
            
            channel = {
                "tvg_id": tvg_id.group(1) if tvg_id else "",
                "tvg_name": urllib.parse.unquote(tvg_name.group(1)) if tvg_name else "Без названия",
                "logo": tvg_logo.group(1) if tvg_logo else "",
                "group": group_title.group(1) if group_title else "Разные",
                "name": name_match.group(0)[1:].strip() if name_match else "Без названия"
            }
        elif line.startswith("http://") or line.startswith("https://"):
            if channel:
                safe_name = slugify(channel["name"])
                channel["url"] = f"{BASE_URL}/{safe_name}"
                channels.append({
                    "name": channel["name"],
                    "url": channel["url"],
                    "logo": channel["logo"],
                    "group": channel["group"]
                })
                channel = {}
    return channels

# Запуск
if __name__ == "__main__":
    try:
        channels = parse_m3u(INPUT_M3U)
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(channels, f, ensure_ascii=False, indent=2)
        print(f"✅ Успешно: {len(channels)} каналов сохранено в {OUTPUT_JSON}")
        print(f"📌 Теперь обновите {OUTPUT_JSON} в вашем .wgt-виджете")
    except Exception as e:
        print(f"❌ Ошибка: {e}")