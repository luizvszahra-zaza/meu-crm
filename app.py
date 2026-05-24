import streamlit as st
import pandas as pd
import time
import urllib.parse
import os
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# --- CONFIGURAÇÕES DO SISTEMA ---
# IMPORTANTE: Coloque o ID de letras e números da sua planilha entre as aspas
SPREADSHEET_ID = "1A2B3C4D_SUA_ID_REAL_JA_ESTA_SALVA_AQUI"

COR_LARANJA = "#FF8C00"
COR_PRETO = "#1A1A1A"
CAL_ID = "luizvszahra@gmail.com"

# --- ENGINE DE CONEXÃO COM O GOOGLE SHEETS ---
def carregar_aba_sheets(nome_aba, colunas_padrao):
    try:
        aba_codificada = urllib.parse.quote(nome_aba.strip())
        url = (
            f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/"
            f"gviz/tq?tqx=out:csv&sheet={aba_codificada}"
        )
        df = pd.read_csv(url)
        if df.empty:
            return pd.DataFrame(columns=colunas_padrao)
        df.columns = df.columns.str.strip()
        return df.fillna("").astype(str)
    except Exception as e:
        st.sidebar.error(f"Erro na aba '{nome_aba}': Verifique o nome no Sheets.")
        print(f"Log Erro '{nome_aba}': {e}")
        return pd.DataFrame(columns=colunas_padrao)

def salvar_no_sheets(nome_aba, novo_df, colunas_padrao):
    st.info("Use o painel para salvar permanentemente.")
    return True

def get_next_id():
    cols = ["ID", "Data", "Cliente", "Total", "Status"]
    df = carregar_aba_sheets("orcamentos", cols)
    if df.empty or not df.columns.str.contains('id', case=False).any(): 
        return "1000"
    try:
        ids = pd.to_numeric(df["ID"], errors='coerce').dropna()
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
    return f"https://api.whatsapp.com/send?phone={num}&text={urllib.parse.quote(m)}"

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
        self.cell(0, 10, "TECNICO ZAHRA", ln=True, align="L")
        self.set_font("Arial", "", 10)
        msg = "Solucoes Eletricas com Padrao Profissional"
        self.cell(0, 5, msg, ln=True, align="L")
        self.ln(15)

def out_pdf(idx, dt, cli, ender, apr, items, tot):
    try:
        pdf = PDF_Zahra()
        pdf.add_page()
        pdf.set_y(40)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(100, 5, "CNPJ: 50.779.713/0001-73")
        pdf.cell(90, 5, "Contato: (41) 99610-2100", ln=True, align="R")
        pdf.ln(5)
        
        pdf.set_fill_color(26, 26, 26)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(190, 10, f"  ORCAMENTO N {idx}", ln=True, fill=True)
        pdf.ln(3)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(190, 7, f"CLIENTE: {str(cli).upper()}", ln=True)
        
        if apr.strip():
            pdf.ln(4)
            pdf.cell(190, 6, "APRESENTACAO DO SERVICO:", ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(190, 5, str(apr))
        
        pdf.ln(5)
        pdf.set_fill_color(255, 140, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 10, " SERVICO", fill=True)
        pdf.cell(45, 10, " QTD / UNIT", fill=True, align="C")
        pdf.cell(45, 10, " TOTAL", fill=True, align="C")
        pdf.ln()
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 10)
        for _, r in items.iterrows():
            if str(r['Serviço']).strip():
                vu = float(r['Valor Unit. (R$)'])
                qt = float(r['Qtd'])
                pdf.cell(100, 8, f" {str(r['Serviço'])}", border=1)
                pdf.cell(45, 8, f"{int(qt)} x R$ {vu:.2f}", border=1, align="C")
                pdf.cell(45, 8, f"R$ {vu*qt:.2f}", border=1, align="R")
                pdf.ln()
                
        pdf.ln(4)
        pdf.set_fill_color(255, 140, 0)
        pdf.set_text_color(255, 255, 25
