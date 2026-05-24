import streamlit as st
import pandas as pd
import time
import urllib.parse
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# --- CONFIGURAÇÕES DO SISTEMA ---
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
        df.columns = df.columns.str.strip()
        return df.fillna("").astype(str)
    except Exception as e:
        st.sidebar.error(f"Erro ao conectar na aba '{nome_aba}': {str(e)}")
        print(f"Erro ao conectar na aba '{nome_
