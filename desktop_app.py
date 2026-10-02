"""GIGAMOGG Studio — Нативное десктопное приложение.

Запускает локальный сервер нейросети и открывает высокопроизводительное
десктопное окно на движке Microsoft Edge WebView2 с поддержкой аппаратного
ускорения GPU, без рамок браузера и с ультра-быстрым откликом.
"""
import os
import sys
import time
import threading
import urllib.request

# Корректная локаль для Windows
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.chdir(BASE)


def is_server_alive(port: int = 8000) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/tiers", timeout=0.6) as r:
            return r.status == 200
    except Exception:
        return False


def start_server_in_background(port: int = 8000):
    if is_server_alive(port):
        return
    from giga.server import serve
    t = threading.Thread(target=serve, kwargs=dict(port=port, host="0.0.0.0", open_browser=False), daemon=True)
    t.start()
    for _ in range(40):
        if is_server_alive(port):
            break
        time.sleep(0.1)


def main():
    port = int(os.environ.get("GIGAMOGG_PORT", 8000))
    print("[GIGAMOGG Desktop] Инициализация нативного десктопного движка...")
    start_server_in_background(port)

    import webview
    window = webview.create_window(
        title="GIGAMOGG Studio",
        url=f"http://127.0.0.1:{port}",
        width=1280,
        height=840,
        min_size=(960, 600),
        background_color="#090a0d",
        text_select=True,
    )
    webview.start()


if __name__ == "__main__":
    main()
