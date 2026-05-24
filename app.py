import streamlit as st
import pandas as pd
import time, io, urllib.parse, os
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# --- CONFIGURAÇÕES DE CONFIGURAÇÃO DIRETA ---
# COLOQUE APENAS O CÓDIGO DA SUA PLANILHA ENTRE AS ASPAS ABAIXO:
SPREADSHEET_ID = "1A2B3C4D_SUA_ID_REAL_JA_ESTA_SALVA_AQUI" 

COR_LARANJA, COR_PRETO = "#FF8C00", "#1A1A1A"
CAL_ID = "luizvszahra@gmail.com"

# --- CONEXÃO DIRETA VIA URL SEM SECRETS ---
def carregar_aba_sheets(nome_aba, colunas_padrao):
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={nome_aba}"
        df = pd.read_csv(url)
        if df.empty:
            return pd.DataFrame(columns=colunas_padrao)
        df.columns = df.columns.str.strip()
        return df.fillna("").astype(str)
    except:
        return pd.DataFrame(columns=colunas_padrao)

def salvar_no_sheets(nome_aba, novo_df, colunas_padrao):
    try:
        st.info("Para sincronizar e salvar novos registros na nuvem permanentemente, utilize o painel administrativo.")
        return True
    except:
        return False

def get_next_id():
    df = carregar_aba_sheets("orcamentos", ["ID", "Data", "Cliente", "Total", "Status", "Apresentacao", "Itens_JSON"])
    if df.empty or "ID" not in df.columns: return "1000"
    try:
        ids = pd.to_numeric(df["ID"], errors='coerce').dropna()
        return "1000" if ids.empty else str(int(ids.max() + 1))
    except: return "1000"

def enviar_whatsapp(nome, tel, dt, hr, ender):
    m = f"Olá {nome}, aqui é o Luiz da Técnico Zahra! ⚡\n\nEstou passando para confirmar nossa visita técnica:\nData: {dt}\nHorário: {hr}\nEndereço: {ender}"
    num = "".join(c for c in str(tel) if c.isdigit())
    if not num.startswith("55"): num = "55" + num
    return "https://api.whatsapp.com/send?phone=" + num + "&text=" + urllib.parse.quote(m)

def calc_maps(ender):
    if not ender: 
        return "#"
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(str(ender))

# --- ESTADOS INTERNOS ---
if 'orc_edit' not in st.session_state: st.session_state.orc_edit = None
if 'vis_edit' not in st.session_state: st.session_state.vis_edit = None
if 'ultimo_agendado' not in st.session_state: st.session_state.ultimo_agendado = None
if 'pdf_gerado' not in st.session_state: st.session_state.pdf_gerado = None
if 'aba_atual' not in st.session_state: st.session_state.aba_atual = "🏠 Painel Principal"

# --- MOTOR DE PDF ---
class PDF_Zahra(FPDF):
    def header(self):
        self.set_fill_color(255, 140, 0)
        self.rect(0,
