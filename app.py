import streamlit as st
import pandas as pd
import time, io, urllib.parse, os
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# --- CONFIGURAÇÕES DO SISTEMA ---
# IMPORTANTE: Verifique se o ID abaixo está exatamente igual ao da sua planilha
SPREADSHEET_ID = "1A2B3C4D_SUA_ID_REAL_JA_ESTA_SALVA_AQUI"

COR_LARANJA = "#FF8C00"
COR_PRETO = "#1A1A1A"
CAL_ID = "luizvszahra@gmail.com"

# --- ENGINE DE CONEXÃO COM O GOOGLE SHEETS ---
def carregar_aba_sheets(nome_aba, colunas_padrao):
    try:
        url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&"
            f"sheet={nome_aba}"
        )
        df = pd.read_csv(url)
        if df.empty:
            return pd.DataFrame(columns=colunas_padrao)
        # Remove espaços em branco antes e depois dos nomes das colunas
        df.columns = df.columns.str.strip()
        return df.fillna("").astype(str)
    except Exception as e:
        # Exibe o erro de conexão na tela de forma limpa para diagnóstico
        st.sidebar.error(f"Erro ao conectar na aba '{nome_aba}': {str(e)}")
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
        f
