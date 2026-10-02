import g4f

for p in g4f.Provider.__providers__:
    if getattr(p, 'working', False) and not getattr(p, 'needs_auth', False):
        try:
            print(f"Testing {p.__name__}...", flush=True)
            resp = g4f.ChatCompletion.create(
                model=g4f.models.default,
                provider=p,
                messages=[{"role": "user", "content": "Привет, ответь одним словом: 'РАБОТАЕТ'"}],
                timeout=6
            )
            if resp and len(str(resp)) > 0:
                print(f"--> {p.__name__} SUCCESS: {str(resp)[:100]}", flush=True)
                break
        except Exception as e:
            # print(f"{p.__name__} failed: {e}", flush=True)
            pass
