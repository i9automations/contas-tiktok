"""
CONTAS TIKTOK — gerenciador de perfis (estilo Dolphin), UI em HTML/CSS.
Backend: Python PURO (http.server da biblioteca padrao, sem instalar nada).
Frontend: pagina HTML/CSS/JS, aberta numa janela do Chrome em modo APP.
Cada conta = um PERFIL do Chrome. Criar -> Iniciar -> loga 1x -> fica logado.
SEM proxy/anti-deteccao (veja LEIA-ME.txt).
"""

import os
import re
import json
import shutil
import threading
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PASTA = os.path.dirname(os.path.abspath(__file__))
CHROME_UDD = os.path.join(PASTA, "navegadores")      # perfis dos clientes
UI_UDD = os.path.join(PASTA, "_ui_profile")          # perfil da janela do app
REG = os.path.join(PASTA, "contas.json")
LOGIN_URL = "https://seller-br.tiktok.com/account/login"


def achar_chrome():
    cands = [
        os.path.join(os.environ.get("PROGRAMFILES", ""),
                     r"Google\Chrome\Application\chrome.exe"),
        os.path.join(os.environ.get("PROGRAMFILES(X86)", ""),
                     r"Google\Chrome\Application\chrome.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""),
                     r"Google\Chrome\Application\chrome.exe"),
    ]
    for c in cands:
        if c and os.path.exists(c):
            return c
    return shutil.which("chrome") or shutil.which("chrome.exe")


CHROME = achar_chrome()


def _slug(nome):
    return re.sub(r'[\\/:*?"<>|]', "", nome).strip() or "conta"


def carregar():
    try:
        with open(REG, encoding="utf-8") as f:
            return json.load(f).get("contas", [])
    except Exception:
        return []


