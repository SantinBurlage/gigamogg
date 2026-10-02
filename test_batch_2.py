import g4f
import concurrent.futures

candidates = [
    "DeepInfra",
    "Cloudflare",
    "LMArena",
    "Pi",
    "GLM",
    "HailuoAI",
    "CohereForAI_C4AI_Command",
    "KiloCode",
    "LLM7",
    "OpenCode",
    "ChatGPT",
    "Perplexity"
]

def try_prov(name):
    p = getattr(g4f.Provider, name)
    resp = g4f.ChatCompletion.create(
        model=g4f.models.default,
        provider=p,
        messages=[{"role": "user", "content": "Hello"}],
    )
    return str(resp)

print("Starting next batch...", flush=True)

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
    future_to_name = {
        executor.submit(try_prov, name): name 
        for name in candidates if hasattr(g4f.Provider, name)
    }
    for future in concurrent.futures.as_completed(future_to_name, timeout=12):
        name = future_to_name[future]
        try:
            res = future.result()
            print(f"[FOUND WORKING] {name} => {res[:150]}", flush=True)
        except Exception as e:
            print(f"[FAIL] {name}: {type(e).__name__}", flush=True)
