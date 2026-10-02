with open('web/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'id="p-webstudio"' in l:
        print(f"Found at line {i+1}:")
        print(''.join(lines[i:i+70]))
        break
