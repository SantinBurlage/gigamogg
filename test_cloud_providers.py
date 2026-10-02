import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Test Puter API
print("Testing Puter AI...")
try:
    url = "https://api.puter.com/drivers/call"
    payload = json.dumps({
        "interface": "puter-chat-completion",
        "driver": "openai",
        "method": "chat",
        "args": {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Привет, ответь одним словом"}]
        }
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    })
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        print("Puter response:", r.read().decode())
except Exception as e:
    print("Puter error:", e)

# Test free reverse proxies or Hugging Face free models:
# e.g., Hugging Face router: https://router.huggingface.co/hf-inference/models/...
# Or free Cloudflare AI workers / OpenRouter free models:
print("\nTesting OpenRouter free models...")
try:
    url = "https://openrouter.ai/api/v1/chat/completions"
    payload = json.dumps({
        "model": "meta-llama/llama-3.2-3b-instruct:free",
        "messages": [{"role": "user", "content": "Привет"}]
    }).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    })
    with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
        print("OpenRouter response:", r.read().decode())
except Exception as e:
    print("OpenRouter error:", e)

# Test DuckDuckGo mobile or alternative headers
print("\nTesting DuckDuckGo alternative...")
try:
    req = urllib.request.Request(
        "https://duckduckgo.com/duckchat/v1/status",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "x-vqd-accept": "1",
            "Referer": "https://duckduckgo.com/",
            "Origin": "https://duckduckgo.com"
        }
    )
    with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
        print("DDG headers:", resp.headers.items())
        vqd = resp.headers.get("x-vqd-4")
        print("DDG vqd:", vqd)
except Exception as e:
    print("DDG alt error:", e)
