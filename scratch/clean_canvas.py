with open('web/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("background: #00f2fe;", "background: #10b981;")
text = text.replace("box-shadow: 0 0 10px #00f2fe;", "box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);")
text = text.replace("50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 16px #00f2fe; }", "50% { transform: scale(1.15); opacity: 1; box-shadow: 0 0 12px rgba(16, 185, 129, 0.5); }")

text = text.replace("background:linear-gradient(135deg, #00f2fe, #8b5cf6); color:#000; font-weight:800; border-radius:4px;", "background:#141722; border:1px solid rgba(255,255,255,0.16); color:#ededed; font-weight:600; border-radius:4px;")

text = text.replace("ctx.strokeStyle = s.isPositive ? '#00f2fe' : '#c084fc';", "ctx.strokeStyle = s.isPositive ? 'rgba(255, 255, 255, 0.35)' : 'rgba(148, 163, 184, 0.2)';")
text = text.replace("ctx.shadowColor = s.isPositive ? '#00f2fe' : '#c084fc';", "ctx.shadowColor = 'transparent';")
text = text.replace("ctx.shadowColor = '#00f2fe';", "ctx.shadowColor = 'transparent';")
text = text.replace("synGrad.addColorStop(0, '#00f2fe');", "synGrad.addColorStop(0, 'rgba(255, 255, 255, 0.4)');")
text = text.replace("mlCtx.shadowColor = '#00f2fe';", "mlCtx.shadowColor = 'transparent';")
text = text.replace("grad.addColorStop(0.35, p.isPositive ? '#00f2fe' : '#c084fc');", "grad.addColorStop(0.35, p.isPositive ? 'rgba(255, 255, 255, 0.7)' : 'rgba(148, 163, 184, 0.5)');")
text = text.replace("mlCtx.fillStyle = isHovered ? '#00f2fe' : inCircuit ? '#ffffff' : isPosCol ? 'rgba(56, 189, 248, 0.7)' : 'rgba(192, 132, 252, 0.65)';", "mlCtx.fillStyle = isHovered ? '#ffffff' : inCircuit ? '#ffffff' : 'rgba(255, 255, 255, 0.45)';")
text = text.replace("color: p.isPositive ? '#38bdf8' : '#c084fc',", "color: 'rgba(255, 255, 255, 0.65)',")

with open('web/index.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Canvas colors updated to strict monochrome!")
