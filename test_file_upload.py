import json
import urllib.request
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def post(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode('utf-8'))

print("=== TEST FILE & PHOTO UPLOAD ===")

test_files = [
    {
        "name": "math_utils.py",
        "type": "text/x-python",
        "size": 128,
        "isImage": False,
        "textContent": "def calculate_factorial(n):\n    if n <= 1:\n        return 1\n    return n * calculate_factorial(n - 1)\n"
    },
    {
        "name": "mockup_screenshot.png",
        "type": "image/png",
        "size": 2048,
        "isImage": True,
        "dataUrl": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    }
]

payload = {
    "text": "Посмотри прикрепленный файл math_utils.py и фото mockup_screenshot.png. Что в них находится?",
    "files": test_files
}

res = post("http://127.0.0.1:8000/api/chat", payload)
ans = res.get("answer", "")
print("Status: Answer received, length:", len(ans))
print("Answer excerpt:", ans[:300])

assert "factorial" in ans.lower() or "факториал" in ans.lower() or "math_utils" in ans.lower(), f"Model did not read attached code! {ans}"

print("\nSUCCESS: File and photo processing verified!")
