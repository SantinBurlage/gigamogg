with open("web/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

print("Total lines:", len(lines))

# Find key anchor lines
for i, line in enumerate(lines):
    if 'meta-pill-apex' in line:
        print(f"meta-pill-apex at line {i+1}")
    if 'id="p-train"' in line:
        print(f"p-train at line {i+1}")
    if 'id="p-catalog"' in line:
        print(f"p-catalog at line {i+1}")
    if 'id="p-hw"' in line:
        print(f"p-hw at line {i+1}")
    if 'id="p-chat"' in line:
        print(f"p-chat at line {i+1}")
    if 'data-tab="train"' in line:
        print(f"data-tab train at line {i+1}")
