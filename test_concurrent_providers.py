import g4f
import concurrent.futures

candidates = [
    "Airforce",
    "DeepInfra",
    "Qwen",
    "OpenRouterFree",
    "Cloudflare",
    "LMArena",
    "TeachAnything",
    "You",
    "PhindAi",
    "OperaAria"
]

def try_prov(name):
    p = getattr(g4f.Provider, name)
    resp = g4f.ChatCompletion.create(
        model="gpt-4o-mini",
        provider=p,
        messages=[{"role": "user", "content": "Say hello in 3 words"}],
    )
    return str(resp)

print("Starting concurrent tests with flush...", flush=True)

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    future_to_name = {
        executor.submit(try_prov, name): name 
        for name in candidates if hasattr(g4f.Provider, name)
    }
    for future in concurrent.futures.as_completed(future_to_name, timeout=15):
        name = future_to_name[future]
        try:
            res = future.result()
            print(f"[FOUND WORKING] {name} => {res[:150]}", flush=True)
            break
        except Exception as e:
            print(f"[FAIL] {name}: {type(e).__name__}", flush=True)
