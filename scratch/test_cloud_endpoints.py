import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# Test 1: DuckDuckGo AI chat (free, no key required)
def test_ddg():
    print("Testing DuckDuckGo...")
    try:
        # DDG requires fetching status first
        req = urllib.request.Request(
            "https://duckduckgo.com/duckchat/v1/status",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "x-vqd-accept": "1"}
        )
        with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
            vqd = resp.headers.get("x-vqd-4")
            print("DDG Status OK, vqd:", vqd[:10] if vqd else "none")
            
        if vqd:
            body = json.dumps({
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Write a 1-line hello world in Python"}]
            }).encode()
            chat_req = urllib.request.Request(
                "https://duckduckgo.com/duckchat/v1/chat",
                data=body,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Content-Type": "application/json",
                    "x-vqd-4": vqd,
                    "Accept": "text/event-stream"
                }
            )
            with urllib.request.urlopen(chat_req, context=ctx, timeout=10) as c_resp:
                out = c_resp.read().decode(errors="ignore")
                print("DDG Chat response snippet:", out[:200])
                return True
    except Exception as e:
        print("DDG failed:", e)
    return False

# Test 2: Pollinations text endpoints check with different models or prompt formats
def test_pollinations():
    print("Testing Pollinations...")
    for model in ["openai", "searchgpt", "mistral", "llama"]:
        try:
            url = f"https://text.pollinations.ai/hello?model={model}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
                print(f"Pollinations {model} OK:", r.read().decode()[:100])
                return True
        except Exception as e:
            print(f"Pollinations {model} error:", e)
    return False

# Test 3: Free cloud proxy / OpenRouter / Hugging Face Serverless / free APIs
def test_free_apis():
    print("Testing free community endpoints...")
    # api.airforce
    try:
        url = "https://api.airforce/v1/chat/completions"
        data = json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "Say 'GIGAMOGG ONLINE'"}]
        }).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
            res = json.loads(r.read().decode())
            print("Airforce OK:", res["choices"][0]["message"]["content"])
            return "airforce"
    except Exception as e:
        print("Airforce error:", e)
        
    return None

test_ddg()
test_pollinations()
test_free_apis()
