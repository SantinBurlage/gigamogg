import g4f

prompt = "Создай современный адаптивный сайт для элитной кофейни с красивыми стилями, темной темой, меню и анимацией."

print("Testing GLM...")
try:
    resp = g4f.ChatCompletion.create(
        model=g4f.models.default,
        provider=g4f.Provider.GLM,
        messages=[{"role": "user", "content": prompt}],
        timeout=30
    )
    print("GLM SUCCESS!")
    print("Length:", len(resp))
    print("Snippet:\n", resp[:400])
except Exception as e:
    print("GLM error:", e)

print("\nTesting CohereForAI_C4AI_Command...")
try:
    resp2 = g4f.ChatCompletion.create(
        model=g4f.models.default,
        provider=g4f.Provider.CohereForAI_C4AI_Command,
        messages=[{"role": "user", "content": prompt}],
        timeout=30
    )
    print("Cohere SUCCESS!")
    print("Length:", len(resp2))
    print("Snippet:\n", resp2[:400])
except Exception as e:
    print("Cohere error:", e)
