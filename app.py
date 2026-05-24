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

# --- CONEXÃO COM O GOOGLE SHEETS (COM LIMPEZA DE CACHE REMOVIDO/FORÇADO) ---
def carregar_aba_sheets(nome_aba, colunas_padrao):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Usamos st.cache_data.clear() no botão para forçar o reset, ttl=0 garante leitura direta
        df = conn.read(worksheet=nome_aba, ttl=0)
        if df.empty:
            return pd.DataFrame(columns=colunas_padrao)
        # Limpar espaços extras nos nomes das colunas para evitar erros de leitura
        df.columns = df.columns.str.strip()
        return df.fillna("").astype(str)
    except Exception as e:
        return pd.DataFrame(columns=colunas_padrao)

def salvar_no_sheets(nome_aba, novo_df, colunas_padrao):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        try:
            df_atual = conn.read(worksheet=nome_aba, ttl=0)
            df_atual.columns = df_atual.columns.str.strip()
        except:
            df_atual = pd.DataFrame(columns=colunas_padrao)
            
        df_final = pd.concat([df_atual, novo_df], ignore_index=True)
        conn.update(worksheet=nome_aba, data=df_final)
        st.cache_data.clear() # Limpa o cache após salvar
        return True
    except Exception as e:
        st.error("Erro ao salvar na nuvem: " + str(e))
        return False

def atualizar_status_sheets(nome_aba, id_registro, novo_status, colunas_padrao):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(worksheet=nome_aba, ttl=0)
        df.columns = df.columns.str.strip()
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
    m = "Olá " + str(nome) + ", aqui é o Luiz da Técnico Zahra! ⚡\n\n"
    m += "Estou passando para confirmar nossa visita técnica:\n"
    m += "Data: " + str(dt) + "\nHorário: " + str(hr) + "\nEndereço: " + str(ender)
    num = "".join(c for c in str(tel) if c.isdigit())
    if not num.startswith("55"): num = "55" + num
    return "https://api.whatsapp.com/send?phone=" + num + "&text=" + urllib.parse.quote(m)

def calc_maps(ender):
    if not ender: return "#"
    q = urllib.parse.quote(str(ender))
    return "https://www.google.com/maps/search/?api=1&query=" + q

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
        t_cab = "  ORCAMENTO N " + str(idx) + " | DATA: " + str(dt)
        pdf.cell(190, 10, t_cab, ln=True, fill=True)
        pdf.ln(3)
        
        pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "B", 10)
        c_dec = str(cli).upper().encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(190, 7, "CLIENTE: " + c_dec, ln=True)
        
        pdf.set_font("Arial", "", 10)
        e_dec = str(ender).upper().encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(190, 6, "ENDERECO: " + e_dec)
        
        if apr.strip():
            pdf.ln(4); pdf.set_font("Arial", "B", 10)
            pdf.cell(190, 6, "APRESENTACAO DO SERVICO:", ln=True)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(190, 5, apr.encode('latin-1', 'replace').decode('latin-1'))
        
        pdf.ln(5); pdf.set_fill_color(255, 140, 0); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 10)
        pdf.cell(100, 10, " SERVICO", fill=True)
        pdf.cell(45, 10, " QTD / UNIT", fill=True, align="C")
        pdf.cell(45, 10, " TOTAL", fill=True, align="C")
        pdf.ln()
        
        pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "", 10)
        for _, r in items.iterrows():
            if str(r['Serviço']).strip():
                vu, qt = float(r['Valor Unit. (R$)']), float(r['Qtd'])
                s_tk = str(r['Serviço']).encode('latin-1', 'replace').decode('latin-1')
                pdf.cell(100, 8, " " + s_tk, border=1)
                t_qtd = str(int(qt)) + " x R$ " + "{:.2f}".format(vu)
                pdf.cell(45, 8, t_qtd, border=1, align="C")
                t_sub = "R$ " + "{:.2f}".format(vu * qt)
                pdf.cell(45, 8, t_sub, border=1, align="R")
                pdf.ln()
                
        pdf.ln(4); pdf.set_fill_color(255, 140, 0); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", "B", 10)
        pdf.cell(145, 10, "TOTAL DO INVESTIMENTO: ", align="R", fill=True)
        t_final = "R$ " + "{:.2f}".format(float(tot))
        pdf.cell(45, 10, t_final, align="R", fill=True, ln=True)
        
        pdf.ln(5); pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", "B", 10)
        pdf.cell(190, 7, "FORMAS DE PAGAMENTO:", ln=True)
        pdf.set_font("Arial", "", 10)
        p_txt = "- Pix, Dinheiro ou Cartao de Debito.\n- Credito: Juros por conta do cliente."
        pdf.multi_cell(190, 5, p_txt)
        
        pdf.ln(20); y_v = pdf.get_y(); pdf.line(20, y_v, 90, y_v)
        pdf.set_y(y_v + 2); pdf.set_x(20); pdf.set_font("Arial", "B", 9); pdf.cell(70, 5, "TECNICO ZAHRA", align="C")
        pdf.line(120, y_v, 190, y_v); pdf.set_y(y_v + 2); pdf.set_x(120)
        cl_b = str(cli).upper().encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(70, 5, cl_b, align="C")
        
        n_f = "orcamento_" + str(idx) + ".pdf"; pdf.output(n_f); return n_f
    except Exception as err:
        st.error("Erro PDF: " + str(err)); return None

