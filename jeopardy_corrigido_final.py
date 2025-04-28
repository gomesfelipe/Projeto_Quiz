import os
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog
import pandas as pd
import ttkbootstrap as ttk
from ttkbootstrap.widgets import Meter
from playsound import playsound
import colorsys
import tkinter.font as tkFont

class JeopardyGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Jeopardy!")
        self.custom_font = ("BIBURY", 16)
        self.perguntas = self.carregar_perguntas()
        self.grupos = self.inicializar_grupos()
        self.pontuacoes = {grupo: 0 for grupo in self.grupos}
        self.labels_pontuacao = {}
        self.botoes = []
        self.labels_categorias = []
        self.categorias = list(self.perguntas.keys())
        self.criar_interface()

    def carregar_perguntas(self):
        arquivo_excel = os.path.join(os.getcwd(), 'perguntas_jeopardy.xlsx')
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
            if categoria not in perguntas:
                perguntas[categoria] = {}
            perguntas[categoria][valor] = (pergunta, resposta)
        return perguntas

    def inicializar_grupos(self):
        num_grupos = simpledialog.askinteger("Configuração", "Quantos grupos vão jogar?", minvalue=1, maxvalue=10)
        if num_grupos is None:
            messagebox.showerror("Erro", "Número de grupos não informado.")
            self.root.destroy()
            exit()
        grupos = []
        for i in range(num_grupos):
            nome_grupo = simpledialog.askstring("Nome do Grupo", f"Digite o nome do Grupo {i+1}:")
            grupos.append(nome_grupo if nome_grupo else f"Grupo {i+1}")
        return grupos

    def tocar_som(self, nome_arquivo):
        caminho_completo = os.path.join(os.getcwd(), nome_arquivo)
        if os.path.exists(caminho_completo):
            threading.Thread(target=lambda: playsound(caminho_completo), daemon=True).start()
        else:
            print(f"Arquivo de som não encontrado: {caminho_completo}")

    def atualizar_pontuacoes(self):
        for grupo, lbl in self.labels_pontuacao.items():
            lbl.config(text=f"{grupo}: {self.pontuacoes[grupo]} pts")

    def escolher_grupo(self):
        grupo_escolhido = tk.StringVar()
        popup = tk.Toplevel(self.root)
        popup.title("Escolher Grupo")
        popup.geometry("400x200")
        ttk.Label(popup, text="Qual grupo vai tentar responder?", font=self.custom_font).pack(pady=10)
        menu = ttk.OptionMenu(popup, grupo_escolhido, *self.grupos)
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

        resposta = {}

        def confirmar():
            resposta["valor"] = entry_resposta.get()
            popup.destroy()

        ttk.Button(frame_direita, text="Confirmar", command=confirmar).pack(pady=10)

        def atualizar_meter():
            nonlocal tempo_limite
            if "valor" not in resposta:
                meter.configure(amountused=tempo_limite)
                if tempo_limite > 20:
                    meter.configure(bootstyle="success")
                elif tempo_limite > 10:
                    meter.configure(bootstyle="warning")
                else:
                    meter.configure(bootstyle="danger")
                if tempo_limite <= 0:
                    resposta["valor"] = None
                    popup.destroy()
                else:
                    tempo_limite -= 1
                    popup.after(1000, atualizar_meter)

        atualizar_meter()
        popup.wait_window()

        return resposta.get("valor")

    def mostrar_pergunta(self, categoria, valor, botao):
        pergunta, resposta_correta = self.perguntas[categoria][valor]
        grupo = self.escolher_grupo()

        if grupo not in self.grupos:
            messagebox.showerror("Erro", "Grupo inválido. Pergunta anulada.")
            botao.config(state="disabled")
            self.verificar_fim()
            return

        resposta_usuario = self.abrir_pergunta_personalizada(f"Pergunta para {grupo}", pergunta)

        if resposta_usuario:
            if resposta_usuario.strip().lower() == resposta_correta.strip().lower():
                self.tocar_som('acerto.mp3')
                messagebox.showinfo("Resultado", "Correto!")
                self.pontuacoes[grupo] += valor
            else:
                self.tocar_som('erro.mp3')
                messagebox.showinfo("Resultado", f"Incorreto!\nResposta correta: {resposta_correta}")
        else:
            self.tocar_som('erro.mp3')
            messagebox.showinfo("Resultado", "Nenhuma resposta fornecida.")

        self.atualizar_pontuacoes()
        botao.config(state="disabled")
        self.verificar_fim()

    def verificar_fim(self):
        botoes_ativos = [botao for botao in self.botoes if botao["state"] == "normal"]
        if not botoes_ativos:
            ranking = sorted(self.pontuacoes.items(), key=lambda x: x[1], reverse=True)
            mensagem = "\n".join([f"{grupo}: {pontos} pts" for grupo, pontos in ranking])
            messagebox.showinfo("Fim de Jogo", f"Ranking Final:\n\n{mensagem}")
            self.root.quit()

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
                botao = tk.Button(frame_tabuleiro, text=str(valor), bg=cor_categoria, fg="white", font=self.custom_font)
                botao.grid(row=j+1, column=i, padx=5, pady=5, sticky="nsew")
                self.botoes.append(botao)
                botao.config(command=lambda c=categoria, v=valor, b=botao: self.mostrar_pergunta(c, v, b))

        for i in range(len(self.categorias)):
            frame_tabuleiro.grid_columnconfigure(i, weight=1)

        total_linhas = max(len(self.perguntas[categoria]) for categoria in self.perguntas) + 2
        for i in range(total_linhas):
            frame_tabuleiro.grid_rowconfigure(i, weight=1)

    def gerar_cores(self, qtd):
        return ['#%02x%02x%02x' % tuple(int(c*255) for c in colorsys.hsv_to_rgb(i/qtd, 0.7, 0.9)) for i in range(qtd)]

if __name__ == "__main__":
    root = ttk.Window(themename="superhero")
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
    app = JeopardyGame(root)
    root.mainloop()
