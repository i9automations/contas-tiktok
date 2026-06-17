"""
CONTAS TIKTOK — gerenciador de perfis (estilo Dolphin), simples, SEM proxy.
Cada conta = um PERFIL DO CHROME proprio (cor + nome, igual o Dolphin mostra).
Cria perfil -> Iniciar -> loga 1x -> fica logado pra sempre.

⚠️ Sem proxy/anti-deteccao: as contas parecem o MESMO PC/IP. Veja o LEIA-ME.txt.
"""

import os
import re
import json
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

PASTA = os.path.dirname(os.path.abspath(__file__))
CHROME_UDD = os.path.join(PASTA, "navegadores")
REG = os.path.join(PASTA, "contas.json")
LOGIN_URL = "https://seller-br.tiktok.com/account/login"

# ---- tema escuro estilo Dolphin ----
BG      = "#0f1318"   # fundo geral
TOPBAR  = "#141922"   # barra de cima
ROW     = "#161b22"   # linha
ROWHOV  = "#1d2530"   # linha hover
BORDER  = "#232a34"   # divisorias
FG      = "#e9edf3"   # texto
MUTED   = "#7d8794"   # texto apagado
TEAL    = "#16c79a"   # acento (criar)
GREEN   = "#21b87a"   # botao iniciar
GREENH  = "#27d68f"
REDX    = "#e5564e"
CHIP    = "#222a36"   # fundo das tags/status
FONT    = "Segoe UI"

CORES = ["#a78bfa", "#34d399", "#60a5fa", "#fbbf24", "#fb7185",
         "#22d3ee", "#f472b6", "#4ade80", "#818cf8", "#fca5a5"]


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


def _slug(nome):
    return re.sub(r'[\\/:*?"<>|]', "", nome).strip() or "conta"


