import urllib.request
import json

payload = json.dumps({
    "text": "Создай сайт для кофейни с темной темой, меню и контактами",
    "temperature": 0.7
}).encode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/chat",
    data=payload,
    headers={"Content-Type": "application/json"}
)

print("Sending chat request to http://127.0.0.1:8000/api/chat ...")
with urllib.request.urlopen(req, timeout=40) as res:
    data = json.loads(res.read().decode("utf-8"))
    print("Provider used:", data.get("provider"))
    print("Device:", data.get("device"))
    print("HTML Preview length:", len(data.get("html_preview") or ""))
    print("Has <!DOCTYPE html>:", "<!DOCTYPE html>" in (data.get("html_preview") or "").upper())
    print("Answer length:", len(data.get("answer", "")))
    print("\nAnswer preview (first 300 chars):\n", data.get("answer", "")[:300])
