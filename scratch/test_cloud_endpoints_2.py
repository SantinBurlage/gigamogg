import urllib.request
import urllib.parse
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Test Pollinations GET with Russian prompt
prompt = "Напиши структуру сайта кофейни на HTML и CSS"
encoded = urllib.parse.quote(prompt)
url = f"https://text.pollinations.ai/{encoded}?model=openai"

print("Testing Pollinations GET...")
try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=15) as r:
        content = r.read().decode("utf-8")
        print("Pollinations GET Response Length:", len(content))
        print("Snippet:", content[:300])
except Exception as e:
    print("Pollinations GET error:", e)

# Test Pollinations POST /openai format
print("\nTesting Pollinations POST...")
try:
    post_url = "https://text.pollinations.ai/"
    payload = json.dumps({
        "messages": [
            {"role": "system", "content": "You are GIGAMOGG, an expert AI web architect."},
            {"role": "user", "content": "Создай сайт для кофейни с красивым дизайном."}
        ],
        "model": "openai",
        "seed": 42
    }).encode("utf-8")
    req = urllib.request.Request(post_url, data=payload, headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    })
    with urllib.request.urlopen(req, context=ctx, timeout=20) as r:
        content = r.read().decode("utf-8")
        print("Pollinations POST Response Length:", len(content))
        print("Snippet:", content[:300])
except Exception as e:
    print("Pollinations POST error:", e)

# Test DuckDuckGo correct flow:
print("\nTesting DuckDuckGo with correct vqd header...")
try:
    req = urllib.request.Request(
        "https://duckduckgo.com/duckchat/v1/status",
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-vqd-accept": "1"
        }
    )
    with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
        vqd = resp.headers.get("x-vqd-4")
        print("DDG vqd:", vqd)
        if vqd:
            body = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Напиши кратко сайт"}]
            }).encode()
            chat_req = urllib.request.Request(
                "https://duckduckgo.com/duckchat/v1/chat",
                data=body,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Content-Type": "application/json",
                    "x-vqd-4": vqd,
                    "Accept": "text/event-stream"
                }
            )
            with urllib.request.urlopen(chat_req, context=ctx, timeout=10) as c_resp:
                out = c_resp.read().decode("utf-8", errors="ignore")
                print("DDG Chat response len:", len(out))
                print("DDG snippet:", out[:200])
except Exception as e:
    print("DDG error:", e)

# Test Hugging Face free router (Qwen 2.5 Coder 32B or similar)
print("\nTesting Qwen / HuggingFace free endpoints...")
for model in ["qwen", "mistral", "searchgpt"]:
    try:
        url = f"https://text.pollinations.ai/{encoded}?model={model}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            print(f"Pollinations {model} worked! Len:", len(r.read()))
    except Exception as e:
        print(f"Pollinations {model} error:", e)
