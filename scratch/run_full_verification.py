import json
import urllib.request
import urllib.parse
import time
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def post(url, data, token=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            **({'Authorization': f'Bearer {token}'} if token else {})
        }
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode('utf-8'))

def get(url, token=None):
    req = urllib.request.Request(
        url,
        headers={**({'Authorization': f'Bearer {token}'} if token else {})}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode('utf-8'))

print("=== 1. TEST AUTHENTICATION & DATABASE ===")
me_guest = get('http://127.0.0.1:8000/api/auth/me')
print("Guest me:", me_guest)
assert me_guest.get('user') is None
assert me_guest.get('is_admin') is False

# Login as default admin Santin
admin_login = post('http://127.0.0.1:8000/api/auth/login', {'username': 'Santin', 'password': 'santin123'})
print("Admin login:", admin_login.get('ok'), admin_login.get('user'))
assert admin_login.get('ok') is True
assert admin_login.get('user', {}).get('role') == 'admin'
admin_token = admin_login.get('token')

me_admin = get('http://127.0.0.1:8000/api/auth/me', token=admin_token)
print("Admin me:", me_admin)
assert me_admin.get('is_admin') is True

# Register a regular user
user_login = post('http://127.0.0.1:8000/api/auth/register', {'username': f'testuser_{int(time.time())}', 'password': 'pass1234'})
print("User reg:", user_login.get('ok'), user_login.get('user'))
assert user_login.get('ok') is True
assert user_login.get('user', {}).get('role') == 'user'
user_token = user_login.get('token')

me_user = get('http://127.0.0.1:8000/api/auth/me', token=user_token)
print("User me:", me_user)
assert me_user.get('is_admin') is False

print("\n=== 2. TEST BENCHMARKS ===")
bench_cached = get('http://127.0.0.1:8000/api/benchmarks')
print("Cached benchmark overall score:", bench_cached.get('overall_score'))

bench_run = post('http://127.0.0.1:8000/api/benchmarks/run', {})
print("Ran benchmark overall score:", bench_run.get('overall_score'), "speed:", bench_run.get('throughput_tps'))
assert bench_run.get('overall_score') is not None

print("\n=== 3. TEST CREATOR & PERSONA & CONTEXT MEMORY ===")
history = []

# Turn 1: Creator question
q1 = "Кто твой создатель?"
history.append({"role": "user", "content": q1})
res1 = post('http://127.0.0.1:8000/api/chat', {"text": q1, "history": history})
ans1 = res1.get('answer', '')
print("Turn 1 Answer preview:", ans1[:250])
history.append({"role": "assistant", "content": ans1})
assert "Кирилл" in ans1 or "Santin" in ans1 or "бакунин" in ans1.lower(), f"Creator not recognized in: {ans1}"

# Turn 2: Memory fact deposit
q2 = "Запомни кодовое слово: АНАБИОЗ-772."
history.append({"role": "user", "content": q2})
res2 = post('http://127.0.0.1:8000/api/chat', {"text": q2, "history": history})
ans2 = res2.get('answer', '')
print("Turn 2 Answer preview:", ans2[:250])
history.append({"role": "assistant", "content": ans2})

# Turn 3: Memory recall
q3 = "Что я у тебя спрашивал до этого и какое кодовое слово я просил запомнить?"
history.append({"role": "user", "content": q3})
res3 = post('http://127.0.0.1:8000/api/chat', {"text": q3, "history": history})
ans3 = res3.get('answer', '')
print("Turn 3 Answer preview (Memory recall):", ans3[:350])
assert "не сохраняю" not in ans3.lower(), f"Model claimed no memory: {ans3}"
assert "создател" in ans3.lower() or "кто" in ans3.lower() or "анабиоз" in ans3.lower() or "772" in ans3, f"Memory failed: {ans3}"

print("\n=== 4. TEST WEB STUDIO & UNIQUE SITE GENERATION ===")
q4 = "Создай стильный современный сайт для крафтовой кофейни с темной темой, меню напитков и корзиной"
res4 = post('http://127.0.0.1:8000/api/chat', {"text": q4})
print("Turn 4 Web preview extracted:", bool(res4.get('html_preview')))
assert res4.get('html_preview') is not None, "Web preview not generated!"
assert "<html" in res4.get('html_preview').lower(), "Invalid HTML preview!"
print("Web preview length:", len(res4.get('html_preview')))

print("\nALL VERIFICATIONS PASSED WITH FLYING COLORS!")
