# 🐉 Chinese Translator (V1)

> **Tradutor de Tela em Tempo Real para Jogos**
> *Tradução Chinês -> Português e Chinês -> Pinyin (Romanização)*

Este projeto é uma ferramenta de sobreposição (overlay) desenvolvida em Python que utiliza OCR (Reconhecimento Óptico de Caracteres) acelerado por GPU para ler textos em chinês na tela e fornecer tradução ou pronúncia instantânea sem sair do jogo.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![GPU](https://img.shields.io/badge/NVIDIA-CUDA%20Accelerated-green)
![Status](https://img.shields.io/badge/Status-Stable-brightgreen)

## ✨ Funcionalidades

* **Dual Mode Intuitivo:**
    * **Tecla F9:** Traduz o texto para **Português** (PT-BR).
    * **Tecla F8:** Exibe o **Pinyin** (Fonética/Som) para quem estuda o idioma.
* **Visual "Clean":** Texto branco com borda preta (estilo legenda de filme/Netflix), sem caixas de fundo intrusivas.
* **Smart Clustering:** Algoritmo próprio que agrupa linhas de texto quebradas verticalmente para garantir que o tradutor receba frases completas, aumentando a precisão.
* **Snapshot Mode:** O sistema congela a tradução na tela para leitura confortável. Ao pressionar a tecla novamente, a tela limpa.
* **Anti-Colisão:** O overlay calcula posições para evitar que uma tradução fique sobreposta a outra.

---

## 🛠️ Tecnologias Utilizadas

* **[EasyOCR](https://github.com/JaidedAI/EasyOCR):** Leitura de texto na tela (Pipeline de Deep Learning baseada em PyTorch).
* **[MSS](https://python-mss.readthedocs.io/):** Captura de tela ultra-rápida.
* **[Deep Translator](https://github.com/nidhaloff/deep-translator):** Integração com API do Google Translate.
* **[XPinyin](https://github.com/lxneng/xpinyin):** Conversão de Hanzi (caracteres) para Pinyin com tons.
* **[Tkinter/CustomTkinter](https://github.com/TomSchimansky/CustomTkinter):** Interface Gráfica e Overlay transparente.
* **Multithreading:** Para evitar congelamento da interface durante o processamento.

---

## ⚙️ Pré-requisitos e Instalação

Para obter a máxima performance (leitura em <1s), é **altamente recomendado** ter uma placa de vídeo NVIDIA (RTX/GTX).

### 1. Instalar Bibliotecas
Abra seu terminal na pasta do projeto e instale as dependências:

```bash
pip install customtkinter mss numpy easyocr deep-translator xpinyin keyboard psutil