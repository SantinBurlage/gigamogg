import urllib.request

html = urllib.request.urlopen('http://127.0.0.1:8000/').read().decode('utf-8')
print("Has meta-pill-apex:", 'meta-pill-apex' in html)
print("Has p-train:", 'id="p-train"' in html)
print("Has Loss Curve:", 'Loss Curve' in html)
print("Has p-webstudio:", 'id="p-webstudio"' in html)
print("Has Cloud Neural Core:", 'Cloud Neural Core' in html)
print("Has GIGAMOGG Apex:", 'GIGAMOGG Apex' in html)