# --- CONFIGURAÇÃO INTERFACE ---
st.set_page_config(page_title="Técnico Zahra CRM", layout="wide", page_icon="⚡")

st.markdown(f"""
<style>
    .metric-card {{ background-color: {COR_PRETO}; padding: 20px; border-radius: 10px; border-top: 4px solid {COR_LARANJA}; text-align: center; }}
    .stButton>button {{ width: 100%; }}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚡ Técnico Zahra")
    
    # BOTÃO MANUAL DE LIMPEZA DE CACHE
    if st.button("🔄 Atualizar Banco de Dados"):
        st.cache_data.clear()
        st.success("Dados sincronizados!")
        time.sleep(0.5)
        st.rerun()
        
    st.divider()
    aba = st.radio(
        "Navegação", 
        ["🏠 Painel Principal", "👥 Clientes", "🛠️ Agenda", "💰 Novo Orçamento", "📊 Histórico"],
        key="aba_atual"
    )

# --- 🏠 PAINEL ---
if aba == "🏠 Painel Principal":
    st.title("🚀 Dashboard Técnico Zahra")
    df_o = carregar_aba_sheets("orcamentos", ["ID", "Data", "Cliente", "Total", "Status", "Apresentacao", "Itens_JSON"])
    fat = pend = 0
    if not df_o.empty and "Total" in df_o.columns:
        df_o["Total"] = pd.to_numeric(df_o["Total"], errors='coerce').fillna(0)
        fat = df_o[df_o["Status"] == "Aprovado"]["Total"].sum()
        pend = df_o[df_o["Status"] == "Pendente"]["Total"].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        m_fat = '<div class="metric-card"><h3 style="color:#00FF00">R$ ' + "{:.2f}".format(fat) + '</h3><p>FATURADO</p></div>'
        st.markdown(m_fat, unsafe_allow_html=True)
    with col2:
        m_pend = '<div class="metric-card"><h3 style="color:#FFA500">R$ ' + "{:.2f}".format(pend) + '</h3><p>PENDENTE</p></div>'
        st.markdown(m_pend, unsafe_allow_html=True)
    with col3:
        st.markdown('<p style="text-align:center;font-weight:bold;margin-bottom:5px;">Estratégia</p>', unsafe_allow_html=True)
        m_inst = '<div style="background-color:' + COR_LARANJA + ';color:white;padding:15px;border-radius:50px;text-align:center;font-weight:bold;">📸 Post: Técnico Zahra</div>'
        st.markdown(m_inst, unsafe_allow_html=True)

    st.divider()
    c_cal, c_age = st.columns([4, 2])
    with c_cal:
        st.subheader("📅 Seu Calendário Google")
        components.iframe("https://calendar.google.com/calendar/embed?src=" + CAL_ID + "&ctz=America%2FSao_Paulo&bgcolor=%23ffffff", height=550)
    with c_age:
        st.subheader("📌 Próximas Visitas")
        df_v = carregar_aba_sheets("visitas", ["ID_V", "Cliente", "Data", "Hora", "Descricao", "Endereco", "Checklist"])
        if not df_v.empty and "Cliente" in df_v.columns:
            for _, r in df_v.tail(5).iloc[::-1].iterrows():
                with st.container(border=True):
                    st.write("⏰ **" + str(r['Data']) + " - " + str(r['Hora']) + "**\n👤 " + str(r['Cliente']))
                    st.markdown("📍 [Abrir Maps](" + calc_maps(r['Endereco']) + ")")
        else:
            st.info("Nenhuma visita agendada na nuvem ainda.")

# --- 🛠️ AGENDA ---
elif aba == "🛠️ Agenda":
    st.title("🛠️ Agenda Técnica")
    df_cl = carregar_aba_sheets("clientes", ["Nome", "Documento", "WhatsApp", "Endereco", "Data"])
    v_ed = st.session_state.vis_edit
    
    if not df_cl.empty and "Nome" in df_cl.columns:
        with st.form("f_vis"):
            c_sel = st.selectbox("Cliente", df_cl["Nome"], index=list(df_cl["Nome"]).index(v_ed["Cliente"]) if v_ed else 0)
            d_in = st.date_input("Data", value=datetime.strptime(v_ed["Data"], '%d/%m/%Y') if v_ed else datetime.now())
            h_in = st.time_input("Hora", value=datetime.strptime(v_ed["Hora"], '%H:%M').time() if v_ed else datetime.now().time())
            e_in = st.text_input("Endereço", value=v_ed["Endereco"] if v_ed else df_cl[df_cl["Nome"] == c_sel].iloc[0]["Endereco"])
            if st.form_submit_button("Salvar na Agenda"):
                id_v = v_ed["ID_V"] if v_ed else str(int(time.time()))
                novo_reg = pd.DataFrame([{"ID_V": id_v, "Cliente": c_sel, "Data": d_in.strftime('%d/%m/%Y'), "Hora": h_in.strftime('%H:%M'), "Endereco": e_in}])
                if salvar_no_sheets("visitas", novo_reg, ["ID_V", "Cliente", "Data", "Hora", "Descricao", "Endereco", "Checklist"]):
                    st.session_state.ultimo_agendado = {"nome": c_sel, "data": d_in.strftime('%d/%m/%Y'), "hora": h_in.strftime('%H:%M'), "endereco": e_in}
                    st.session_state.vis_edit = None; st.success("Agendado na Nuvem!"); st.rerun()
    else:
        st.warning("Cadastre um cliente na aba 'Clientes' antes de usar a agenda.")

    if st.session_state.ultimo_agendado:
        u = st.session_state.ultimo_agendado
        try:
            row = df_cl[df_cl["Nome"] == u["nome"]].iloc[0]
            lw = enviar_whatsapp(u["nome"], row["WhatsApp"], u["data"], u["hora"], u["endereco"])
            tg = urllib.parse.quote("Técnico Zahra: " + str(u['nome']))
            dg = datetime.strptime(u['data'], '%d/%m/%Y').strftime('%Y%m%d')
            lg = "https://www.google.com/calendar/render?action=TEMPLATE&text=" + tg + "&dates=" + dg + "/" + dg
            
            col_w, col_g = st.columns(2)
            s_w = "display:block;text-align:center;background-color:#25D366;color:white;padding:12px;border-radius:5px;font-weight:bold;text-decoration:none;"
            s_g = "display:block;text-align:center;background-color:#4285F4;color:white;padding:12px;border-radius:5px;font-weight:bold;text-decoration:none;"
            
            col_w.markdown('<a href="' + lw + '" target="_blank" style="' + s_w + '">📲 Confirmar WhatsApp</a>', unsafe_allow_html=True)
            col_g.markdown('<a href="' + lg + '" target="_blank" style="' + s_g + '">📅 Gravar na Agenda</a>', unsafe_allow_html=True)
        except: pass

    st.divider()
    df_vl = carregar_aba_sheets("visitas", ["ID_V", "Cliente", "Data", "Hora", "Descricao", "Endereco", "Checklist"])
    if not df_vl.empty and "Cliente" in df_vl.columns:
        for i, r in df_vl.iloc[::-1].iterrows():
            with st.container(border=True):
                st.write("**" + str(r['Data']) + " - " + str(r['Hora']) + "** | " + str(r['Cliente']) + "\n📍 [Maps](" + calc_maps(r['Endereco']) + ")")

# --- 💰 NOVO ORÇAMENTO ---
elif aba == "💰 Novo Orçamento":
    st.title("💰 Criar Orçamento")
    df_cl = carregar_aba_sheets("clientes", ["Nome", "Documento", "WhatsApp", "Endereco", "Data"])
    e_dt = st.session_state.orc_edit
    if not df_cl.empty and "Nome" in df_cl.columns:
        id_f = e_dt["ID"] if e_dt else get_next_id()
        st.info("📄 Orçamento Nº: " + str(id_f))
        esc = st.selectbox("Cliente", [""] + list(df_cl["Nome"]), index=list(df_cl["Nome"]).index(e_dt['Cliente']) + 1 if e_dt else 0)
        
        ap_df = e_dt["Apresentacao"] if e_dt and "Apresentacao" in e_dt else ""
        txt_ap = st.text_area("Apresentação do Serviço (Escopo no PDF)", value=ap_df, placeholder="Ex: Execução de projeto elétrico...")
        
        df_b = e_dt['Itens'] if e_dt else pd.DataFrame([{"Serviço": "", "Qtd": 1, "Valor Unit. (R$)": 0.0}])
        it = st.data_editor(df_b, num_rows="dynamic", use_container_width=True)
        tot = (pd.to_numeric(it["Valor Unit. (R$)"], errors='coerce').fillna(0) * pd.to_numeric(it["Qtd"], errors='coerce').fillna(0)).sum()
        st.write("### Total: R$ " + "{:.2f}".format(tot))
        
        if st.button("🚀 Finalizar e Gerar PDF"):
            if esc:
                end = df_cl[df_cl["Nome"]==esc].iloc[0]["Endereco"]
                novo_orc = pd.DataFrame([{"ID": id_f, "Data": datetime.now().strftime('%d/%m/%Y'), "Cliente": esc, "Total": f"{tot:.2f}", "Status": "Pendente", "Apresentacao": txt_ap, "Itens_JSON": it.to_json()}])
                if salvar_no_sheets("orcamentos", novo_orc, ["ID", "Data", "Cliente", "Total", "Status", "Apresentacao", "Itens_JSON"]):
                    p_f = out_pdf(id_f, datetime.now().strftime('%d/%m/%Y'), esc, end, txt_ap, it, tot)
                    st.session_state.pdf_gerado = p_f
                    st.session_state.orc_edit = None; st.success("Salvo na Nuvem!"); st.rerun()
            else: st.error("Escolha um cliente!")
    else:
        st.warning("Cadastre um cliente na aba 'Clientes' antes de criar um orçamento.")

    if st.session_state.pdf_gerado:
        p_f = st.session_state.pdf_gerado
        if os.path.exists(p_f):
            with open(p_f, "rb") as f:
                st.download_button("📩 Baixar PDF do Orçamento", f, file_name=p_f)
            if st.button("🆕 Criar Outro Orçamento"):
                st.session_state.pdf_gerado = None; st.rerun()

# --- 📊 HISTÓRICO ---
elif aba == "📊 Histórico":
    st.title("📊 Gestão de Orçamentos")
    df_h = carregar_aba_sheets("orcamentos", ["ID", "Data", "Cliente", "Total", "Status", "Apresentacao", "Itens_JSON"])
    if not df_h.empty and "Cliente" in df_h.columns:
        for i, r in df_h.iloc[::-1].iterrows():
            with st.container(border=True):
                c_d, c_s = st.columns([4, 2])
                with c_d: st.write("**Nº " + str(r['ID']) + " | " + str(r['Cliente']) + "**\n💰 R$ " + str(r['Total']) + " | 📅 " + str(r['Data']))
                with c_s:
                    if r['Status'] == "Pendente":
                        if st.button("✅ FECHAR SERVIÇO", key="fat_" + str(r['ID'])):
                            if atualizar_status_sheets("orcamentos", r['ID'], "Aprovado", ["ID", "Data", "Cliente", "Total", "Status", "Apresentacao", "Itens_JSON"]):
                                st.success("Serviço Fechado!"); st.rerun()
                    else: st.markdown("<h4 style='color:#00FF00;text-align:center;'>APROVADO</h4>", unsafe_allow_html=True)
    else:
        st.info("Nenhum orçamento cadastrado na nuvem ainda.")

# --- 👥 CLIENTES ---
elif aba == "👥 Clientes":
    st.title("👥 Meus Clientes")
    st.write("DEBUG CLIENTES:", carregar_aba_sheets("clientes", ["Nome", "Documento", "WhatsApp", "Endereco", "Data"]))
    df_c = carregar_aba_sheets("clientes", ["Nome", "Documento", "WhatsApp", "Endereco", "Data"])
    with st.form("c_cli", clear_on_submit=True):
        n, w, e = st.text_input("Nome"), st.text_input("WhatsApp"), st.text_input("Endereço Padrão")
        if st.form_submit_button("Cadastrar"):
            novo_c = pd.DataFrame([{"Nome": n, "WhatsApp": w, "Endereco": e, "Data": datetime.now().strftime('%d/%m/%Y')}])
            if salvar_no_sheets("clientes", novo_c, ["Nome", "Documento", "WhatsApp", "Endereco", "Data"]):
                st.success("Cliente salvo!"); st.rerun()
                
    if not df_c.empty and "Nome" in df_c.columns:
        for i, r in df_c.iterrows():
            with st.expander("👤 " + str(r['Nome'])):
                st.write("📍 " + str(r['Endereco']) + " | 📞 " + str(r['WhatsApp']))
    else:
        st.info("Nenhum cliente cadastrado na nuvem ainda.")
