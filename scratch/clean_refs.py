with open('web/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('<span class="c-tag">GIGA 1B</span>', '<span class="c-tag">APEX</span>')
text = text.replace('model="giga1b"', 'model="apex"')
text = text.replace('"model": "giga1b"', '"model": "apex"')
text = text.replace('model: "giga1b"', 'model: "apex"')
text = text.replace('<span class="syn-tag">1B веса</span>', '<span class="syn-tag">Apex веса</span>')
text = text.replace("'Трансформер GIGA 1B (24 слоя, 16 Attention Heads на GPU CUDA)'", "'Трансформер Apex (24 слоя, 16 Attention Heads на GPU CUDA)'")
text = text.replace("'CUDA_ATTENTION_1B'", "'CUDA_ATTENTION_APEX'")
text = text.replace('CUDA_1B', 'CUDA_APEX')
text = text.replace('СЕЛЕКТОР МОДЕЛЕЙ (ПОДДЕРЖКА 1 000 000 000 ПАРАМЕТРОВ GIGA 1B)', 'СЕЛЕКТОР АРХИТЕКТУР GIGAMOGG')
text = text.replace('// Выбираем GIGA 1B (Флагман на 1.1 млрд параметров)', '// Выбираем флагманскую архитектуру GIGAMOGG Apex')

with open('web/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Cleaned model references!')
