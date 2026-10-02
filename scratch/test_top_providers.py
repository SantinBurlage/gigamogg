import g4f

candidates = [
    "OpenRouterFree",
    "DeepInfra",
    "Airforce",
    "Cloudflare",
    "ChatGPT",
    "Qwen",
    "LMArena",
    "PhindAi",
    "TeachAnything",
    "You",
    "OperaAria",
    "GeminiPro",
    "GoogleAiMode",
]

for name in candidates:
    if hasattr(g4f.Provider, name):
        p = getattr(g4f.Provider, name)
        try:
            print(f"Trying {name}...")
            resp = g4f.ChatCompletion.create(
                model=g4f.models.default,
                provider=p,
                messages=[{"role": "user", "content": "Ответь кратко: 'Привет от ' и твое название"}],
                timeout=5
            )
            if resp:
                print(f"SUCCESS {name} => {resp}")
        except Exception as e:
            print(f"Failed {name}: {type(e).__name__} - {e}")
