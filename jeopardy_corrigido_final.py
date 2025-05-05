import os
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
import pandas as pd
import random
import colorsys
from playsound import playsound
import ttkbootstrap as ttk
from ttkbootstrap.widgets import Meter
import unicodedata
import difflib

class TelaConfiguracao:
    def __init__(self, root):
        self.root = root
        self.resultado = None
        self.config_window = tk.Toplevel(root)
        self.config_window.title("Configurações do Jogo")
        self.config_window.geometry("900x370")
        self.config_window.minsize(900, 370)
        self.config_window.maxsize(900, 370)
        self.config_window.grab_set()

        self.custom_font = ("Times New Roman", 14)

        frame_principal = tk.Frame(self.config_window)
        frame_principal.pack(pady=10, padx=10, fill="both", expand=True)

        frame_esquerda = tk.Frame(frame_principal)
        frame_esquerda.grid(row=0, column=0, sticky="n")
        frame_direita = tk.Frame(frame_principal)
        frame_direita.grid(row=0, column=1, sticky="n", padx=20)

        frame_inferior = tk.Frame(self.config_window)
        frame_inferior.pack(pady=20)

        tk.Label(frame_esquerda, text="Quantos grupos?", font=self.custom_font).grid(row=0, column=0, sticky="w")
        self.entry_num_grupos = tk.Entry(frame_esquerda, font=self.custom_font, width=5)
        self.entry_num_grupos.grid(row=0, column=1, sticky="w")

        btn_confirmar_grupos = tk.Button(frame_esquerda, text="Confirmar", command=self.definir_nomes_grupos, font=self.custom_font)
        btn_confirmar_grupos.grid(row=0, column=2, padx=10)

        self.penalizar_erro = tk.BooleanVar()
        self.penalizar_pular = tk.BooleanVar()
        self.perguntas_secretas = tk.BooleanVar()

        tk.Checkbutton(frame_esquerda, text="Penalizar Resposta Errada", variable=self.penalizar_erro, font=self.custom_font).grid(row=1, column=0, columnspan=3, sticky="w", pady=5)
        tk.Checkbutton(frame_esquerda, text="Penalizar ao Pular Pergunta", variable=self.penalizar_pular, font=self.custom_font).grid(row=2, column=0, columnspan=3, sticky="w", pady=5)
        tk.Checkbutton(frame_esquerda, text="Incluir Perguntas Secretas com bônus", variable=self.perguntas_secretas, font=self.custom_font).grid(row=3, column=0, columnspan=3, sticky="w", pady=5)

        self.frame_nomes_grupos = tk.Frame(frame_direita)
        self.frame_nomes_grupos.pack()

        self.btn_iniciar = tk.Button(frame_inferior, text="Iniciar Jogo", command=self.confirmar_configuracoes, font=("Times New Roman", 16))
        self.btn_iniciar.pack()

    def definir_nomes_grupos(self):
        for widget in self.frame_nomes_grupos.winfo_children():
            widget.destroy()

        try:
            num = int(self.entry_num_grupos.get())
        except ValueError:
            messagebox.showerror("Erro", "Digite um número válido para os grupos.")
            return

        self.entries_nomes = []
        for i in range(num):
            tk.Label(self.frame_nomes_grupos, text=f"Nome do Grupo {i+1}:", font=self.custom_font).grid(row=i, column=0, sticky="e", pady=2)
            entry_nome = tk.Entry(self.frame_nomes_grupos, font=self.custom_font, width=20)
            entry_nome.grid(row=i, column=1, pady=2, padx=5)
            self.entries_nomes.append(entry_nome)

    def confirmar_configuracoes(self):
        grupos = [e.get() if e.get() else f"Grupo {i+1}" for i, e in enumerate(self.entries_nomes)]
        self.resultado = {
            "grupos": grupos,
            "penalizar_erro": self.penalizar_erro.get(),
            "penalizar_pular": self.penalizar_pular.get(),
            "perguntas_secretas": self.perguntas_secretas.get()
        }
        self.config_window.destroy()

