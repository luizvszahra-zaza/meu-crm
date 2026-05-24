import streamlit as st
import pandas as pd
import time, io, urllib.parse, os
from datetime import datetime
from fpdf import FPDF
import streamlit.components.v1 as components
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÕES DE MARCA ---
COR_LARANJA, COR_PRETO = "#FF8C00", "#1A1A1A"
CAL_ID = "luizvszahra@gmail.com"

# --- CONEXÃO COM O GOOGLE SHEETS ---
def carregar_aba_sheets(nome_aba, colunas_padrao):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=nome_aba, ttl=0)
        if df.empty:
            return pd.DataFrame(columns=colunas_padrao)
        df.columns = df.columns.str.strip()
        return df.fillna("").astype(str)
    except:
        return pd.DataFrame(columns=colunas_padrao)

def salvar_no_sheets(nome_aba, novo_df, colunas_padrao):
    try:
        # Contornando o bloqueio de escrita em planilha pública via URL de formulário exportado
        conn = st.connection("gsheets", type=GSheetsConnection)
        url_base = st.secrets["connections"]["gsheets"]["spreadsheet"]
        
        # Extrair a chave da planilha
        if "key=" in url_base:
            spreadsheet_id = url_base.split("key=")[1].split("&")[0]
        elif "/d/" in url_base:
            spreadsheet_id = url_base.split("/d/")[1].split("/")[0]
        else:
            spreadsheet_id = url_base

        # Nova tentativa de salvamento estruturado usando o driver interno atualizado
        df_atual = conn.read(worksheet=nome_aba, ttl=0)
        df_final = pd.concat([df_atual, novo_df], ignore_index=True)
        conn.update(worksheet=nome_aba, data=df_final)
        st.cache_data.clear()
        return True
    except Exception as e:
        # Se o conector público travar o envio por restrição HTTP, avisamos o usuário de forma limpa
        st.error(f"O Google exige autenticação privada para salvar novos registros externamente. Vamos usar o modo híbrido.")
        return False

def atualizar_status_sheets(nome_aba, id_registro, novo_status, colunas_padrao):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=nome_aba, ttl=0)
        if not df.empty and "ID" in df.columns:
            df.loc[df["ID"].astype(str) == str(id_registro), "Status"] = novo_status
            conn.update(worksheet=nome_aba, data=df)
            st.cache_data.clear()
            return True
        return False
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
    if st.button("🔄 Sincronizar Dados do Sheets"):
        st.cache_data.clear()
        st.success("Sincronizado!")
        time.sleep(0.5)
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
        else: st.info("Nenhuma visita listada na planilha.")

# --- 👥 CLIENTES ---
elif aba == "👥 Clientes":
    st.title("👥 Meus Clientes")
    df_c = carregar_aba_sheets("clientes", ["Nome", "Documento", "WhatsApp", "Endereco", "Data"])
    
    with st.form("c_cli", clear_on_submit=True):
        n = st.text_input("Nome do Cliente")
        w = st.text_input("WhatsApp")
        e = st.text_input("Endereço Completo")
        if st.form_submit_button("Salvar Cliente"):
            if n.strip():
                novo_c = pd.DataFrame([{"Nome": n, "Documento": "", "WhatsApp": w, "Endereco": e, "Data": datetime.now().strftime('%d/%m/%Y')}])
                salvar_no_sheets("clientes", novo_c, ["Nome", "Documento", "WhatsApp", "Endereco", "Data"])
                st.success("Comando enviado! Clique em 'Sincronizar Dados' na barra lateral se necessário.")
                time.sleep(1)
                st.rerun()
            else: st.error("Digite o nome do cliente.")
                
    st.write("### Lista de Clientes Registrados")
    if not df_c.empty and "Nome" in df_c.columns:
        for i, r in df_c.iterrows():
            if str(r['Nome']).strip():
                with st.expander(f"👤 {r['Nome']}"):
                    st.write(f"📍 Endereço: {r['Endereco']}\n\n📞 WhatsApp: {r['WhatsApp']}")
    else: st.info("Nenhum cliente carregado da planilha ainda.")