def salvar(contas):
    try:
        with open(REG, "w", encoding="utf-8") as f:
            json.dump({"contas": contas}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def semear(nome):
    d = os.path.join(CHROME_UDD, _slug(nome))
    os.makedirs(d, exist_ok=True)
    prefs = os.path.join(d, "Preferences")
    if not os.path.exists(prefs):
        try:
            with open(prefs, "w", encoding="utf-8") as f:
                json.dump({"profile": {"name": nome}}, f)
        except Exception:
            pass


def abrir_perfil(nome):
    if not CHROME:
        return False
    semear(nome)
    subprocess.Popen([
        CHROME,
        f"--user-data-dir={CHROME_UDD}",
        f"--profile-directory={_slug(nome)}",
        "--no-first-run", "--no-default-browser-check", LOGIN_URL,
    ])
    return True


HTML = r"""<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Contas TikTok</title>
<style>
:root{
  --bg:#0e1217; --side:#0a0e13; --card:#19212c; --card2:#212c39;
  --chip:#26333f; --fg:#eaeef4; --muted:#828d9c; --line:#222c38;
  --teal:#16c79a; --tealh:#1ee0af; --green:#27c07e; --greenh:#31d68d;
  --cy:#25f4ee; --pk:#fe2c55;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%}
body{font-family:'Segoe UI',system-ui,sans-serif;background:var(--bg);
  color:var(--fg);display:flex;overflow:hidden}
::-webkit-scrollbar{width:10px}
::-webkit-scrollbar-thumb{background:#2a3543;border-radius:6px}
::-webkit-scrollbar-track{background:transparent}

/* sidebar */
.side{width:230px;background:var(--side);height:100vh;flex-shrink:0;
  padding:22px 16px;display:flex;flex-direction:column;border-right:1px solid var(--line)}
.brand{display:flex;align-items:center;gap:10px;margin-bottom:26px;padding:0 6px}
.logo{width:40px;height:40px;border-radius:11px;background:#0c0d11;
  display:grid;place-items:center;position:relative;box-shadow:0 4px 14px #0008}
.logo b{font-size:20px;color:#fff;position:relative;z-index:2}
.logo .cy{position:absolute;color:var(--cy);transform:translate(2px,0);font-size:20px;font-weight:700}
.logo .pk{position:absolute;color:var(--pk);transform:translate(-2px,0);font-size:20px;font-weight:700}
.brand h1{font-size:17px;font-weight:700;letter-spacing:.2px}
.btn-criar{width:100%;border:0;border-radius:11px;background:var(--teal);
  color:#06231f;font-weight:700;font-size:14px;padding:12px;cursor:pointer;
  transition:.15s;display:flex;align-items:center;justify-content:center;gap:8px}
.btn-criar:hover{background:var(--tealh);transform:translateY(-1px)}
.navit{display:flex;align-items:center;gap:10px;padding:11px 12px;margin-top:18px;
  border-radius:10px;background:var(--card);font-weight:600;font-size:13px;
  position:relative;color:var(--fg)}
.navit::before{content:"";position:absolute;left:0;top:8px;bottom:8px;width:3px;
  background:var(--teal);border-radius:3px}
.count{color:var(--muted);font-size:12px;margin-top:14px;padding-left:6px}
.foot{margin-top:auto;color:#5d6775;font-size:10px;line-height:1.5}

/* main */
.main{flex:1;height:100vh;display:flex;flex-direction:column;overflow:hidden}
.top{display:flex;align-items:center;gap:14px;padding:22px 26px 12px}
.top h2{font-size:23px;font-weight:800;flex:1}
.search{background:var(--card);border:1px solid var(--line);border-radius:11px;
  color:var(--fg);padding:11px 14px;width:240px;font-size:13px;outline:none}
.search::placeholder{color:var(--muted)}
.search:focus{border-color:var(--teal)}
.thead{display:flex;justify-content:space-between;color:var(--muted);
  font-size:11px;font-weight:700;letter-spacing:.6px;padding:6px 30px;
  border-bottom:1px solid var(--line)}
.list{flex:1;overflow-y:auto;padding:14px 22px 22px}

/* card */
.card{display:flex;align-items:center;gap:14px;background:var(--card);
  border-radius:15px;padding:12px 16px;margin-bottom:10px;
  transition:.13s;border:1px solid transparent}
.card:hover{background:var(--card2);transform:translateY(-1px);
  border-color:#2f3b49;box-shadow:0 6px 18px #0006}
.ava{width:44px;height:44px;border-radius:50%;display:grid;place-items:center;
  font-weight:800;color:#0c0d11;font-size:17px;flex-shrink:0}
.nome{font-size:15px;font-weight:700;flex:1}
.tag{background:var(--chip);color:#8fb7ff;font-size:11px;font-weight:700;
  padding:5px 11px;border-radius:8px}
.start{border:0;border-radius:10px;background:var(--green);color:#06231f;
  font-weight:800;font-size:13px;padding:10px 18px;cursor:pointer;transition:.13s;
  display:flex;align-items:center;gap:7px}
.start:hover{background:var(--greenh)}
.del{background:none;border:0;color:var(--muted);font-size:17px;cursor:pointer;
  padding:8px;border-radius:9px;transition:.13s}
.del:hover{color:var(--pk);background:#2a1820}

/* vazio */
.vazio{text-align:center;color:var(--muted);margin-top:80px}
.vazio .ic{font-size:60px;opacity:.7}
.vazio h3{color:var(--fg);font-size:18px;margin:10px 0 4px}

/* modal */
.ov{position:fixed;inset:0;background:#000a;display:none;place-items:center;z-index:9}
.ov.on{display:grid}
.modal{background:var(--card);border-radius:16px;padding:24px;width:380px;
  box-shadow:0 20px 50px #000b;border:1px solid var(--line)}
.modal h3{font-size:17px;margin-bottom:6px}
.modal p{color:var(--muted);font-size:13px;margin-bottom:14px}
.modal input{width:100%;background:#0b0f14;border:1px solid var(--line);
  border-radius:10px;color:var(--fg);padding:12px;font-size:14px;outline:none}
.modal input:focus{border-color:var(--teal)}
.macts{display:flex;justify-content:flex-end;gap:10px;margin-top:18px}
.bsec{background:var(--chip);color:var(--fg);border:0;border-radius:10px;
  padding:10px 16px;font-weight:600;cursor:pointer}
.bsec:hover{background:#313e4c}
.bok{background:var(--teal);color:#06231f;border:0;border-radius:10px;
  padding:10px 18px;font-weight:700;cursor:pointer}
.bok:hover{background:var(--tealh)}
</style></head>
<body>
  <aside class="side">
    <div class="brand">
      <div class="logo"><span class="cy">♪</span><span class="pk">♪</span><b>♪</b></div>
      <h1>Contas TikTok</h1>
    </div>
    <button class="btn-criar" onclick="abrirModal()">+ &nbsp;Criar perfil</button>
    <div class="navit">📁 &nbsp;Todos os perfis</div>
    <div class="count" id="count">0 perfis</div>
    <div class="foot">sem proxy · sem anti-detecção<br>simples e direto</div>
  </aside>

  <main class="main">
    <div class="top">
      <h2>Todos os perfis</h2>
      <input class="search" id="busca" placeholder="🔎  Buscar perfil..."
             oninput="render()">
    </div>
    <div class="thead"><span>PERFIL</span><span>AÇÕES</span></div>
    <div class="list" id="list"></div>
  </main>

  <div class="ov" id="ov">
    <div class="modal">
      <h3 id="mtit">Novo perfil</h3>
      <p id="mmsg">Nome do cliente (ex: Loja da Ana):</p>
      <input id="mInput" autocomplete="off">
      <div class="macts">
        <button class="bsec" onclick="fecharModal()">Cancelar</button>
        <button class="bok" id="mok">OK</button>
      </div>
    </div>
  </div>

<script>
const CORES=["#a78bfa","#34d399","#60a5fa","#fbbf24","#fb7185","#22d3ee",
             "#f472b6","#4ade80","#818cf8","#f0883e"];
let CONTAS=[];

async function api(p,body){
  const o={method: body?'POST':'GET'};
  if(body){o.headers={'Content-Type':'application/json'};o.body=JSON.stringify(body)}
  const r=await fetch(p,o); return r.json();
}
async function load(){ CONTAS=(await api('/api/list')).contas||[]; render(); }

function render(){
  const f=(document.getElementById('busca').value||'').toLowerCase();
  document.getElementById('count').textContent=CONTAS.length+' perfis';
  const vis=CONTAS.filter(n=>n.toLowerCase().includes(f));
  const L=document.getElementById('list');
  if(!CONTAS.length){L.innerHTML=`<div class="vazio"><div class="ic">🗂️</div>
    <h3>Nenhum perfil ainda</h3><div>Clique em “+ Criar perfil”.</div></div>`;return}
  if(!vis.length){L.innerHTML=`<div class="vazio"><h3>Nada encontrado</h3></div>`;return}
  L.innerHTML=vis.map(n=>{
    const i=CONTAS.indexOf(n), c=CORES[i%CORES.length];
    const ini=n.trim()[0].toUpperCase();
    return `<div class="card">
      <div class="ava" style="background:${c}">${ini}</div>
      <div class="nome">${esc(n)}</div>
      <span class="tag">TikTok Shop</span>
      <button class="start" onclick="abrir('${esc(n)}')">▶ START</button>
      <button class="del" title="Remover" onclick="remover('${esc(n)}')">🗑</button>
    </div>`;}).join('');
}
function esc(s){return s.replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]))}

async function abrir(n){ await api('/api/open',{nome:n}); }
async function remover(n){
  pedir("Remover perfil","Remover '"+n+"'? Isso apaga o login salvo dele.",async()=>{
    await api('/api/delete',{nome:n}); load();
  },"Remover");
}
function abrirModal(){
  pedir("Novo perfil","Nome do cliente (ex: Loja da Ana):",async()=>{
    const v=document.getElementById('mInput').value.trim();
    if(!v) return;
    const r=await api('/api/create',{nome:v});
    if(r.erro){ alert(r.erro); return; }
    load();
  },"Criar");
}
let _cb=null;
function pedir(tit,msg,cb,okTxt){
  document.getElementById('mtit').textContent=tit;
  document.getElementById('mmsg').textContent=msg;
  document.getElementById('mok').textContent=okTxt||'OK';
  const inp=document.getElementById('mInput');
  inp.style.display=(tit==='Novo perfil')?'block':'none';
  inp.value='';
  document.getElementById('ov').classList.add('on');
  setTimeout(()=>inp.focus(),50);
  _cb=cb;
}
function fecharModal(){document.getElementById('ov').classList.remove('on');_cb=null;}
document.getElementById('mok').onclick=()=>{const cb=_cb;fecharModal();if(cb)cb();};
document.getElementById('mInput').addEventListener('keydown',e=>{
  if(e.key==='Enter'){const cb=_cb;fecharModal();if(cb)cb();}
});
document.addEventListener('keydown',e=>{if(e.key==='Escape')fecharModal();});
load();
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/index"):
            self._send(200, HTML, "text/html")
        elif self.path == "/api/list":
            self._send(200, json.dumps({"contas": carregar()}))
        else:
            self._send(404, "{}")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            dados = json.loads(self.rfile.read(n) or "{}")
        except Exception:
            dados = {}
        nome = (dados.get("nome") or "").strip()
        contas = carregar()
        if self.path == "/api/create":
            if not nome:
                return self._send(200, json.dumps({"erro": "Nome vazio"}))
            if nome in contas:
                return self._send(200, json.dumps(
                    {"erro": "Ja existe um perfil com esse nome."}))
            contas.append(nome)
            salvar(contas)
            semear(nome)
            self._send(200, json.dumps({"ok": True}))
        elif self.path == "/api/open":
            ok = abrir_perfil(nome)
            self._send(200, json.dumps({"ok": ok}))
        elif self.path == "/api/delete":
            if nome in contas:
                contas.remove(nome)
                salvar(contas)
            try:
                shutil.rmtree(os.path.join(CHROME_UDD, _slug(nome)),
                              ignore_errors=True)
            except Exception:
                pass
            self._send(200, json.dumps({"ok": True}))
        else:
            self._send(404, "{}")


def main():
    os.makedirs(CHROME_UDD, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{port}/"

    if CHROME:
        proc = subprocess.Popen([
            CHROME, f"--app={url}", f"--user-data-dir={UI_UDD}",
            "--no-first-run", "--no-default-browser-check",
            "--window-size=1120,720",
        ])
        proc.wait()                 # bloqueia ate fechar a janela do app
    else:
        import webbrowser
        webbrowser.open(url)        # sem Chrome: abre no navegador padrao
        try:
            input()
        except Exception:
            threading.Event().wait()
    try:
        server.shutdown()
    except Exception:
        pass


if __name__ == "__main__":
    main()
