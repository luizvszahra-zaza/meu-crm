import streamlit as st
import pandas as pd
import time, io, urllib.parse, os
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# --- CONFIGURAÇÕES DE CONFIGURAÇÃO DIRETA ---
# LEMBRE-SE DE TROCAR ESTE TEXTO ABAIXO PELA ID REAL DA SUA PLANILHA
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
    if not ender: return "#"
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
        self.rect(0, 0, 210, 35, 'F')
        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 20)
        self.cell(0, 10, "TECNICO ZAHRA", ln=True, align="L")
        self.set_font("Arial", "", 10)
        self.cell(0, 5, "Solucoes Eletricas com Padrao Profissional", ln=True, align="L")
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
        pdf.cell(190, 10, f"  ORCAMENTO N {idx} | DATA: {dt}", ln=True, fill=True)
        pdf.ln(3)
        
        pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "B", 10)
        pdf.cell(190, 7, f"CLIENTE: {str(cli).upper()}", ln=True)
        pdf.multi_cell(190, 6, f"ENDERECO: {str(ender).upper()}")
        
        if apr.strip():
            pdf.ln(4); pdf.set_font("Arial", "B", 10)
            pdf.cell(190, 6, "APRESENTACAO DO SERVICO:", ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(190, 5, str(apr))
        
        pdf.ln(5); pdf.set_fill_color(255, 140, 0); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 10)
        pdf.cell(100, 10, " SERVICO", fill=True)
        pdf.cell(45, 10, " QTD / UNIT", fill=True, align="C")
        pdf.cell(45, 10, " TOTAL", fill=True, align="C")
        pdf.ln()
        
        pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 10)
        for _, r in items.iterrows():
            if str(r['Serviço']).strip():
                vu, qt = float(r['Valor Unit. (R$)']), float(r['Qtd'])
                pdf.cell(100, 8, f" {str(r['Serviço'])}", border=1)
                pdf.cell(45, 8, f"{int(qt)} x R$ {vu:.2f}", border=1, align="C")
                pdf.cell(45, 8, f"R$ {vu*qt:.2f}", border=1, align="R")
                pdf.ln()
                
        pdf.ln(4); pdf.set_fill_color(255, 140, 0); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 10)
        pdf.cell(145, 10, "TOTAL DO INVESTIMENTO: ", align="R", fill=True)
        pdf.cell(45, 10, f"R$ {float(tot):.2f}", align="R", fill=True, ln=True)
        
        pdf.ln(20); y_v = pdf.get_y(); pdf.line(20, y_v, 90, y_v)
        pdf.set_y(y_v + 2); pdf.set_x(20); pdf.set_font("Arial", "B", 9); pdf.cell(70, 5, "TECNICO ZAHRA", align="C")
        pdf.line(120, y_v, 190, y_v); pdf.set_y(y_v + 2); pdf.set_x(120)
        pdf.cell(70, 5, str(cli).upper(), align="C")
        
        n_f = f"orcamento_{idx}.pdf"; pdf.output(n_f); return n_f
    except Exception as err:
        st.error("Erro PDF: " + str(err)); return None

# --- INTERFACE ---
st.set_page_config(page_title="Técnico Zahra CRM", layout="wide", page_icon="⚡")

with st.sidebar:
    st.title("⚡ Técnico Zahra")
    if st.button("🔄 Sincronizar"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    aba = st.radio("Navegação", ["🏠 Painel Principal", "👥 Clientes", "🛠️ Agenda", "💰 Novo Orçamento", "📊 Histórico"], key="aba_atual")

# --- 🏠 PAINEL ---
if aba == "🏠 Painel Principal":
    st.title("🚀 Dashboard Técnico Zahra")
    df_o = carregar_aba_sheets("orcamentos",
