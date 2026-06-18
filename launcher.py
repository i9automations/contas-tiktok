"""
LAUNCHER do CONTAS TIKTOK — auto-atualizavel.
Toda vez que abre, baixa a versao mais NOVA do app (navegador.py) do GitHub e
roda. Assim, o que voce atualizar no repositorio aparece no app na proxima
abertura. Sem internet, usa a ultima versao baixada (cache local).

Repo: https://github.com/i9automations/contas-tiktok
"""

import os
import sys
import time
import urllib.request

# A API do GitHub reflete a versao mais nova NA HORA. O raw.githubusercontent
# tem um cache (CDN) que ignora ?t= e servia versao velha -> por isso usamos a
# API primeiro, com o raw so de reserva.
API_URL = ("https://api.github.com/repos/i9automations/contas-tiktok/"
           "contents/navegador.py?ref=main")
RAW_URL = ("https://raw.githubusercontent.com/i9automations/"
           "contas-tiktok/main/navegador.py")


def _base_dir():
    # rodando como .exe (PyInstaller) -> pasta do exe; senao -> pasta do script
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


BASE = _base_dir()
CACHE = os.path.join(BASE, "_cache_app.py")   # ultima versao baixada (fallback)


def _baixar():
    tentativas = [
        # 1) API do GitHub (sempre fresca) — Accept raw devolve o arquivo cru
        (API_URL, {"Accept": "application/vnd.github.raw",
                   "User-Agent": "ContasTikTok-Launcher",
                   "Cache-Control": "no-cache"}),
        # 2) reserva: raw + timestamp
        (RAW_URL + "?t=" + str(int(time.time())),
         {"User-Agent": "ContasTikTok-Launcher", "Cache-Control": "no-cache"}),
    ]
    for url, hdr in tentativas:
        try:
            req = urllib.request.Request(url, headers=hdr)
            with urllib.request.urlopen(req, timeout=15) as r:
                txt = r.read().decode("utf-8")
            if txt.strip():
                return txt
        except Exception:
            continue
    raise RuntimeError("download falhou")


def main():
    codigo = None
    try:
        codigo = _baixar()                      # tenta sempre a versao mais nova
        try:
            with open(CACHE, "w", encoding="utf-8") as f:
                f.write(codigo)
        except Exception:
            pass
    except Exception:
        if os.path.exists(CACHE):               # offline -> usa o cache
            with open(CACHE, encoding="utf-8") as f:
                codigo = f.read()
    if not codigo:
        try:
            import tkinter as tk
            from tkinter import messagebox
            tk.Tk().withdraw()
            messagebox.showerror(
                "Sem internet",
                "Preciso de internet na PRIMEIRA vez pra baixar o app.\n"
                "Conecte a internet e abra de novo.")
        except Exception:
            pass
        return
    # roda o app baixado (o navegador.py). __file__ = CACHE -> a pasta de dados
    # (navegadores/, contas.json) fica ao lado do exe.
    g = {"__name__": "__main__", "__file__": CACHE}
    exec(compile(codigo, CACHE, "exec"), g)


if __name__ == "__main__":
    main()