class App:
    def __init__(self, root):
        self.root = root
        self.chrome = achar_chrome()
        os.makedirs(CHROME_UDD, exist_ok=True)
        self.contas = self._carregar()
        root.title("Contas TikTok")
        root.configure(bg=BG)

        # ===== barra de cima =====
        top = tk.Frame(root, bg=TOPBAR, height=58)
        top.pack(fill="x")
        top.pack_propagate(False)
        logo = tk.Canvas(top, width=30, height=30, bg=TOPBAR,
                         highlightthickness=0)
        logo.create_oval(4, 4, 26, 26, fill=TEAL, outline="")
        logo.create_text(15, 15, text="C", fill="#06231f",
                         font=(FONT, 12, "bold"))
        logo.pack(side="left", padx=(16, 8))
        tk.Label(top, text="Contas TikTok", fg=FG, bg=TOPBAR,
                 font=(FONT, 15, "bold")).pack(side="left")

        self.btn_criar = tk.Button(top, text="+  Criar perfil",
                                   command=self.nova, fg="#06231f", bg=TEAL,
                                   activebackground=GREENH, activeforeground="#06231f",
                                   font=(FONT, 10, "bold"), relief="flat", bd=0,
                                   cursor="hand2", padx=16, pady=8)
        self.btn_criar.pack(side="right", padx=16)

        # busca
        self.var_busca = tk.StringVar()
        busca = tk.Entry(top, textvariable=self.var_busca, bg=BG, fg=FG,
                         insertbackground=FG, relief="flat",
                         font=(FONT, 10), width=22)
        busca.pack(side="right", padx=8, ipady=6)
        self.var_busca.trace_add("write", lambda *a: self._montar_lista())
        tk.Label(top, text="Buscar:", fg=MUTED, bg=TOPBAR,
                 font=(FONT, 9)).pack(side="right")

        # ===== cabecalho da "tabela" =====
        hd = tk.Frame(root, bg=BG)
        hd.pack(fill="x", padx=16, pady=(14, 4))
        tk.Label(hd, text="PERFIL", fg=MUTED, bg=BG,
                 font=(FONT, 9, "bold")).pack(side="left")
        self.var_info = tk.StringVar()
        tk.Label(hd, textvariable=self.var_info, fg=MUTED, bg=BG,
                 font=(FONT, 9)).pack(side="right")

        # linha divisoria
        tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=16)

        # ===== lista rolavel =====
        cont = tk.Frame(root, bg=BG)
        cont.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        self.canvas = tk.Canvas(cont, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(cont, orient="vertical", command=self.canvas.yview)
        self.lista = tk.Frame(self.canvas, bg=BG)
        self._win = self.canvas.create_window((0, 0), window=self.lista,
                                              anchor="nw")
        self.lista.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(
            self._win, width=e.width))
        self.canvas.configure(yscrollcommand=sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(
            int(-e.delta / 120), "units"))

        if not self.chrome:
            messagebox.showwarning(
                "Chrome nao encontrado",
                "Nao achei o Google Chrome instalado.\n"
                "Instale o Chrome (google.com/chrome) e abra de novo.")
        self._montar_lista()

    # ---------- registro ----------
    def _carregar(self):
        try:
            with open(REG, encoding="utf-8") as f:
                return json.load(f).get("contas", [])
        except Exception:
            return []

    def _salvar(self):
        try:
            with open(REG, "w", encoding="utf-8") as f:
                json.dump({"contas": self.contas}, f, ensure_ascii=False,
                          indent=2)
        except Exception:
            pass

    def _montar_lista(self):
        for w in self.lista.winfo_children():
            w.destroy()
        filtro = self.var_busca.get().strip().lower()
        visiveis = [n for n in self.contas if filtro in n.lower()]
        self.var_info.set(f"{len(self.contas)} perfil(is)")
        if not self.contas:
            self._vazio("Nenhum perfil ainda. Clique em '+ Criar perfil'.")
            return
        if not visiveis:
            self._vazio("Nenhum perfil com esse nome.")
            return
        for i, nome in enumerate(self.contas):
            if nome in visiveis:
                self._linha(i, nome)

    def _vazio(self, txt):
        tk.Label(self.lista, text=txt, fg=MUTED, bg=BG,
                 font=(FONT, 11)).pack(pady=30)

    def _linha(self, i, nome):
        cor = CORES[i % len(CORES)]
        row = tk.Frame(self.lista, bg=ROW, height=58)
        row.pack(fill="x", pady=(0, 1))
        row.pack_propagate(False)

        def hover(_e, c):
            row.configure(bg=c)
            for w in row.winfo_children():
                if isinstance(w, tk.Label):
                    w.configure(bg=c)
        row.bind("<Enter>", lambda e: hover(e, ROWHOV))
        row.bind("<Leave>", lambda e: hover(e, ROW))

        # bolinha colorida com a inicial (= cor do perfil)
        bol = tk.Label(row, text=nome[:1].upper(), fg="#0c0d11", bg=cor,
                       font=(FONT, 12, "bold"), width=3)
        bol.pack(side="left", padx=(12, 12))
        tk.Label(row, text=nome, fg=FG, bg=ROW,
                 font=(FONT, 12, "bold")).pack(side="left")

        # acoes (direita)
        rem = tk.Button(row, text="🗑", command=lambda: self._remover(nome),
                        fg=MUTED, bg=ROW, activebackground=ROWHOV,
                        activeforeground=REDX, relief="flat", bd=0,
                        cursor="hand2", font=(FONT, 12))
        rem.pack(side="right", padx=(4, 14))
        ini = tk.Button(row, text="▶  Iniciar",
                        command=lambda: self._abrir(nome),
                        fg="#06231f", bg=GREEN, activebackground=GREENH,
                        activeforeground="#06231f", relief="flat", bd=0,
                        cursor="hand2", font=(FONT, 10, "bold"),
                        padx=16, pady=6)
        ini.pack(side="right", padx=4)
        # chip "perfil" (estilo status do Dolphin)
        tk.Label(row, text=" tiktok ", fg=MUTED, bg=CHIP,
                 font=(FONT, 8, "bold")).pack(side="right", padx=8)

    # ---------- acoes ----------
    def nova(self):
        nome = simpledialog.askstring(
            "Novo perfil", "Nome do cliente (ex: Loja da Ana):",
            parent=self.root)
        if not nome:
            return
        nome = nome.strip()
        if not nome:
            return
        if nome in self.contas:
            messagebox.showinfo("Ja existe", "Ja tem um perfil com esse nome.")
            return
        self.contas.append(nome)
        self._salvar()
        self._semear_perfil(nome)
        self._montar_lista()

    def _perfil_dir(self, nome):
        return os.path.join(CHROME_UDD, _slug(nome))

    def _semear_perfil(self, nome):
        d = self._perfil_dir(nome)
        os.makedirs(d, exist_ok=True)
        prefs = os.path.join(d, "Preferences")
        if not os.path.exists(prefs):
            try:
                with open(prefs, "w", encoding="utf-8") as f:
                    json.dump({"profile": {"name": nome}}, f)
            except Exception:
                pass

    def _abrir(self, nome):
        if not self.chrome:
            messagebox.showerror("Chrome nao encontrado",
                                 "Nao achei o Google Chrome instalado.")
            return
        self._semear_perfil(nome)
        try:
            subprocess.Popen([
                self.chrome,
                f"--user-data-dir={CHROME_UDD}",
                f"--profile-directory={_slug(nome)}",
                "--no-first-run",
                "--no-default-browser-check",
                LOGIN_URL,
            ])
        except Exception as e:
            messagebox.showerror("Erro ao abrir", str(e))

    def _remover(self, nome):
        if not messagebox.askyesno(
                "Remover perfil",
                f"Remover '{nome}'?\n\nIsso APAGA o login salvo dele (vai "
                "precisar logar de novo).\nFeche o navegador desse perfil antes."):
            return
        if nome in self.contas:
            self.contas.remove(nome)
            self._salvar()
        try:
            shutil.rmtree(self._perfil_dir(nome), ignore_errors=True)
        except Exception:
            pass
        self._montar_lista()


def _corrigir_dpi():
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main():
    _corrigir_dpi()
    root = tk.Tk()
    try:
        dpi = root.winfo_fpixels("1i")
        root.tk.call("tk", "scaling", dpi / 72.0)
        f = dpi / 96.0
        root.geometry(f"{int(720 * f)}x{int(620 * f)}")
        root.minsize(int(560 * f), int(440 * f))
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
