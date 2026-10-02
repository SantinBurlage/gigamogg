import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_blackbox():
    print("Testing Blackbox AI...")
    try:
        url = "https://www.blackbox.ai/api/chat"
        payload = json.dumps({
            "messages": [{"id": "1", "content": "Привет! Ответь одним словом.", "role": "user"}],
            "id": "chat-test-1",
            "previewToken": None,
            "userId": None,
            "codeModelMode": True,
            "agentMode": {},
            "trendingAgentMode": {},
            "isMicMode": False,
            "maxTokens": 1024
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            res = r.read().decode("utf-8")
            print("Blackbox AI Response:", res[:200])
            return True
    except Exception as e:
        print("Blackbox error:", e)
    return False

def test_nexra():
    print("Testing Nexra...")
    try:
        url = "https://nexra.aryahcr.cc/api/chat/gpt"
        payload = json.dumps({
            "messages": [{"role": "user", "content": "Привет"}],
            "prompt": "Привет",
            "model": "chatgpt"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            res = r.read().decode("utf-8")
            print("Nexra response:", res[:200])
            return True
    except Exception as e:
        print("Nexra error:", e)
    return False

def test_pollinations_gen():
    print("Testing Pollinations with simple path...")
    try:
        # Check if text.pollinations.ai works with no model param or with feed
        url = "https://text.pollinations.ai/Say%20GIGAMOGG%20Ready"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.68.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=10) as r:
            print("Pollinations simple:", r.read().decode())
            return True
    except Exception as e:
        print("Pollinations simple error:", e)
    return False

test_blackbox()
test_nexra()
test_pollinations_gen()
