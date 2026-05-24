import streamlit as st
import pandas as pd
import time
import urllib.parse
import os
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# --- CONFIGURAÇÕES DO SISTEMA ---
# IMPORTANTE: Coloque o ID de letras e números da sua planilha real aqui
SPREADSHEET_ID = "1Z3AKmim2N-zfPCagSyGmY-kwPdy0fCwFYt81uMUsaxE"

COR_LARANJA = "#FF8C00"
COR_PRETO = "#1A1A1A"
CAL_ID = "luizvszahra@gmail.com"

# --- ENGINE DE CONEXÃO COM O GOOGLE SHEETS ---
def carregar_aba_sheets(nome_aba):
    try:
        aba_cod = urllib.parse.quote(nome_aba.strip())
        url = (
            f"https://docs.google.com/spreadsheets/d/"
            f"{SPREADSHEET_ID}/gviz/tq?tqx=out:csv"
            f"&sheet={aba_cod}"
        )
        df = pd.read_csv(url)
        if df.empty:
            return pd.DataFrame()
        df.columns = df.columns.str.strip()
        return df.fillna("").astype(str)
    except Exception as e:
        st.sidebar.error(f"Erro na aba '{nome_aba}'")
        return pd.DataFrame()

def get_next_id():
    df = carregar_aba_sheets("orcamentos")
    if df.empty:
        return "1000"
    id_col = next((c for c in df.columns if c.lower() == 'id'), None)
    if not id_col:
        return "1000"
    try:
        ids = pd.to_numeric(df[id_col], errors='coerce').dropna()
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

