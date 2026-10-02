import g4f

for name in dir(g4f.Provider):
    if name.startswith('_'): continue
    prov = getattr(g4f.Provider, name)
    if hasattr(prov, 'working') and prov.working and not getattr(prov, 'needs_auth', False):
        try:
            print(f"Testing {name}...")
            resp = g4f.ChatCompletion.create(
                model=g4f.models.default,
                provider=prov,
                messages=[{"role": "user", "content": "Привет! Назови столицу Франции."}],
                timeout=8
            )
            print(f"--> {name} SUCCESS: {resp[:100]}")
            break
        except Exception as e:
            # print(f"--> {name} error: {e}")
            pass
