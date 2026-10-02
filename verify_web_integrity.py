with open("web/index.html", "r", encoding="utf-8") as f:
    c = f.read()

assert 'toggleLanguage()' in c, "Missing toggleLanguage"
assert 'openAuthModal()' in c, "Missing openAuthModal"
assert 'loadHtmlIntoStudio' in c, "Missing loadHtmlIntoStudio"
assert 'triggerRunBenchmark()' in c, "Missing triggerRunBenchmark"
assert 'bottomDisclaimer' in c, "Missing bottomDisclaimer"
assert 'Кирилл Бакунин' in c, "Missing creator"
assert 'Santin' in c, "Missing Santin"
assert 'conversationHistory.push' in c, "Missing history push"
assert 'webstudio-card-banner' in c, "Missing webstudio banner"

print("All index.html assertions passed successfully!")
