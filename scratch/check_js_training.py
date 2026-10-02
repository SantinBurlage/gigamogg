with open("web/index.html", "r", encoding="utf-8") as f:
    text = f.read()

# Check for lingering training functions
for keyword in ["fetchLossHistory", "startQuickTrain", "stopTraining", "lossChartCanvas", "renderCatalogTiers"]:
    count = text.count(keyword)
    print(f"{keyword}: {count}")
