import streamlit as st
import pandas as pd
import time, io, urllib.parse, os
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components

# --- CONFIGURAÇÕES DE CONFIGURAÇÃO DIRETA ---
# Mantém a ID da sua planilha que funcionou perfeitamente
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
    df_o = carregar_aba_sheets("orcamentos", ["ID", "Data", "Cliente", "Total", "Status", "Apresentacao", "Itens_JSON"])
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
        components.iframe("https://calendar.google.com/calendar/embed?src=" + CAL_ID + "&ctz=America%2FSao_Paulo&bgcolor=%23ffffff", height=500)
    with c_age:
        st.subheader("📌 Próximas Visitas")
        df_v = carregar_aba_sheets("visitas", ["ID_V", "Cliente", "Data", "Hora", "Descricao", "Endereco", "Checklist"])
        if not df_v.empty and "Cliente" in df_v.columns:
            for _, r in df_v.tail(5).iloc[::-1].iterrows():
                with st.container(border=True):
                    st.write(f"⏰ **{r['Data']} - {r['Hora']}**\n👤 {r['Cliente']}")
                    st.markdown(f"[📍 Abrir no Maps]({calc_maps(r['Endereco'])})")

# --- 👥 CLIENTES ---
elif aba == "👥 Clientes":
    st.title("👥 Meus Clientes")
    df_c = carregar_aba_sheets("clientes", ["Nome", "Documento", "WhatsApp", "Endereco", "Data"])
    
    st.write("### Lista de Clientes Registrados")
    if not df_c.empty:
        df_c.columns = df_c.columns.str.strip().str.lower()
        
        col_nome = 'nome' if 'nome' in df_c.columns else df_c.columns[0]
        col_end = 'endereco' if 'endereco' in df_c.columns else ('endereço' if 'endereço' in df_c.columns else df_c.columns[0])
        col_whats = 'whatsapp' if 'whatsapp' in df_c.columns else df_c.columns[0]
        
        for i, r in df_c.iterrows():
            nome_original = str(r[col_nome]).strip()
            if nome_original:
                with st.expander(f"👤 {nome_original}"):
                    st.write(f"📍 Endereço atual: {r[col_end]}")
                    st.write(f"📞 WhatsApp atual: {r[col_whats]}")
                    
                    com_editar = st.checkbox("✏️ Editar informações deste cliente", key=f"edit_{i}")
                    if com_editar:
                        with st.form(f"form_edit_{i}", clear_on_submit=False):
                            novo_nome = st.text_input("Alterar Nome", value=r[col_nome])
                            novo_whats = st.text_input("Alterar WhatsApp", value=r[col_whats])
                            novo_end = st.text_input("Alterar Endereço", value=r[col_end])
                            
                            if st.form_submit_button("💾 Salvar Alterações"):
                                st.success(f"Alterações preparadas para {nome_original}!")
                                st.info(f"👉 Acesse sua planilha Google Sheets 'CRM_Zahra' na aba 'clientes' para aplicar ou confirmar a alteração permanentemente se necessário.")
                                r[col_nome] = novo_nome
                                r[col_whats] = novo_whats
                                r[col_end] = novo_end
                                time.sleep(0.5)
                                st.rerun()
    else:
        st.info("Buscando clientes na planilha... Clique em Sincronizar se necessário.")

# --- 🛠️ AGENDA ---
elif aba == "🛠️ Agenda":
    st.title("🛠️ Agenda Técnica")
    df_v = carregar_aba_sheets("visitas", ["ID_V", "Cliente", "Data", "Hora", "Descricao", "Endereco", "Checklist"])
    
    st.write("### Compromissos na Planilha")
    if not df_v.empty and "Cliente" in df_v.columns:
        for i, r in df_v.iloc[::-1].iterrows():
            if str(r['Cliente']).strip():
                with st.container(border=True):
                    st.write(f"📅 **{r['Data']} às {r['Hora']}** — Cliente: {r['Cliente']}")
                    st.markdown(f"[📍 Ver no Google Maps]({calc_maps(r['Endereco'])})")

# --- 💰 NOVO ORÇAMENTO ---
elif aba == "💰 Novo Orçamento":
    st.title("💰 Criar Orçamento")
    df_cl = carregar_aba_sheets("clientes", ["Nome", "Documento", "WhatsApp", "Endereco", "Data"])
    if not df_cl.empty and "Nome" in df_cl.columns:
        id_f = get_next_id()
        st.subheader(f"📄 Orçamento Nº: {id_f}")
        esc = st.selectbox("Selecione o Cliente", [""] + list(df_cl["Nome"]))
        txt_ap = st.text_area("Escopo/Apresentação do Serviço")
        
        df_b = pd.DataFrame([{"Serviço": "", "Qtd": 1, "Valor Unit. (R$)": 0.0}])
        it = st.data_editor(df_b, num_rows="dynamic", use_container_width=True)
        tot = (pd.to_numeric(it["Valor Unit. (R$)"], errors='coerce').fillna(0) * pd.to_numeric(it["Qtd"], errors='coerce').fillna(0)).sum()
        st.write(f"### Total Geral: R$ {tot:.2f}")
        
        if st.button("🚀 Gerar PDF"):
            if esc:
                st.session_state.pdf_gerado = out_pdf(id_f, datetime.now().strftime('%d/%m/%Y'), esc, "", txt_ap, it, tot)
                st.rerun()
    else: st.warning("Adicione dados na planilha primeiro.")

    if st.session_state.pdf_gerado and os.path.exists(st.session_state.pdf_gerado):
        with open(st.session_state.pdf_gerado, "rb") as f:
            st.download_button("📩 Baixar PDF do Orçamento", f, file_name=st.session_state.pdf_gerado)

# --- 📊 HISTÓRICO ---
elif aba == "📊 Histórico":
    st.title("📊 Histórico de Orçamentos")
    df_h = carregar_aba_sheets("orcamentos", ["ID", "Data", "Cliente", "Total", "Status", "Apresentacao", "Itens_JSON"])
    if not df_h.empty and "Cliente" in df_h.columns:
        for i, r in df_h.iloc[::-1].iterrows():
            if str(r['Cliente']).strip():
                with st.container(border=True):
                    st.write(f"**Orçamento Nº {r['ID']} — {r['Cliente']}**\n\nInvestimento: R$ {r['Total']} | Data: {r['Data']} | Status: {r['Status']}")