def out_pdf(idx, dt, cli, ender, apr, items, tot):
    try:
        pdf = PDF_Zahra()
        pdf.add_page()
        pdf.set_y(40)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(100, 5, "CNPJ: 50.779.713/0001-73")
        pdf.cell(90, 5, "Contato: (41) 99610-2100", ln=True)
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
            pdf.cell(190, 6, "SERVICO:", ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(190, 5, str(apr))
        
        pdf.ln(5)
        pdf.set_fill_color(255, 140, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(100, 10, " SERVICO", fill=True)
        pdf.cell(45, 10, " QTD / UNIT", fill=True)
        pdf.cell(45, 10, " TOTAL", fill=True, ln=True)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", "", 10)
        for _, r in items.iterrows():
            if str(r['Serviço']).strip():
                vu = float(r['Valor Unit. (R$)'])
                qt = float(r['Qtd'])
                pdf.cell(100, 8, f" {str(r['Serviço'])}", border=1)
                pdf.cell(45, 8, f"{int(qt)} x {vu:.2f}", border=1)
                pdf.cell(45, 8, f"R$ {vu*qt:.2f}", border=1, ln=True)
                
        pdf.ln(4)
        pdf.set_fill_color(255, 140, 0)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(145, 10, "TOTAL: ", fill=True)
        pdf.cell(45, 10, f"R$ {float(tot):.2f}", fill=True, ln=True)
        
        pdf.ln(20)
        y_v = pdf.get_y()
        pdf.line(20, y_v, 90, y_v)
        pdf.set_y(y_v + 2)
        pdf.set_x(20)
        pdf.cell(70, 5, "TECNICO ZAHRA")
        
        n_f = f"orcamento_{idx}.pdf"
        pdf.output(n_f)
        return n_f
    except Exception as err:
        st.error(f"Erro PDF: {err}")
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
    df_o = carregar_aba_sheets("orcamentos")
    fat = pend = 0
    
    if not df_o.empty:
        status_col = next((c for c in df_o.columns if c.lower() == 'status'), None)
        total_col = next((c for c in df_o.columns if c.lower() == 'total'), None)
        
        if total_col and status_col:
            df_o[total_col] = pd.to_numeric(df_o[total_col], errors='coerce').fillna(0)
            fat = df_o[df_o[status_col].str.lower() == "aprovado"][total_col].sum()
            pend = df_o[df_o[status_col].str.lower() == "pendente"][total_col].sum()
    
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
        df_v = carregar_aba_sheets("visitas")
        
        if not df_v.empty:
            cli_col = next((c for c in df_v.columns if c.lower() == 'cliente'), None)
            end_col = next((c for c in df_v.columns if c.lower() in ['endereco', 'endereço']), None)
            data_col = next((c for c in df_v.columns if c.lower() == 'data'), None)
            hora_col = next((c for c in df_v.columns if c.lower() == 'hora'), None)
            
            if cli_col:
                for _, r in df_v.tail(5).iloc[::-1].iterrows():
                    with st.container(border=True):
                        d_txt = r.get(data_col, '') if data_col else ''
                        h_txt = r.get(hora_col, '') if hora_col else ''
                        st.write(f"⏰ **{d_txt} - {h_txt}**\n👤 {r[cli_col]}")
                        if end_col:
                            st.markdown(f"[📍 Abrir no Maps]({calc_maps(r[end_col])})")

elif aba == "👥 Clientes":
    st.title("👥 Meus Clientes")
    df_c = carregar_aba_sheets("clientes")
    
    st.write("### Lista de Clientes Registrados")
    if not df_c.empty:
        c_nome = next((c for c in df_c.columns if c.lower() == 'nome'), df_c.columns[0])
        c_end = next((c for c in df_c.columns if c.lower() in ['endereco', 'endereço']), None)
        c_whats = next((c for c in df_c.columns if c.lower() in ['whatsapp', 'whats']), None)
        
        c_end = c_end if c_end else (df_c.columns[3] if len(df_c.columns) > 3 else df_c.columns[0])
        c_whats = c_whats if c_whats else (df_c.columns[2] if len(df_c.columns) > 2 else df_c.columns[0])
        
        for i, r in df_c.iterrows():
            nome_orig = str(r[c_nome]).strip()
            if nome_orig:
                with st.expander(f"👤 {nome_orig}"):
                    st.write(f"📍 Endereço: {r.get(c_end, 'Não informado')}")
                    st.write(f"📞 WhatsApp: {r.get(c_whats, 'Não informado')}")
                    
                    if st.checkbox("✏️ Editar", key=f"edit_{i}"):
                        with st.form(f"f_{i}", clear_on_submit=False):
                            n_n = st.text_input("Nome", value=r[c_nome])
                            n_w = st.text_input("WhatsApp", value=r.get(c_whats, ""))
                            n_e = st.text_input("Endereço", value=r.get(c_end, ""))
                            
                            if st.form_submit_button("💾 Salvar"):
                                st.success("Pronto!")
                                r[c_nome] = n_n
                                if c_whats in r: r[c_whats] = n_w
                                if c_end in r: r[c_end] = n_e
                                time.sleep(0.5)
                                st.rerun()
    else:
        st.info("Nenhum cliente listado. Verifique os dados ou clique em 'Sincronizar'.")

elif aba == "🛠️ Agenda":
    st.title("🛠️ Agenda Técnica")
    df_v = carregar_aba_sheets("visitas")
    
    if not df_v.empty:
        cli_col = next((c for c in df_v.columns if c.lower() == 'cliente'), None)
        end_col = next((c for c in df_v.columns if c.lower() in ['endereco', 'endereço']), None)
        data_col = next((c for c in df_v.columns if c.lower() == 'data'), None)
        hora_col = next((c for c in df_v.columns if c.lower() == 'hora'), None)
        
        if cli_col:
            for i, r in df_v.iloc[::-1].iterrows():
                if str(r[cli_col]).strip():
                    with st.container(border=True):
                        d_txt = r.get(data_col, '') if data_col else ''
                        h_txt = r.get(hora_col, '') if hora_col else ''
                        st.write(f"📅 **{d_txt} às {h_txt}** — {r[cli_col]}")
                        if end_col:
                            st.markdown(f"[📍 Maps]({calc_maps(r[end_col])})")
    else:
        st.info("Nenhum compromisso agendado na planilha.")

elif aba == "💰 Novo Orçamento":
    st.title("💰 Criar Orçamento")
    df_cl = carregar_aba_sheets("clientes")
    
    if not df_cl.empty:
        nome_col = next((c for c in df_cl.columns if c.lower() == 'nome'), df_cl.columns[0])
        id_f = get_next_id()
        st.subheader(f"📄 Orçamento Nº: {id_f}")
        lista_clientes = [n for n in df_cl[nome_col].unique() if str(n).strip()]
        esc = st.selectbox("Cliente", [""] + lista_clientes)
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
        st.warning("Adicione dados na aba 'clientes' da planilha primeiro.")

    if st.session_state.pdf_gerado and os.path.exists(st.session_state.pdf_gerado):
        with open(st.session_state.pdf_gerado, "rb") as f:
            st.download_button("📩 Baixar PDF", f, file_name=st.session_state.pdf_gerado)

elif aba == "📊 Histórico":
    st.title("📊 Histórico")
    df_h = carregar_aba_sheets("orcamentos")
    
    if not df_h.empty:
        cli_col = next((c for c in df_h.columns if c.lower() == 'cliente'), None)
        id_col = next((c for c in df_h.columns if c.lower() == 'id'), None)
        tot_col = next((c for c in df_h.columns if c.lower() == 'total'), None)
        st_col = next((c for c in df_h.columns if c.lower() == 'status'), None)
        
        if cli_col:
            for i, r in df_h.iloc[::-1].iterrows():
                if str(r[cli_col]).strip():
                    with st.container(border=True):
                        i_txt = r.get(id_col, '') if id_col else ''
                        t_txt = r.get(tot_col, '0.00') if tot_col else '0.00'
                        s_txt = r.get(st_col, 'Pendente') if st_col else 'Pendente'
                        st.write(f"**Nº {i_txt} — {r[cli_col]}**\n\nInvestimento: R$ {t_txt} | Status: {s_txt}")
    else:
        st.info("Nenhum histórico encontrado.")
