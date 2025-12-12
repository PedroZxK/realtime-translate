import customtkinter as ctk
import tkinter as tk
from tkinter import font as tkfont
import threading
import mss
import numpy as np
import easyocr
from deep_translator import GoogleTranslator
from xpinyin import Pinyin
import keyboard
import sys
import ctypes
import psutil
import os
import time

APP_NAME = "HSR Dual Translator V13"
COR_TEXTO = "#FFFFFF"
COR_PINYIN = "#00FFFF"
COR_BORDA = "#000000" 
FONTE_FAMILIA = "Segoe UI"
FONTE_TAMANHO = 14
ESPACAMENTO = 15

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

if not is_admin():
    print("!!! ALERTA: Rode como ADMINISTRADOR para as teclas funcionarem no jogo !!!")

try:
    p = psutil.Process(os.getpid())
    p.nice(psutil.HIGH_PRIORITY_CLASS)
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except: pass

def agrupar_blocos(resultados, limiar_vertical=45):
    if not resultados: return []
    resultados.sort(key=lambda x: x[0][0][1])

    blocos = []
    bloco_atual = None

    for (bbox, texto, conf) in resultados:
        if len(texto) < 1 or conf < 0.4: continue
        if any(x in texto for x in ["UID", "FPS", "ms", "::", "Loading"]): continue
        
        tl, _, br, _ = bbox
        y_top, y_bottom = int(tl[1]), int(br[1])
        x_left, w = int(tl[0]), int(br[0] - tl[0])
        h = y_bottom - y_top

        if bloco_atual is None:
            bloco_atual = {"texto": texto, "x": x_left, "y": y_top, "w": w, "h": h, "bottom": y_bottom}
        else:
            if (y_top - bloco_atual["bottom"] < limiar_vertical) and (abs(x_left - bloco_atual["x"]) < 150):
                bloco_atual["texto"] += " " + texto
                bloco_atual["h"] = y_bottom - bloco_atual["y"]
                bloco_atual["w"] = max(bloco_atual["w"], w)
                bloco_atual["bottom"] = y_bottom
            else:
                blocos.append(bloco_atual)
                bloco_atual = {"texto": texto, "x": x_left, "y": y_top, "w": w, "h": h, "bottom": y_bottom}
    
    if bloco_atual: blocos.append(bloco_atual)
    return blocos

class OverlayWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.overrideredirect(True)
        self.wm_attributes("-topmost", True)
        self.transparency_key = "#000001"
        self.wm_attributes("-transparentcolor", self.transparency_key)
        self.config(bg=self.transparency_key)
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")
        
        self.canvas = tk.Canvas(self, bg=self.transparency_key, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.font_bold = tkfont.Font(family=FONTE_FAMILIA, size=FONTE_TAMANHO, weight="bold")

    def limpar(self):
        self.canvas.delete("all")

    def desenhar_texto(self, x, y, texto, cor_principal):
        offsets = [(-1, -1), (-1, 1), (1, -1), (1, 1), (0, 2), (0, -2), (2, 0), (-2, 0)]
        for ox, oy in offsets:
            self.canvas.create_text(x+ox, y+oy, text=texto, font=self.font_bold, fill=COR_BORDA, anchor="nw")
        # Texto principal
        self.canvas.create_text(x, y, text=texto, font=self.font_bold, fill=cor_principal, anchor="nw")

    def renderizar(self, blocos, cor_texto):
        self.limpar()
        blocos.sort(key=lambda b: b['y'])
        ultimo_y = -100

        for b in blocos:
            if 'resultado' not in b: continue
            
            texto = b['resultado']
            x, y = b['x'], b['y']

            linhas = texto.split('\n')
            altura_bloco = (len(linhas) * (FONTE_TAMANHO + 8)) + 10
            
            draw_y = y - altura_bloco - 5
            if draw_y < 10: draw_y = y + b['h'] + 10
            if draw_y < ultimo_y + ESPACAMENTO: draw_y = ultimo_y + ESPACAMENTO

            self.desenhar_texto(x, draw_y, texto, cor_texto)
            ultimo_y = draw_y + altura_bloco

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Chinese Translator")
        self.geometry("350x300")
        self.attributes("-topmost", True)
        ctk.set_appearance_mode("Dark")

        self.modo_ativo = None
        self.ocupado = False

        self.lbl_status = ctk.CTkLabel(self, text="Carregando...", font=("Arial", 18, "bold"), text_color="orange")
        self.lbl_status.pack(pady=20)
        
        info = "F8: Pinyin (Sons)\nF9: Português\nF12: Fechar"
        self.lbl_info = ctk.CTkLabel(self, text=info, font=("Arial", 14))
        self.lbl_info.pack(pady=10)

        if is_admin():
            ctk.CTkLabel(self, text="✅ Admin OK", text_color="green").pack()
        else:
            ctk.CTkLabel(self, text="⚠️ Sem Admin", text_color="red").pack()

        self.overlay = OverlayWindow(self)
        threading.Thread(target=self.setup_ia, daemon=True).start()

        keyboard.add_hotkey('f8', lambda: self.ativar_modo('pinyin'))
        keyboard.add_hotkey('f9', lambda: self.ativar_modo('pt'))
        keyboard.add_hotkey('f12', self.sair)

    def setup_ia(self):
        try:
            self.reader = easyocr.Reader(['ch_sim'], gpu=True, verbose=False)
            self.translator = GoogleTranslator(source='zh-CN', target='pt')
            self.pinyin_gen = Pinyin()
            
            self.reader.readtext(np.zeros((50, 50, 3), dtype=np.uint8))
            self.lbl_status.configure(text="PRONTO", text_color="white")
        except Exception as e:
            self.lbl_status.configure(text=f"Erro Load: {e}", text_color="red")

    def ativar_modo(self, novo_modo):
        if self.ocupado: return

        if self.modo_ativo == novo_modo:
            self.overlay.limpar()
            self.modo_ativo = None
            self.lbl_status.configure(text="LIMPO", text_color="white")
            return

        self.modo_ativo = novo_modo
        threading.Thread(target=self.processar, args=(novo_modo,), daemon=True).start()

    def quebrar_texto(self, texto, limite=40):
        words = texto.split()
        final_str = ""
        line_len = 0
        for w in words:
            final_str += w + " "
            line_len += len(w)
            if line_len > limite:
                final_str += "\n"
                line_len = 0
        return final_str

    def processar(self, modo):
        self.ocupado = True
        nome_modo = "PINYIN" if modo == 'pinyin' else "PORTUGUÊS"
        self.lbl_status.configure(text=f"Lendo ({nome_modo})...", text_color="yellow")
        
        try:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                img = np.array(sct.grab(monitor))

            if hasattr(self, 'reader'):
                raw = self.reader.readtext(img, paragraph=False)
                blocos = agrupar_blocos(raw)

                if not blocos:
                    self.lbl_status.configure(text="Nada encontrado", text_color="orange")
                    self.modo_ativo = None
                else:
                    self.lbl_status.configure(text=f"Processando {nome_modo}...", text_color="cyan")
                    
                    for b in blocos:
                        txt_limpo = b['texto'].replace(" ", "")
                        
                        try:
                            if modo == 'pt':
                                trad = self.translator.translate(txt_limpo)
                                b['resultado'] = self.quebrar_texto(trad if trad else "...")
                                cor = COR_TEXTO
                            else:
                                pinyin_txt = self.pinyin_gen.get_pinyin(txt_limpo, ' ', tone_marks='marks')
                                b['resultado'] = self.quebrar_texto(pinyin_txt)
                                cor = COR_PINYIN
                        except:
                            b['resultado'] = "Erro"

                    if self.modo_ativo == modo:
                        self.overlay.after(0, lambda: self.overlay.renderizar(blocos, cor))
                        self.lbl_status.configure(text=f"EXIBINDO {nome_modo}", text_color="#00FF7F")
        
        except Exception as e:
            print(e)
            self.lbl_status.configure(text="Erro Interno", text_color="red")
            self.modo_ativo = None

        self.ocupado = False

    def sair(self):
        self.overlay.destroy()
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    App().mainloop()