class JeopardyGame:
    def __init__(self, root, configuracoes):
        self.root = root
        self.root.title("Jeopardy!")
        self.custom_font = ("Times New Roman", 16)

        self.perguntas = self.carregar_perguntas()
        self.grupos = configuracoes["grupos"]
        self.penalizar_resposta_errada = configuracoes["penalizar_erro"]
        self.penalizar_pular = configuracoes["penalizar_pular"]
        self.perguntas_secretas = configuracoes["perguntas_secretas"]
        
        self.valor_penalizacao = 1
        self.pontuacoes = {grupo: 0 for grupo in self.grupos}
        self.erros_grupos = {grupo: 0 for grupo in self.grupos}
        self.labels_pontuacao = {}
        self.botoes = []
        self.labels_categorias = []
        self.categorias = list(self.perguntas.keys())
        self.limite_erros = 3
        self.criar_interface()
        
    def carregar_perguntas(self):
        arquivo_excel = os.path.join(os.getcwd(), 'C:/Users/sn1075293/Documents/Projeto_Quiz/perguntas_jeopardy.xlsx')
        try:
            df = pd.read_excel(arquivo_excel)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar perguntas: {e}")
            self.root.destroy()
            exit()
        perguntas = {}
        for _, linha in df.iterrows():
            categoria = linha['Categoria']
            valor = int(linha['Valor'])
            pergunta = linha['Pergunta']
            resposta = linha['Resposta']
            alternativas = linha.get('Alternativas', None)
            if pd.notna(alternativas):
                alternativas = [alt.strip() for alt in alternativas.split(';')]
            else:
                alternativas = None
            if categoria not in perguntas:
                perguntas[categoria] = {}
            perguntas[categoria][valor] = (pergunta, resposta, alternativas)
        return perguntas

    def abrir_pergunta_com_alternativas(self, titulo, pergunta, alternativas, tempo_limite=30):
        popup = tk.Toplevel(self.root)
        popup.title(titulo)
        popup.geometry("800x500")
        popup.configure(bg="white")
        popup.grab_set()

        resposta = {"valor": None, "acao": None}

        tk.Label(popup, text=pergunta, font=self.custom_font, bg="white", wraplength=750).pack(pady=20)

        var_escolha = tk.StringVar()

        for alt in alternativas:
            tk.Radiobutton(popup, text=alt, variable=var_escolha, value=alt, font=self.custom_font, bg="white").pack(anchor="w", padx=20)

        def confirmar():
            resposta["valor"] = var_escolha.get()
            resposta["acao"] = "confirmar"
            popup.destroy()

        def pular():
            resposta["valor"] = None
            resposta["acao"] = "pular"
            popup.destroy()

        ttk.Button(popup, text="Confirmar", command=confirmar).pack(pady=10)
        ttk.Button(popup, text="Pular", command=pular).pack()

        # Timer opcional
        def countdown():
            nonlocal tempo_limite
            if resposta["acao"] is None:
                if tempo_limite <= 0:
                    resposta["acao"] = "tempo"
                    popup.destroy()
                else:
                    tempo_limite -= 1
                    popup.after(1000, countdown)

        countdown()
        popup.wait_window()
        return resposta

    def tocar_som(self, nome_arquivo):
        caminho_completo = os.path.join(os.getcwd(), nome_arquivo)
        if os.path.exists(caminho_completo):
            threading.Thread(target=lambda: playsound(caminho_completo), daemon=True).start()

    def atualizar_pontuacoes(self):
        for grupo, lbl in self.labels_pontuacao.items():
            lbl.config(text=f"{grupo}: {self.pontuacoes[grupo]} pts")

    def criar_interface(self):
        frame_superior = ttk.Frame(self.root)
        frame_superior.pack(fill="x", padx=10, pady=10)

        for idx, grupo in enumerate(self.grupos):
            lbl = ttk.Label(frame_superior, text=f"{grupo}: 0 pts", font=self.custom_font, anchor="center")
            lbl.grid(row=0, column=idx, padx=10)
            self.labels_pontuacao[grupo] = lbl

        frame_tabuleiro = ttk.Frame(self.root)
        frame_tabuleiro.pack(fill="both", expand=True)

        cores_personalizadas = self.gerar_cores(len(self.categorias))
        cores_categoria = {categoria: cores_personalizadas[i % len(cores_personalizadas)] for i, categoria in enumerate(self.categorias)}

        for i, categoria in enumerate(self.categorias):
            cor_categoria = cores_categoria.get(categoria, "lightgrey")
            label = tk.Label(frame_tabuleiro, text=categoria, font=self.custom_font, bg=cor_categoria, fg="white", justify="center", wraplength=150)
            label.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            self.labels_categorias.append(label)

            valores_ordenados = sorted(self.perguntas[categoria].keys())
            for j, valor in enumerate(valores_ordenados):
                botao = tk.Button(frame_tabuleiro, text=str(valor), bg=cor_categoria, fg="white", font=self.custom_font, cursor="hand2")
                botao.grid(row=j+1, column=i, padx=5, pady=5, sticky="nsew")
                self.botoes.append(botao)
                botao.config(command=lambda c=categoria, v=valor, b=botao: self.mostrar_pergunta(c, v, b))

                cor_original = cor_categoria
                cor_hover = "#fecd01"
                botao.bind("<Enter>", lambda e, b=botao, h=cor_hover: b.config(bg=h))
                botao.bind("<Leave>", lambda e, b=botao, n=cor_original: b.config(bg=n))

        for i in range(len(self.categorias)):
            frame_tabuleiro.grid_columnconfigure(i, weight=1)
            
    def escolher_grupo_para_pontuacao(self):
        grupos_disponiveis = self.grupos
        if not grupos_disponiveis:
            return None

        grupo_escolhido = tk.StringVar()
        grupo_escolhido.set(grupos_disponiveis[0])

        popup = tk.Toplevel(self.root)
        popup.title("Escolher Grupo para Pontuação")
        popup.geometry("400x200")
        ttk.Label(popup, text="Para qual grupo vai a pontuação?", font=self.custom_font).pack(pady=10)

        menu = ttk.OptionMenu(popup, grupo_escolhido, grupos_disponiveis[0], *grupos_disponiveis)
        menu.pack(pady=10)

        ttk.Button(popup, text="Confirmar", command=popup.destroy).pack(pady=10)
        popup.transient(self.root)
        popup.grab_set()
        self.root.wait_window(popup)

        return grupo_escolhido.get()


    def abrir_pergunta_personalizada(self, titulo, pergunta, tempo_limite=30):
        popup = tk.Toplevel(self.root)
        popup.title(titulo)
        popup.geometry("800x500")
        popup.configure(bg="white")
        popup.grab_set()

        frame_esquerda = tk.Frame(popup, bg="white")
        frame_esquerda.pack(side="left", fill="both", expand=False, padx=10, pady=10)
        frame_direita = tk.Frame(popup, bg="white")
        frame_direita.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        meter = Meter(frame_esquerda, bootstyle="success", amounttotal=tempo_limite, amountused=tempo_limite,
                      metertype="full", stripethickness=10, textfont=self.custom_font, subtext="Tempo", interactive=False)
        meter.pack(padx=10, pady=10, fill="both", expand=True)

        lbl_pergunta = tk.Label(frame_direita, text=pergunta, font=self.custom_font, wraplength=350, bg="white", justify="center")
        lbl_pergunta.pack(pady=20)

        entry_resposta = tk.Entry(frame_direita, font=self.custom_font, bd=5, relief="solid", bg="#f0f0f0", highlightthickness=2)
        entry_resposta.pack(pady=10, ipadx=10, ipady=10)
        entry_resposta.focus_set()

        resposta = {}

        def confirmar():
            resposta["valor"] = entry_resposta.get()
            resposta["acao"] = "confirmar"
            popup.destroy()

        def pular():
            resposta["valor"] = None
            resposta["acao"] = "pular"
            popup.destroy()

        entry_resposta.bind("<Return>", lambda event: confirmar())

        botoes_frame = tk.Frame(frame_direita, bg="white")
        botoes_frame.pack(pady=10)

        ttk.Button(botoes_frame, text="Confirmar", command=confirmar).grid(row=0, column=0, padx=5)
        ttk.Button(botoes_frame, text="Pular", command=pular).grid(row=0, column=1, padx=5)

        def atualizar_meter():
            nonlocal tempo_limite
            if "valor" not in resposta:
                meter.configure(amountused=tempo_limite)
                if tempo_limite <= 0:
                    resposta["valor"] = None
                    resposta["acao"] = "tempo"
                    popup.destroy()
                else:
                    tempo_limite -= 1
                    popup.after(1000, atualizar_meter)

        atualizar_meter()
        popup.wait_window()

        return resposta
    
    def normalizar(self, texto):
        texto = texto.strip().lower()
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')  # Remove acentos
        return texto

    def remover_o_que_e(self, texto):
        texto = texto.strip().lower()
        if texto.startswith("o que e "):
            return texto[8:]  # Remove "o que e " (sem acento)
        if texto.startswith("o que sao "):
            return texto[10:]  # Remove "o que sao " (sem acento)
        return texto
    
    def mostrar_pergunta(self, categoria, valor, botao):
        botao.config(state="disabled")
        pergunta, resposta_correta, alternativas = self.perguntas[categoria][valor]
        is_pergunta_secreta = self.perguntas_secretas and random.random() < 0.2

        if alternativas:
            resposta_usuario = self.abrir_pergunta_com_alternativas("Pergunta", pergunta, alternativas)
        else:
            resposta_usuario = self.abrir_pergunta_personalizada("Pergunta", pergunta)
        def animar_botao(botao, cor_final):
            original_color = botao.cget("bg")
            def piscar(count):
                if count > 0:
                    cor = cor_final if count % 2 == 0 else original_color
                    botao.config(bg=cor)
                    botao.after(150, lambda: piscar(count - 1))
                else:
                    botao.config(bg=original_color)
            piscar(4)

        if resposta_usuario["acao"] == "confirmar":
            if resposta_usuario["valor"]:
                resposta_aluno = self.normalizar(resposta_usuario["valor"])
                resposta_correta_norm = self.normalizar(resposta_correta)
                # Remove "o que é" ou "o que são" se houver
                resposta_aluno = self.remover_o_que_e(resposta_aluno)
                resposta_correta_norm = self.remover_o_que_e(resposta_correta_norm)

                similaridade = difflib.SequenceMatcher(None, resposta_aluno, resposta_correta_norm).ratio()

                if similaridade >= 0.8:  # >= 80% de similaridade, considera correto
                    self.tocar_som('acerto.mp3')
                    messagebox.showinfo("Resultado", "Correto!")
                    grupo_destino = self.escolher_grupo_para_pontuacao()
                    if grupo_destino:
                        ganho = valor * 2 if is_pergunta_secreta else valor
                        self.pontuacoes[grupo_destino] += ganho
                        self.atualizar_pontuacoes()
                    animar_botao(botao, "#28a745")
                else:
                    self.tocar_som('erro.mp3')
                    grupo_destino = self.escolher_grupo_para_pontuacao()
                    if grupo_destino:
                        if self.penalizar_resposta_errada:
                            penalidade = int(valor * self.valor_penalizacao)
                            self.pontuacoes[grupo_destino] -= penalidade
                        self.erros_grupos[grupo_destino] += 1
                        self.atualizar_pontuacoes()
                    messagebox.showinfo("Resultado", f"Incorreto!\nResposta correta: {resposta_correta}")
                    animar_botao(botao, "#dc3545")
        elif resposta_usuario["acao"] in ["pular", "tempo"]:
            grupo_destino = self.escolher_grupo_para_pontuacao()
            if grupo_destino:
                if self.penalizar_pular:
                    penalidade = int(valor * self.valor_penalizacao)
                    self.pontuacoes[grupo_destino] -= penalidade
                self.erros_grupos[grupo_destino] += 1
                self.atualizar_pontuacoes()
            messagebox.showinfo("Pular", "Pergunta pulada ou tempo esgotado.")
            animar_botao(botao, "#6c757d")
            
    def gerar_cores(self, qtd):
        cores = []
        for _ in range(qtd):
            h = random.random()
            s = 0.7
            v = 0.9
            rgb = colorsys.hsv_to_rgb(h, s, v)
            hex_color = '#%02x%02x%02x' % tuple(int(c*255) for c in rgb)
            cores.append(hex_color)
        return cores

if __name__ == "__main__":
    root = ttk.Window(themename="superhero")
    root.withdraw()
    configurador = TelaConfiguracao(root)
    root.wait_window(configurador.config_window)

    if configurador.resultado:
        root.deiconify()
        largura_tela = root.winfo_screenwidth()
        altura_tela = root.winfo_screenheight()
        largura_janela = 1280
        altura_janela = 720
        pos_x = (largura_tela // 2) - (largura_janela // 2)
        pos_y = (altura_tela // 2) - (altura_janela // 2)
        root.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")
        root.minsize(1024, 600)

        try:
            root.tk.call('font', 'create', 'BIBURY', '-family', 'BIBURY')
        except tk.TclError:
            print("Fonte personalizada não carregada corretamente.")

        root.bind("<Escape>", lambda e: root.destroy())
        app = JeopardyGame(root, configurador.resultado)
        root.mainloop()
