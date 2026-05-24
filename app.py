import streamlit as st
import pandas as pd
import time
import urllib.parse
import os
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# --- CONFIGURAÇÕES DO SISTEMA ---
# IMPORTANTE: Insira o ID da sua planilha aqui
SPREADSHEET_ID = "1A2B3C4D_SUA_ID_REAL_JA_ESTA_SALVA_AQUI"

COR_LARANJA = "#FF8C00"
COR_PRETO = "#1A1A1A"
CAL_ID = "luizvszahra@gmail.com"

# --- ENGINE DE CONEXÃO COM O GOOGLE SHEETS ---
def carregar_aba_sheets(nome_aba, colunas_padrao):
    try:
        aba_cod = urllib.parse.quote(nome_aba.strip())
        url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{SPREADSHEET_ID}/gviz/tq?tqx=out:csv"
            f"&sheet={aba_cod}"
        )
        df = pd.read_csv(url)
        if df.empty:
            return pd.DataFrame(columns=colunas_padrao)
        df.columns = df.columns.str.strip()
        return df.fillna("").astype(str)
    except Exception as e:
        st.sidebar.error(f"Erro na aba '{nome_aba}'")
        return pd.DataFrame(columns=colunas_padrao)

def salvar_no_sheets(nome_aba, novo_df, colunas_padrao):
    st.info("Use o painel para salvar permanentemente.")
    return True

def get_next_id():
    cols = ["ID", "Data", "Cliente", "Total", "Status"]
    df = carregar_aba_sheets("orcamentos", cols)
    if df.empty or "ID" not in df.columns: 
        return "1000"
    try:
        ids = pd.to_numeric(df["ID"], errors='coerce')
        ids = ids.dropna()
        return "1000" if ids.empty else str(int(ids.max() + 1))
    except: 
        return "1000"

def enviar_whatsapp(nome, tel, dt, hr, ender):
    m = (
        f"Olá {nome}, aqui é o Luiz da Técnico Zahra! ⚡\n\n"
        f"Confirmando visita:\nData: {dt}\nHorário: {hr}\n"
        f"Endereço: {ender}"
    )
    num = "".join(c for c in str(tel) if c.isdigit())
    if not num.startswith("55"): 
        num = "55" + num
    return (
        f"https://api.whatsapp.com/send?phone={num}"
        f"&text={urllib.parse.quote(m)}"
    )

def calc_maps(ender):
    if not ender: 
        return "#"
    base = "https://www.google.com/maps/search/?api=1&query="
    return base + urllib.parse.quote(str(ender))

# --- CONFIGURAÇÃO DE ESTADOS ---
if 'orc_edit' not in st.session_state:
    st.session_state.orc_edit = None
if 'vis_edit' not in st.session_state:
    st.session_state.vis_edit = None
if 'pdf_gerado' not in st.session_state:
    st.session_state.pdf_gerado = None
if 'aba_atual' not in st.session_state:
    st.session_state.aba_atual = "🏠 Painel Principal"

# --- ENGINE DO PDF ---
class PDF_Zahra(FPDF):
    def header(self):
        self.set_fill_color(255, 140, 0)
        self.rect(0, 0, 210, 35, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 20)
        self.cell(0, 10, "TECNICO ZAHRA", ln=True)
        self.set_font("Arial", "", 10)
        msg = "Solucoes Eletricas Profissionais"
        self.cell(0, 5, msg, ln=True)
        self.ln(15)

def out_pdf(idx, dt, cli, ender
