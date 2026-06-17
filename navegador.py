"""
CONTAS TIKTOK — gerenciador de perfis estilo Dolphin (simples, SEM proxy,
SEM anti-deteccao). Cada "conta" e um PERFIL DO CHROME proprio:
  - voce cria a conta (um nome de cliente),
  - clica Abrir -> abre o Chrome NAQUELE perfil, na tela de login do TikTok Seller,
  - voce loga UMA vez,
  - fechou e abriu de novo -> continua logado naquele perfil.

Usa os PERFIS NATIVOS do Chrome (--profile-directory): cada cliente ganha uma
COR e um NOME proprios, que aparecem no Chrome e na barra de tarefas (igual o
Dolphin mostra os perfis coloridos). Cada janela e independente: pode fechar este
gerenciador que os navegadores continuam abertos.

⚠️ Sem proxy nem anti-deteccao: todas as contas parecem o MESMO aparelho/IP.
O TikTok PODE relacionar elas. Veja o LEIA-ME.txt.
"""

import os
import re
import json
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox

PASTA = os.path.dirname(os.path.abspath(__file__))
CHROME_UDD = os.path.join(PASTA, "navegadores")   # pasta-mae dos perfis do Chrome
REG = os.path.join(PASTA, "contas.json")           # lista de contas (clientes)
LOGIN_URL = "https://seller-br.tiktok.com/account/login"

# ---- tema escuro ----
BG     = "#13151a"
CARD   = "#1b1e26"
HEADER = "#0c0d11"
FG     = "#e6e9ef"
MUTED  = "#8b93a7"
CYAN   = "#25f4ee"
PINK   = "#fe2c55"
GREEN  = "#34d399"
RED    = "#f87171"
FONT   = "Segoe UI"

# cores giradas por conta (so pra bolinha do app — o Chrome usa as dele)
CORES = ["#a78bfa", "#34d399", "#60a5fa", "#fbbf24", "#fb7185",
         "#22d3ee", "#f472b6", "#4ade80", "#818cf8", "#fca5a5"]


def achar_chrome():
    """Acha o Google Chrome instalado (locais comuns no Windows)."""
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
    """Nome de pasta seguro (tira so caracteres proibidos no Windows)."""
    return re.sub(r'[\\/:*?"<>|]', "", nome).strip() or "conta"


class App:
    def __init__(self, root):
        self.root = root
        self.chrome = achar_chrome()
        os.makedirs(CHROME_UDD, exist_ok=True)
        self.contas = self._carregar()
        root.title("Contas TikTok")
        root.configure(bg=BG)
        self._estilo()

        head = tk.Frame(root, bg=HEADER)
        head.pack(fill="x")
        tk.Label(head, text="●", fg=CYAN, bg=HEADER,
                 font=(FONT, 16)).pack(side="left", padx=(16, 6), pady=12)
        tk.Label(head, text="Contas TikTok", fg=FG, bg=HEADER,
                 font=(FONT, 15, "bold")).pack(side="left")
        tk.Label(head, text="gerenciador de logins", fg=MUTED, bg=HEADER,
                 font=(FONT, 11)).pack(side="left", padx=8)

        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=14)

        topo = tk.Frame(body, bg=BG)
        topo.pack(fill="x", pady=(0, 10))
        ttk.Button(topo, text="+ Nova conta", style="Cyan.TButton",
                   command=self.nova).pack(side="left")
        self.var_info = tk.StringVar()
        tk.Label(topo, textvariable=self.var_info, fg=MUTED, bg=BG,
                 font=(FONT, 9)).pack(side="right")

        container = tk.Frame(body, bg=BG)
        container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        sb = ttk.Scrollbar(container, orient="vertical",
                           command=self.canvas.yview)
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

    def _estilo(self):
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except Exception:
            pass

        def botao(nome, bg, fg, ativo):
            s.configure(nome, background=bg, foreground=fg, borderwidth=0,
                        focusthickness=0, font=(FONT, 10, "bold"),
                        padding=(14, 8))
            s.map(nome, background=[("active", ativo)])
        botao("Cyan.TButton", CYAN, "#06231f", "#5ff7f1")
        botao("Danger.TButton", CARD, RED, "#2a2f3a")

    # ---------- registro de contas ----------
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
        self.var_info.set(f"{len(self.contas)} conta(s)")
        if not self.contas:
            tk.Label(self.lista,
                     text="(nenhuma conta ainda — clique em '+ Nova conta')",
                     fg=MUTED, bg=BG, font=(FONT, 11)).pack(pady=24)
            return
        for i, nome in enumerate(self.contas):
            self._linha(i, nome)

    def _linha(self, i, nome):
        cor = CORES[i % len(CORES)]
        row = tk.Frame(self.lista, bg=CARD)
        row.pack(fill="x", pady=4)
        # "bolinha" colorida com a inicial (combina com a cor do perfil)
        bol = tk.Label(row, text=nome[:1].upper(), fg="#0c0d11", bg=cor,
                       font=(FONT, 12, "bold"), width=2)
        bol.pack(side="left", padx=(12, 10), pady=10)
        tk.Label(row, text=nome, fg=FG, bg=CARD,
                 font=(FONT, 12, "bold")).pack(side="left")
        ttk.Button(row, text="Remover", style="Danger.TButton",
                   command=lambda: self._remover(nome)).pack(side="right",
                                                             padx=(4, 12))
        ttk.Button(row, text="▶  Abrir", style="Cyan.TButton",
                   command=lambda: self._abrir(nome)).pack(side="right", padx=4)

    # ---------- acoes ----------
    def nova(self):
        nome = simpledialog.askstring(
            "Nova conta", "Nome do cliente (ex: Loja da Ana):",
            parent=self.root)
        if not nome:
            return
        nome = nome.strip()
        if not nome:
            return
        if nome in self.contas:
            messagebox.showinfo("Já existe", "Já tem uma conta com esse nome.")
            return
        self.contas.append(nome)
        self._salvar()
        self._semear_perfil(nome)
        self._montar_lista()
        messagebox.showinfo(
            "Conta criada",
            f"Conta '{nome}' criada!\n\nClique em 'Abrir', faca o login no TikTok "
            "(so dessa vez). Da proxima ja entra logado.\n\nDica: no Chrome, no "
            "canto superior direito, da pra trocar a COR/foto desse perfil.")

    def _perfil_dir(self, nome):
        return os.path.join(CHROME_UDD, _slug(nome))

    def _semear_perfil(self, nome):
        """Cria a pasta do perfil ja com o NOME do cliente, pro Chrome mostrar
        o nome (e dar uma cor) automaticamente."""
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
                "Remover conta",
                f"Remover '{nome}'?\n\nIsso APAGA o login salvo dela (vai "
                "precisar logar de novo).\nFeche o navegador dessa conta antes."):
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
        root.geometry(f"{int(560 * f)}x{int(560 * f)}")
        root.minsize(int(460 * f), int(420 * f))
    except Exception:
        pass
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
