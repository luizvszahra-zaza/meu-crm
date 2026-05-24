import streamlit as st
import pandas as pd
import time, io, urllib.parse, os
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# --- CONFIGURAÇÕES DO SISTEMA ---
# Cole a ID da sua planilha entre as aspas abaixo:
SPREADSHEET_ID = "1A2B3C4D_SUA_ID_REAL_JA_ESTA_SALVA_AQUI"

COR_LARANJA = "#FF8C00"
COR_PRETO = "#1A1A1A"
CAL_ID = "luizvszahra@gmail.com"

# --- UTILITÁRIOS E CONEXÃO ---
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
    except:
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
        pdf.set_text_color(255, 255, 255)
        pdf.cell(145, 10, "TOTAL: ", align="R", fill=True)
        pdf.cell(45, 10, f"R$ {float(tot):.2f}", align="R", fill=True, ln=True)
        
        pdf.ln(20)
        y_v = pdf.get_y()
        pdf.line(20, y_v, 90, y_v)
        pdf.set_y(y_v + 2)
        pdf.set_x(20)
        pdf.cell(70, 5, "TECNICO ZAHRA", align="C")
        
        n_f = f"orcamento_{idx}.pdf"
        pdf.output(n_f)
        return n_f
    except Exception as err:
        st.error("Erro PDF: " + str(err))
        return None

# --- VIEWS (STREAMLIT INTERFACE) ---
st.set_page_config(page_title="Técnico Zahra CRM", layout="wide", page_icon="⚡")

