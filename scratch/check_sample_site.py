import urllib.request
import json
import sys
sys.stdout.reconfigure(encoding="utf-8")

payload = json.dumps({
    "text": "Создай сайт для кофейни",
    "temperature": 0.7
}).encode("utf-8")

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/chat",
    data=payload,
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req, timeout=40) as res:
    data = json.loads(res.read().decode("utf-8"))
    answer = data.get("answer", "")
    preview = data.get("html_preview") or ""
    print("Answer length:", len(answer))
    print("Preview length:", len(preview))
    print("Answer snippet:\n", answer[:400])
    if preview:
        with open("scratch/sample_generated_site.html", "w", encoding="utf-8") as f:
            f.write(preview)
        print("\nSaved generated site to scratch/sample_generated_site.html!")
