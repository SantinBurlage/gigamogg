with open('web/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("'✓ Скопировано!'", "'Скопировано'")
text = text.replace("'✓'", "'OK'")
text = text.replace("'✓ OK'", "'OK'")
text = text.replace("'⚡ Трансформер GIGA 1B: 24 слоя, 16 Attention Heads вычисляются на GPU CUDA...'", "'Трансформер Apex: 24 слоя, 16 Attention Heads вычисляются на GPU CUDA...'")
text = text.replace("'🔍 Когнитивное ядро: синтез кода, проверка логики и сборка фактов...'", "'Когнитивное ядро: синтез кода, проверка логики и сборка фактов...'")
text = text.replace("'🛡️ Критик-Ко-пайлот: аудит синтаксиса, скобок кода и проверка на живой язык...'", "'Критик-Ко-пайлот: аудит синтаксиса, скобок кода и проверка на живой язык...'")
text = text.replace("⚡ Выделение тензорных ядер NVIDIA CUDA и активация прямого прохода...", "Выделение тензорных ядер NVIDIA CUDA и активация прямого прохода...")

# Remove remaining 1B and param count mentions
text = text.replace("ИНФЕРЕНС 1 000 000 000 ПАРАМЕТРОВ", "ИНФЕРЕНС APEX")
text = text.replace("GIGA 1B (24 СЛОЯ, 16 HEADS RoPE НА GPU)", "APEX (24 СЛОЯ, 16 HEADS RoPE НА GPU)")
text = text.replace("2. Трансформер 1B", "2. Трансформер Apex")
text = text.replace("Трансформер 1B на GPU", "Трансформер Apex на GPU")
text = text.replace("Трансформер 1B: прямой проход", "Трансформер Apex: прямой проход")
text = text.replace("Активация слоев GIGAMOGG 1B", "Активация слоев GIGAMOGG Apex")
text = text.replace("Все слои 1B вычислены успешно", "Все слои Apex вычислены успешно")
text = text.replace("<span>GIGAMOGG 1B</span>", "<span>GIGAMOGG Apex</span>")

with open('web/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Final cleanup finished!")