with st.sidebar:
    st.title("⚡ Técnico Zahra")
    if st.button("🔄 Sincronizar"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    opcoes = ["🏠 Painel Principal", "👥 Clientes", "🛠️ Agenda", "💰 Novo Orçamento", "📊 Histórico"]
    aba = st.radio("Navegação", opcoes, key="aba_atual")

if aba == "🏠 Painel Principal":
    st.title("🚀 Dashboard Técnico Zahra")
    cols = ["ID", "Data", "Cliente", "Total", "Status"]
    df_o = carregar_aba_sheets("orcamentos", cols)
    fat = pend = 0
    if not df_o.empty and "Total" in df_o.columns:
        df_o["Total"] = pd.to_numeric(df_o["Total"], errors='coerce').fillna(0)
        fat = df_o[df_o["Status"] == "Aprovado"]["Total"].sum()
        pend = df_o[df_o["Status"] == "Pendente"]["Total"].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("FATURADO (APROVADO)", f"R$ {fat:.2f}")
    col2.metric("PENDENTE", f"R$ {pend:.2f}")

    st.divider()
    c_cal, c_age = st.columns([4, 2])
    with c_cal:
        st.subheader("📅 Seu Calendário Google")
        url_cal = f"https://calendar.google.com/calendar/embed?src={CAL_ID}&ctz=America%2FSao_Paulo&bgcolor=%23ffffff"
        components.iframe(url_cal, height=500)
    with c_age:
        st.subheader("📌 Próximas Visitas")
        cols_v = ["ID_V", "Cliente", "Data", "Hora", "Endereco"]
        df_v = carregar_aba_sheets("visitas", cols_v)
        if not df_v.empty and "Cliente" in df_v.columns:
            for _, r in df_v.tail(5).iloc[::-1].iterrows():
                with st.container(border=True):
                    st.write(f"⏰ **{r['Data']} - {r['Hora']}**\n👤 {r['Cliente']}")
                    st.markdown(f"[📍 Abrir no Maps]({calc_maps(r['Endereco'])})")

elif aba == "👥 Clientes":
    st.title("👥 Meus Clientes")
    cols_c = ["Nome", "Documento", "WhatsApp", "Endereco", "Data"]
    df_c = carregar_aba_sheets("clientes", cols_c)
    
    st.write("### Lista de Clientes Registrados")
    if not df_c.empty:
        df_c.columns = df_c.columns.str.strip().str.lower()
        c_nome = 'nome' if 'nome' in df_c.columns else df_c.columns[0]
        c_end = 'endereco' if 'endereco' in df_c.columns else df_c.columns[0]
        c_whats = 'whatsapp' if 'whatsapp' in df_c.columns else df_c.columns[0]
        
        for i, r in df_c.iterrows():
            nome_orig = str(r[c_nome]).strip()
            if nome_orig:
                with st.expander(f"👤 {nome_orig}"):
                    st.write(f"📍 Endereço: {r[c_end]}")
                    st.write(f"📞 WhatsApp: {r[c_whats]}")
                    
                    if st.checkbox("✏️ Editar", key=f"edit_{i}"):
                        with st.form(f"f_{i}", clear_on_submit=False):
                            n_n = st.text_input("Nome", value=r[c_nome])
                            n_w = st.text_input("WhatsApp", value=r[c_whats])
                            n_e = st.text_input("Endereço", value=r[c_end])
                            
                            if st.form_submit_button("💾 Salvar"):
                                st.success("Pronto!")
                                r[c_nome], r[c_whats], r[c_end] = n_n, n_w, n_e
                                time.sleep(0.5)
                                st.rerun()
    else:
        st.info("Buscando clientes...")

elif aba == "🛠️ Agenda":
    st.title("🛠️ Agenda Técnica")
    cols_v = ["ID_V", "Cliente", "Data", "Hora", "Endereco"]
    df_v = carregar_aba_sheets("visitas", cols_v)
    
    if not df_v.empty and "Cliente" in df_v.columns:
        for i, r in df_v.iloc[::-1].iterrows():
            if str(r['Cliente']).strip():
                with st.container(border=True):
                    st.write(f"📅 **{r['Data']} às {r['Hora']}** — {r['Cliente']}")
                    st.markdown(f"[📍 Maps]({calc_maps(r['Endereco'])})")

elif aba == "💰 Novo Orçamento":
    st.title("💰 Criar Orçamento")
    df_cl = carregar_aba_sheets("clientes", ["Nome"])
    if not df_cl.empty and "Nome" in df_cl.columns:
        id_f = get_next_id()
        st.subheader(f"📄 Orçamento Nº: {id_f}")
        esc = st.selectbox("Cliente", [""] + list(df_cl["Nome"]))
        txt_ap = st.text_area("Escopo do Serviço")
        
        df_b = pd.DataFrame([{"Serviço": "", "Qtd": 1, "Valor Unit. (R$)": 0.0}])
        it = st.data_editor(df_b, num_rows="dynamic", use_container_width=True)
        v_u = pd.to_numeric(it["Valor Unit. (R$)"], errors='coerce').fillna(0)
        q_t = pd.to_numeric(it["Qtd"], errors='coerce').fillna(0)
        tot = (v_u * q_t).sum()
        st.write(f"### Total: R$ {tot:.2f}")
        
        if st.button("🚀 Gerar PDF"):
            if esc:
                hoje = datetime.now().strftime('%d/%m/%Y')
                st.session_state.pdf_gerado = out_pdf(id_f, hoje, esc, "", txt_ap, it, tot)
                st.rerun()
    else:
        st.warning("Adicione dados na planilha primeiro.")

    if st.session_state.pdf_gerado and os.path.exists(st.session_state.pdf_gerado):
        with open(st.session_state.pdf_gerado, "rb") as f:
            st.download_button("📩 Baixar PDF", f, file_name=st.session_state.pdf_gerado)

elif aba == "📊 Histórico":
    st.title("📊 Histórico")
    cols_h = ["ID", "Data", "Cliente", "Total", "Status"]
    df_h = carregar_aba_sheets("orcamentos", cols_h)
    if not df_h.empty and "Cliente" in df_h.columns:
        for i, r in df_h.iloc[::-1].iterrows():
            if str(r['Cliente']).strip():
                with st.container(border=True):
                    st.write(f"**Nº {r['ID']} — {r['Cliente']}**\n\nInvestimento: R$ {r['Total']} | Status: {r['Status']}")
