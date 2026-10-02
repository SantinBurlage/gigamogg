import urllib.request
import urllib.parse
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def test_pollinations_prompt(prompt, system=None):
    full_prompt = prompt
    if system:
        full_prompt = f"{system}\n\nUser: {prompt}\nAssistant:"
    
    encoded = urllib.parse.quote(full_prompt)
    url = f"https://text.pollinations.ai/{encoded}"
    
    print(f"Requesting prompt length: {len(full_prompt)}")
    req = urllib.request.Request(url, headers={
        "User-Agent": "curl/7.68.0",
        "Accept": "*/*"
    })
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            res = r.read().decode("utf-8")
            print("Status:", r.status)
            print("Response Length:", len(res))
            print("Snippet:\n", res[:400])
            return res
    except Exception as e:
        print("Error:", e)
        return None

test_pollinations_prompt("Напиши красивый сайт для кофейни на HTML и CSS с современным дизайном")
