import sys, g4f
sys.stdout.reconfigure(encoding='utf-8')

system_prompt = (
    "Ты — GIGAMOGG, элитный искусственный интеллект, созданный для профессиональных разработчиков и архитекторов. "
    "Твое имя строго GIGAMOGG (без приставок Apex). "
    "Ты отвечаешь умно, глубоко, профессионально, современно, без смайликов и эмодзи. "
    "Когда тебя просят написать сайт или код, ты создаешь ПОЛНЫЙ, рабочий, красивейший, современный продакшн код (HTML5, стили CSS, логику JS), без заглушек и без лени."
)

user_prompt = "Создай сайт для кофейни. Сделай его стильным, с темной темой, меню напитков и контактами."

print("Testing GIGAMOGG cloud generation with CohereForAI_C4AI_Command...", flush=True)

try:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    resp = g4f.ChatCompletion.create(
        model=g4f.models.default,
        provider=g4f.Provider.CohereForAI_C4AI_Command,
        messages=messages,
        timeout=30
    )
    print("SUCCESS! Generated length:", len(resp))
    print("First 500 chars:\n", resp[:500])
    print("\nLast 300 chars:\n", resp[-300:])
except Exception as e:
    print("Error:", e)
