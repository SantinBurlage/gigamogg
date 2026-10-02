import sys, g4f
sys.stdout.reconfigure(encoding='utf-8')

providers_to_test = [
    "CohereForAI_C4AI_Command",
    "GLM",
    "BlackForestLabs_Flux1Dev",
    "Claude",
    "ChatGPT",
    "DeepInfra",
    "Cloudflare",
    "LMArena"
]

for name in providers_to_test:
    if hasattr(g4f.Provider, name):
        p = getattr(g4f.Provider, name)
        try:
            print(f"Testing {name}...", flush=True)
            res = g4f.ChatCompletion.create(
                model=g4f.models.default,
                provider=p,
                messages=[{"role": "user", "content": "Привет! Ответь одним словом."}],
                timeout=6
            )
            print(f"--> {name} OK: {res}", flush=True)
        except Exception as e:
            print(f"--> {name} FAIL: {type(e).__name__} - {e}", flush=True)
