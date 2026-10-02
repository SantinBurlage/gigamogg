with open("web/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    for kw in ["fetchLossHistory", "startQuickTrain", "stopTraining", "lossChartCanvas", "renderCatalogTiers"]:
        if kw in line:
            print(f"Line {i+1}: {kw} -> {line.strip()[:80]}")