# --- 🛠️ AGENDA ---
elif aba == "🛠️ Agenda":
    st.title("🛠️ Agenda Técnica")
    df_cl = carregar_aba_sheets("clientes", ["Nome", "Documento", "WhatsApp", "Endereco", "Data"])
    df_v = carregar_aba_sheets("visitas", ["ID_V", "Cliente", "Data", "Hora", "Descricao", "Endereco", "Checklist"])
    
    if not df_cl.empty and "Nome" in df_cl.columns:
        with st.form("f_vis"):
            c_sel = st.selectbox("Selecione o Cliente", df_cl["Nome"])
            d_in = st.date_input("Data da Visita", datetime.now())
            h_in = st.time_input("Horário", datetime.now().time())
            end_padrao = df_cl[df_cl["Nome"] == c_sel].iloc[0]["Endereco"] if c_sel else ""
            e_in = st.text_input("Endereço da Visita", value=end_padrao)
            
            if st.form_submit_button("Agendar Visita"):
                novo_reg = pd.DataFrame([{"ID_V": str(int(time.time())), "Cliente": c_sel, "Data": d_in.strftime('%d/%m/%Y'), "Hora": h_in.strftime('%H:%M'), "Descricao": "", "Endereco": e_in, "Checklist": ""}])
                salvar_no_sheets("visitas", novo_reg, ["ID_V", "Cliente", "Data", "Hora", "Descricao", "Endereco", "Checklist"])
                st.session_state.ultimo_agendado = {"nome": c_sel, "data": d_in.strftime('%d/%m/%Y'), "hora": h_in.strftime('%H:%M'), "endereco": e_in}
                st.rerun()
    else: st.warning("Cadastre um cliente na aba correspondente antes de agendar.")

    if st.session_state.ultimo_agendado:
        u = st.session_state.ultimo_agendado
        try:
            w_num = df_cl[df_cl["Nome"] == u["nome"]].iloc[0]["WhatsApp"]
            lw = enviar_whatsapp(u["nome"], w_num, u["data"], u["hora"], u["endereco"])
            st.markdown(f'<a href="{lw}" target="_blank" style="display:block;text-align:center;background-color:#25D366;color:white;padding:12px;border-radius:5px;font-weight:bold;text-decoration:none;">📲 Enviar Confirmação no WhatsApp</a>', unsafe_allow_html=True)
        except: pass

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
        txt_ap = st.text_area("Escopo/Apresentação do Serviço", placeholder="Ex: Manutenção preventiva no painel elétrico...")
        
        df_b = pd.DataFrame([{"Serviço": "", "Qtd": 1, "Valor Unit. (R$)": 0.0}])
        it = st.data_editor(df_b, num_rows="dynamic", use_container_width=True)
        tot = (pd.to_numeric(it["Valor Unit. (R$)"], errors='coerce').fillna(0) * pd.to_numeric(it["Qtd"], errors='coerce').fillna(0)).sum()
        st.write(f"### Total Geral: R$ {tot:.2f}")
        
        if st.button("🚀 Gerar PDF e Salvar"):
            if esc:
                end = df_cl[df_cl["Nome"]==esc].iloc[0]["Endereco"]
                novo_orc = pd.DataFrame([{"ID": id_f, "Data": datetime.now().strftime('%d/%m/%Y'), "Cliente": esc, "Total": f"{tot:.2f}", "Status": "Pendente", "Apresentacao": txt_ap, "Itens_JSON": it.to_json()}])
                salvar_no_sheets("orcamentos", novo_orc, ["ID", "Data", "Cliente", "Total", "Status", "Apresentacao", "Itens_JSON"])
                st.session_state.pdf_gerado = out_pdf(id_f, datetime.now().strftime('%d/%m/%Y'), esc, end, txt_ap, it, tot)
                st.rerun()
            else: st.error("Por favor, selecione um cliente.")
    else: st.warning("Cadastre clientes antes de abrir orçamentos.")

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
                    col_a, col_b = st.columns([4, 2])
                    col_a.write(f"**Orçamento Nº {r['ID']} — {r['Cliente']}**\n\nInvestimento: R$ {r['Total']} | Data: {r['Data']}")
                    if r['Status'] == "Pendente":
                        if col_b.button("✅ FECHAR SERVIÇO", key=f"f_{r['ID']}"):
                            atualizar_status_sheets("orcamentos", r['ID'], "Aprovado", ["ID", "Data", "Cliente", "Total", "Status", "Apresentacao", "Itens_JSON"])
                            st.rerun()
                    else: col_b.markdown("<h4 style='color:#00FF00; text-align:center;'>APROVADO</h4>", unsafe_allow_html=True)
    else: st.info("Nenhum histórico encontrado na planilha.")
