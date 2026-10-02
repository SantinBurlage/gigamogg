import g4f

print("Listing some g4f working providers...")
providers = [
    g4f.Provider.Blackbox,
    g4f.Provider.DDG,
    g4f.Provider.FreeNetfly,
    g4f.Provider.HuggingChat,
    g4f.Provider.Pizzagpt,
    g4f.Provider.Airforce,
    g4f.Provider.Liaobots,
]

for p in providers:
    try:
        print(f"Testing provider: {p.__name__}")
        resp = g4f.ChatCompletion.create(
            model=g4f.models.default,
            provider=p,
            messages=[{"role": "user", "content": "Привет, скажи 1 слово"}],
            timeout=5
        )
        print(f"Provider {p.__name__} OK: {resp}")
        break
    except Exception as e:
        print(f"Provider {p.__name__} failed: {e}")
