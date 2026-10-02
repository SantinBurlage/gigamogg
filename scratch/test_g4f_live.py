import g4f
from g4f.client import Client

print("Testing g4f client with free providers...")
client = Client()

models_to_test = ["gpt-4o-mini", "gpt-4o", "claude-3.5-sonnet", "deepseek-chat", "llama-3.3-70b", "qwen-2.5-coder-32b"]

for model in models_to_test:
    print(f"\n--- Testing model: {model} ---")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Скажи коротко: кто ты и какая сегодня дата?"}]
        )
        content = response.choices[0].message.content
        print(f"SUCCESS with {model}!")
        print("Response snippet:", content[:200])
        break
    except Exception as e:
        print(f"Failed {model}: {e}")
