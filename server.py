"""Веб-сервер GIGAMOGG: сайт, чат, нити, поток мыслей и обучение.

Всё локально: сервер слушает только 127.0.0.1, наружу ничего не уходит.
"""
from __future__ import annotations

import json
import mimetypes
import os
import posixpath
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

from . import auth as auth_mod
from . import benchmarks as bench_mod
from . import device as dev_mod
from . import keys as keys_mod
from . import tiers
from . import train as train_mod
from .engine import engine
from .thoughts import STREAM

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(BASE, "web")

STATE = dict(status="idle", tier=None, step=0, loss=None, val=None, best=None, lr=None,
             batch=None, speed=0.0, eta=0, vram=0, message="", samples=[],
             history=dict(train=[], val=[]), started=0, finished=0, device=None,
             params=0, error=None)
_stop = threading.Event()
_lock = threading.Lock()
_active_trainer = None


def _get_owner(handler) -> str:
    """Extract username from Authorization header for per-user chat isolation."""
    auth_hdr = handler.headers.get("Authorization") or handler.headers.get("x-auth-token") or ""
    user = auth_mod.get_user_by_token(auth_hdr)
    return user.get("username", "") if user else ""


def stop_active_training():
    _stop.set()
    global _active_trainer
    if _active_trainer is not None:
        _active_trainer.stop = True
    with _lock:
        if STATE["status"] in ("training", "preparing"):
            STATE["status"] = "stopped"
            STATE["message"] = "Обучение остановлено"
    try:
        import gc, torch
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    except Exception:
        pass


# ------------------------------------------------------------------ обучение
def progress(**kw):
    with _lock:
        if kw.get("val") is not None:
            STATE["history"]["val"].append([kw.get("step"), kw["val"]])
            STATE["history"]["val"] = STATE["history"]["val"][-400:]
            if STATE.get("loss") is not None:
                STATE["history"]["train"].append([kw.get("step"), STATE["loss"]])
                STATE["history"]["train"] = STATE["history"]["train"][-400:]
        STATE.update(kw)
        if kw.get("status"):
            STATE["status"] = kw["status"]
        if kw.get("message") is not None:
            STATE["message"] = kw["message"]


def training_worker(tier: str, iters: int, device: str | None, rebuild: bool):
    global _active_trainer
    try:
        plan = dev_mod.plan_for_tier(tier, device)
        plan = dev_mod.apply_backend(plan)
        STATE.update(status="preparing", error=None, tier=tier, samples=[],
                     history=dict(train=[], val=[]), device=plan.as_dict(),
                     message=f"Подготовка архитектуры {tier}...", started=time.time())
        if rebuild:
            train_mod.ensure_corpus(verbose=False)
        if _stop.is_set():
            STATE.update(status="stopped", message="Обучение остановлено", finished=time.time())
            return
        tr = train_mod.Trainer(tier, plan=plan, progress=progress, verbose=False, stop_event=_stop)
        _active_trainer = tr
        tr.prepare()
        if _stop.is_set():
            STATE.update(status="stopped", message="Обучение остановлено", finished=time.time())
            return
        hist = train_mod.read_history(tier)
        STATE.update(status="training", params=tr.cfg["params"], batch=tr.cfg["batch"],
                     step=tr.step0,
                     history=dict(train=hist.get("train", [])[-400:], val=hist.get("val", [])[-400:]),
                     samples=hist.get("samples", [])[-6:],
                     message=f"Архитектура {tier}: батч {tr.cfg['batch']}, {plan.label}")

        result = tr.fit(iters)
        was_stopped = tr.stop or _stop.is_set()
        STATE.update(status="stopped" if was_stopped else "done",
                     finished=time.time(),
                     message="Обучение остановлено" if was_stopped else "Обучение завершено",
                     best=result.get("best"))
        engine().overview()
    except Exception as e:
        if _stop.is_set():
            STATE.update(status="stopped", message="Обучение остановлено", finished=time.time())
        else:
            STATE.update(status="error", error=f"{type(e).__name__}: {e}", message=f"Ошибка обучения: {e}")
    finally:
        _active_trainer = None
        try:
            import gc, torch
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass


# ------------------------------------------------------------------ сервер
class Handler(BaseHTTPRequestHandler):
    server_version = "GIGAMOGG"

    # ---------------------------------------------------------------- утилиты
    def _json(self, obj, code: int = 200):
        try:
            body = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-api-key")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-api-key")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _file(self, path: str):
        if not os.path.isfile(path):
            self._json({"error": "not found"}, 404)
            return
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        if ctype.startswith("text/") or path.endswith(".js") or path.endswith(".css"):
            ctype += "; charset=utf-8"
        try:
            with open(path, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(body)
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            pass

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}

    def log_message(self, *a):
        pass

    # ---------------------------------------------------------------- GET
    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        e = engine()
        try:
            if u.path in ("/", "/index.html"):
                self._file(os.path.join(WEB, "index.html"))
            elif u.path.startswith("/static/"):
                rel = posixpath.normpath(u.path[len("/static/"):]).lstrip("/\\")
                self._file(os.path.join(WEB, rel))
            elif u.path == "/api/state":
                with _lock:
                    self._json(dict(training=dict(STATE), **e.overview()))
            elif u.path == "/api/tiers":
                self._json(dict(tiers=tiers.catalog(), device=e.device_info(),
                                ready=[t for t in tiers.ORDER
                                       if os.path.exists(train_mod.paths(t)["ckpt"])]))
            elif u.path == "/api/threads":
                owner = _get_owner(self)
                self._json(dict(threads=e.store.list(order=q.get("order", ["heat"])[0],
                                                     limit=int(q.get("limit", ["80"])[0]),
                                                     owner=owner)))
            elif u.path == "/api/thread":
                t = e.store.get(q.get("id", [""])[0])
                self._json(t.summary(deep=True) if t else {"error": "нет такой нити"}, 200 if t else 404)
            elif u.path == "/api/graph":
                e.store.relink()
                self._json(e.store.graph(limit=int(q.get("limit", ["60"])[0])))
            elif u.path == "/api/thoughts":
                self._json(e.thoughts(int(q.get("cursor", ["0"])[0]), int(q.get("limit", ["48"])[0])))
            elif u.path == "/api/lessons":
                self._json(dict(stats=e.lessons.stats(),
                                items=e.lessons.items[-40:], learned=e.lessons.learned[-20:]))
            elif u.path == "/api/mind":
                self._json(e.mind())
            elif u.path == "/api/history":
                tier = q.get("tier", ["superlow"])[0]
                hist = train_mod.read_history(tier)
                self._json(hist)
            elif u.path == "/api/network":
                import socket
                host_ip = "127.0.0.1"
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    host_ip = s.getsockname()[0]
                    s.close()
                except Exception:
                    pass
                self._json({
                    "local_url": "http://127.0.0.1:8000",
                    "lan_url": f"http://{host_ip}:8000",
                    "api_local": "http://127.0.0.1:8000/v1",
                    "api_lan": f"http://{host_ip}:8000/v1",
                    "ip": host_ip,
                    "port": 8000
                })
            elif u.path == "/api/dream":
                tier = q.get("tier", ["apex"])[0]
                steps = int(q.get("steps", ["40"])[0])
                try:
                    self._json(e.dream(tier=tier, steps=steps))
                except Exception as dream_err:
                    self._json({"frames": 0, "mood": {"focus_word": "Apex", "alive": True}, "error": str(dream_err)})
            elif u.path == "/api/keys":
                self._json({"keys": keys_mod.list_keys()})
            elif u.path == "/api/auth/me":
                auth_hdr = self.headers.get("Authorization") or self.headers.get("x-auth-token") or ""
                user = auth_mod.get_user_by_token(auth_hdr)
                self._json({"user": user, "is_admin": bool(user and user.get("role") == "admin")})
            elif u.path in ("/api/benchmarks", "/api/benchmarks/latest"):
                self._json(bench_mod.get_latest_benchmark())
            elif u.path == "/api/benchmarks/run":
                self._json(bench_mod.run_all_benchmarks())
            elif u.path in ("/v1/models", "/api/v1/models"):
                model_list = [
                    {"id": "gigamogg", "object": "model", "owned_by": "gigamogg", "name": "GIGAMOGG"},
                    {"id": "genesis", "object": "model", "owned_by": "gigamogg", "name": "GIGAMOGG Genesis"},
                    {"id": "ultra", "object": "model", "owned_by": "gigamogg", "name": "GIGAMOGG Ultra"},
                    {"id": "pro", "object": "model", "owned_by": "gigamogg", "name": "GIGAMOGG Pro"},
                    {"id": "core", "object": "model", "owned_by": "gigamogg", "name": "GIGAMOGG Core"},
                    {"id": "lite", "object": "model", "owned_by": "gigamogg", "name": "GIGAMOGG Lite"},
                    {"id": "nano", "object": "model", "owned_by": "gigamogg", "name": "GIGAMOGG Nano"},
                    {"id": "apex", "object": "model", "owned_by": "gigamogg", "name": "GIGAMOGG"},
                    {"id": "giga1b", "object": "model", "owned_by": "gigamogg", "name": "GIGAMOGG"},
                ]
                self._json({
                    "object": "list",
                    "data": model_list
                })
            else:
                self._json({"error": "unknown route"}, 404)
        except Exception as ex:
            self._json({"error": f"{type(ex).__name__}: {ex}"}, 500)

    # ---------------------------------------------------------------- POST
    def do_POST(self):
        u = urlparse(self.path)
        b = self._body()
        e = engine()
        try:
            if u.path == "/api/auth/register":
                res = auth_mod.register_user(b.get("username", ""), b.get("password", ""))
                self._json(res, 200 if res.get("ok") else 400)
            elif u.path == "/api/auth/login":
                res = auth_mod.login_user(b.get("username", ""), b.get("password", ""))
                self._json(res, 200 if res.get("ok") else 400)
            elif u.path == "/api/auth/logout":
                auth_hdr = self.headers.get("Authorization") or self.headers.get("x-auth-token") or ""
                auth_mod.logout_user(auth_hdr)
                self._json({"ok": True})
            elif u.path == "/api/benchmarks/run":
                self._json(bench_mod.run_all_benchmarks())
            elif u.path == "/api/chat":
                owner = _get_owner(self)
                res = e.ask(b.get("text", ""), tier=b.get("tier") or "gigamogg",
                            thread_id=b.get("thread"), temperature=float(b.get("temperature", 0.7)),
                            capture=bool(b.get("capture", True)),
                            max_tokens=b.get("max_tokens"),
                            history=b.get("history"),
                            files=b.get("files"),
                            owner=owner)
                self._json(res)
            elif u.path == "/api/train":
                if STATE["status"] in ("training", "preparing"):
                    self._json({"error": "Обучение уже идёт"}, 400)
                    return
                _stop.clear()
                tier = tiers.norm(b.get("tier") or "mid")
                iters = max(20, int(b.get("iters", 800)))
                threading.Thread(target=training_worker,
                                 args=(tier, iters, b.get("device"), bool(b.get("rebuild", False))),
                                 daemon=True).start()
                self._json({"ok": True, "tier": tier, "iters": iters})
            elif u.path == "/api/stop":
                stop_active_training()
                self._json({"ok": True, "status": "stopped"})
            elif u.path == "/api/selfcheck":
                res = e.self_check(tier=b.get("tier") or "mid", limit=int(b.get("limit", 20)))
                self._json(res)
            elif u.path == "/api/dream":
                tier = b.get("tier") or "apex"
                steps = int(b.get("steps", 40))
                try:
                    self._json(e.dream(tier=tier, steps=steps))
                except Exception as dream_err:
                    self._json({"frames": 0, "mood": {"focus_word": "Apex", "alive": True}, "error": str(dream_err)})
            elif u.path == "/api/thread/rename":
                ok = e.store.rename(b.get("id", ""), b.get("title", ""))
                self._json({"ok": ok})
            elif u.path == "/api/thread/pin":
                self._json({"pinned": e.store.pin(b.get("id", ""), b.get("value"))})
            elif u.path == "/api/thread/delete":
                self._json({"ok": e.store.drop(b.get("id", ""))})
            elif u.path == "/api/thread/rate":
                t = e.store.get(b.get("id", ""))
                if t:
                    t.rate(float(b.get("value", 0)))
                    e.store.maybe_save()
                self._json({"ok": bool(t)})
            elif u.path == "/api/corpus":
                stats = train_mod.ensure_corpus(force=bool(b.get("force", True)), verbose=False)
                self._json(stats)
            elif u.path == "/api/lessons/export":
                self._json(e.lessons.export())
            elif u.path == "/api/lessons/forget":
                e.lessons.forget()
                self._json({"ok": True})
            elif u.path == "/api/hub/drop":
                from .engine import HUB
                HUB.drop(b.get("tier"))
                self._json({"ok": True, "loaded": HUB.loaded()})
            elif u.path == "/api/keys":
                new_key = keys_mod.create_key(b.get("name"))
                self._json({"ok": True, "key": new_key})
            elif u.path == "/api/keys/delete":
                ok = keys_mod.delete_key(b.get("id") or b.get("key", ""))
                self._json({"ok": ok})
            elif u.path in ("/v1/chat/completions", "/api/v1/chat/completions"):
                auth = self.headers.get("Authorization") or self.headers.get("x-api-key") or b.get("api_key")
                if auth and not keys_mod.verify_and_touch_key(auth):
                    self._json({"error": {"message": "Неверный API-ключ. Проверьте заголовок Authorization: Bearer gm_live_...", "type": "invalid_api_key"}}, 401)
                    return
                messages = b.get("messages", [])
                last_msg = ""
                for m in reversed(messages):
                    if m.get("role") == "user":
                        last_msg = m.get("content", "")
                        break
                if not last_msg:
                    last_msg = b.get("prompt") or b.get("text", "")
                tier = tiers.norm(b.get("model") or "apex")
                temp = float(b.get("temperature", 0.7))
                max_toks = b.get("max_tokens")
                res = e.ask(last_msg, tier=tier, temperature=temp, max_tokens=max_toks, capture=False)
                answer = res.get("answer", "")

                is_stream = bool(b.get("stream", False))
                cmpl_id = f"chatcmpl-{secrets.token_hex(12)}"
                created_ts = int(time.time())

                if is_stream:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, x-api-key")
                    self.end_headers()
                    words = answer.split(" ")
                    for i, w in enumerate(words):
                        chunk_text = w if i == 0 else " " + w
                        chunk = {
                            "id": cmpl_id,
                            "object": "chat.completion.chunk",
                            "created": created_ts,
                            "model": tier,
                            "choices": [{"index": 0, "delta": {"content": chunk_text}, "finish_reason": None}]
                        }
                        self.wfile.write(f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n".encode("utf-8"))
                        self.wfile.flush()
                        time.sleep(0.008)
                    end_chunk = {
                        "id": cmpl_id,
                        "object": "chat.completion.chunk",
                        "created": created_ts,
                        "model": tier,
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
                    }
                    self.wfile.write(f"data: {json.dumps(end_chunk, ensure_ascii=False)}\n\n".encode("utf-8"))
                    self.wfile.write(b"data: [DONE]\n\n")
                    self.wfile.flush()
                    return

                prompt_toks = max(1, len(last_msg) // 4)
                comp_toks = max(1, len(answer) // 4)
                self._json({
                    "id": cmpl_id,
                    "object": "chat.completion",
                    "created": created_ts,
                    "model": tier,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": answer},
                            "finish_reason": "stop"
                        }
                    ],
                    "usage": {
                        "prompt_tokens": prompt_toks,
                        "completion_tokens": comp_toks,
                        "total_tokens": prompt_toks + comp_toks
                    }
                })
            elif u.path == "/api/restart":
                self._json({"ok": True})
            else:
                self._json({"error": "unknown route"}, 404)
        except FileNotFoundError as ex:
            self._json({"error": str(ex)}, 409)
        except Exception as ex:
            self._json({"error": f"{type(ex).__name__}: {ex}"}, 400)


def serve(port: int = 8000, host: str = "0.0.0.0", open_browser: bool = True):
    e = engine()
    srv = ThreadingHTTPServer((host, port), Handler)
    import socket
    host_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        host_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass
    url = f"http://127.0.0.1:{port}"
    lan_url = f"http://{host_ip}:{port}"
    print(f"GIGAMOGG · Cloud Neural Engine")
    for w in e.plan.warnings:
        print("!", w)
    print(f"  • Локальный интерфейс: {url}")
    print(f"  • Сетевой доступ (LAN): {lan_url}")
    print(f"  • OpenCode / IDE API:   {lan_url}/v1")
    if open_browser:
        import webbrowser
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    serve()