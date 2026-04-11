import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import openai
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Intelligence", layout="wide", initial_sidebar_state="expanded")

# --- CSS WHITELABEL REFORÇADO (Anti-Conflito) ---
st.markdown("""
    <style>
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stApp { background-color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    .stApp p, .stApp span, .stApp label { color: #1e293b !important; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-right: 1px solid #1e293b !important; min-width: 300px !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] h2 { color: #f1f5f9 !important; }
    h1, h2, h3 { color: #0f172a !important; font-weight: 800; letter-spacing: -0.04em !important; }
    .risk-card { padding: 22px; border-radius: 8px; text-align: center; color: white !important; font-weight: 600; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .insight-box { background-color: #ffffff !important; padding: 25px; border-left: 5px solid #3b82f6; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 25px; border: 1px solid #f1f5f9; }
    .stButton>button { background-color: #2563eb !important; color: white !important; border-radius: 6px; width: 100%; font-weight: 600; height: 48px; border: none; }
    .feedback-box { background-color: #fffbe6; padding: 20px; border-radius: 8px; border: 1px solid #ffe58f; margin-bottom: 20px; color: #856404 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE SEGURANÇA E DADOS ---
def safe_float(val, default=0.0):
    try: return float(val)
    except: return default

def safe_json(val):
    if val is None or val == "" or val == "None": return {}
    if isinstance(val, dict): return val
    try: return json.loads(val)
    except: return {}

@st.cache_data(ttl=3600)
def get_live_selic():
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        return float(requests.get(url, timeout=5).json()[0]['valor'])
    except: return 10.75

try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("Erro de conexão com o banco de dados. Verifique os Secrets.")
    st.stop()

def load_data(gid):
    try:
        res = supabase.table("eco_data").select("*").eq("group_id", gid).execute()
        if res.data:
            row = res.data[0]
            for col in ['porter', 'dre', 'wacc', 'swot', 'participants', 'company_info', 'diary']:
                row[col] = safe_json(row.get(col))
            return row
    except: pass
    return {'group_id': gid, 'porter': {}, 'dre': {}, 'wacc': {}, 'swot': {}, 'hhi': '0', 'diary': {}, 'participants': {}, 'company_info': {}, 'feedback': ''}

def save_data(gid, column, value):
    if isinstance(value, (dict, list)): value = json.dumps(value)
    supabase.table("eco_data").upsert({"group_id": gid, column: str(value)}).execute()

def gerar_correcao_ia(dados):
    if "OPENAI_API_KEY" not in st.secrets: return "Erro: Chave OpenAI ausente."
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    prompt = f"Analise como professor de economia: {dados}"
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return f"Erro na IA: {e}"

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_teacher' not in st.session_state: st.session_state.is_teacher = False

if not st.session_state.auth:
    st.markdown("<h2 style='text-align: center; color: #0f172a; padding-top: 50px;'>ECOSTRATEGY HUB</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.6, 1])
    with col_l2:
        try: st.image("logo.png", use_container_width=True)
        except: pass
        group_sel = st.selectbox("Selecione sua Unidade", ["Grupo 1", "Grupo 2", "Grupo 3"])
        pwd_input = st.text_input("Chave de Acesso", type="password")
        if st.button("Acessar Sistema"):
            passwords = st.secrets.get("GROUP_PASSWORDS", {})
            dev_pwd = st.secrets.get("DEV_PASSWORD")
            if pwd_input == passwords.get(group_sel) or pwd_input == dev_pwd:
                st.session_state.auth, st.session_state.group = True, group_sel
                st.session_state.is_teacher = (pwd_input == dev_pwd)
                st.rerun()
            else: st.error("Acesso Negado.")
    st.stop()

# CARREGA DADOS DO GRUPO LOGADO
data = load_data(st.session_state.group)

# --- SIDEBAR (Sempre visível após login) ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    st.markdown(f"<h2>{st.session_state.group.upper()}</h2>", unsafe_allow_html=True)
    st.divider()
    selic_meta = get_live_selic()
    selic_ref = st.number_input("Taxa Selic Referência (%)", value=selic_meta, step=0.25)
    
    opcoes_menu = [
        "01 DASHBOARD EXECUTIVO", "02 IDENTIFICAÇÃO", "03 PERFIL EMPRESA", 
        "04 DIÁRIO DE CAMPO", "05 ESTRATÉGIA", "06 MONETÁRIO", 
        "07 FINANCEIRO", "08 RELATÓRIO FINAL"
    ]
    if st.session_state.is_teacher:
        opcoes_menu.append("09 PORTAL DO ORIENTADOR")
    
    menu = st.radio("NAVEGAÇÃO", opcoes_menu)
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# --- 1. DASHBOARD EXECUTIVO ---
if menu == "01 DASHBOARD EXECUTIVO":
    st.title("Executive Management Dashboard")
    
    # FEEDBACK DO PROFESSOR
    fb = data.get('feedback', '')
    if fb:
        st.markdown(f'<div class="feedback-box"><b>📬 PARECER DO ORIENTADOR:</b><br>{fb}</div>', unsafe_allow_html=True)

    info = data.get('company_info', {})
    st.markdown(f'<div class="insight-box"><h4>Unidade: {st.session_state.group} | Cliente: {info.get("nome", "Pendente")}</h4></div>', unsafe_allow_html=True)
    
    # Cálculos para Gráficos
    dre_d = data.get('dre', {})
    ebitda = safe_float(dre_d.get('receita')) - safe_float(dre_d.get('custos'))
    divida = safe_float(dre_d.get('divida'))
    idx_total = safe_float(dre_d.get('idx_valor')) + safe_float(dre_d.get('spread'))
    break_even = (ebitda / divida * 100) if divida > 0 else 0
    hhi_str = str(data.get('hhi', '0'))
    try: hhi_val = sum([float(x)**2 for x in hhi_str.split(",") if x.strip()])
    except: hhi_val = 0
    w_d = data.get('wacc', {})
    roi = safe_float(w_d.get('roi'))
    w_final = safe_float(w_d.get('wacc_final', 15.0))
    
    # HEALTH SCORE GAUGE
    score = 0
    if divida == 0 or idx_total < (ebitda/divida*100 if divida > 0 else 100): score += 40
    if hhi_val < 2500: score += 30
    if roi > w_final: score += 30

    col_g, col_s = st.columns([1.5, 2])
    with col_g:
        fig_health = go.Figure(go.Indicator(
            mode = "gauge+number", value = score, title = {'text': "Financial Health Score"},
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#2563eb"},
                     'steps': [{'range': [0, 50], 'color': "#dc3545"}, {'range': [50, 75], 'color': "#ffc107"}, {'range': [75, 100], 'color': "#28a745"}]}))
        st.plotly_chart(fig_health, use_container_width=True)
    
    with col_s:
        c1, c2, c3 = st.columns(3)
        with c1:
            color = "#28a745" if selic_ref < break_even else "#dc3545" if break_even > 0 else "#6c757d"
            st.markdown(f'<div class="risk-card" style="background:{color}">CRÉDITO<br>{idx_total:.1f}%</div>', unsafe_allow_html=True)
        with c2:
            m_color = "#28a745" if hhi_val < 1500 else "#ffc107" if hhi_val < 2500 else "#dc3545"
            st.markdown(f'<div class="risk-card" style="background:{m_color}">MERCADO<br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
        with c3:
            v_color = "#28a745" if roi > w_final else "#dc3545"
            st.markdown(f'<div class="risk-card" style="background:{v_color}">VALOR<br>ROI: {roi}%</div>', unsafe_allow_html=True)

# --- 2. IDENTIFICAÇÃO ---
elif menu == "02 IDENTIFICAÇÃO":
    st.title("Equipe de Consultoria")
    part = data.get('participants', {})
    with st.form("f_eq"):
        al1 = st.text_input("Aluno 1", value=part.get('aluno1', ''))
        prof = st.text_input("Professor", value=part.get('professor', ''))
        if st.form_submit_button("Salvar"):
            save_data(st.session_state.group, "participants", {"aluno1":al1, "professor":prof})
            st.success("Salvo!")

# --- 3. PERFIL EMPRESA ---
elif menu == "03 PERFIL EMPRESA":
    st.title("Perfil do Cliente")
    info = data.get('company_info', {})
    with st.form("f_emp"):
        n = st.text_input("Nome Empresa", value=info.get('nome', ''))
        d = st.text_area("Descrição", value=info.get('desc', ''))
        if st.form_submit_button("Salvar Perfil"):
            save_data(st.session_state.group, "company_info", {"nome":n, "desc":d})
            st.success("Salvo!")

# --- 4. DIÁRIO DE CAMPO ---
elif menu == "04 DIÁRIO DE CAMPO":
    st.title("Diagnóstico de Campo")
    diary = data.get('diary', {})
    with st.form("f_dia"):
        q1 = st.text_area("Histórico", value=diary.get('q1', ''))
        if st.form_submit_button("Sincronizar"):
            save_data(st.session_state.group, "diary", {"q1":q1})
            st.success("Salvo!")

# --- 5. ESTRATÉGIA ---
elif menu == "05 ESTRATÉGIA":
    st.title("Microeconomia e Inteligência")
    t1, t2, t3 = st.tabs(["Porter", "HHI", "SWOT"])
    with t1:
        p = data.get('porter', {})
        p1 = st.slider("Novos Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        if st.button("Salvar Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1})
            st.success("Porter Salvo!")
    with t2:
        s1 = st.number_input("Share Líder %", value=30.0)
        if st.button("Salvar HHI"):
            save_data(st.session_state.group, "hhi", f"{s1}")
    with t3:
        sw = data.get('swot', {})
        f = st.text_area("Forças", value=sw.get('f', ''))
        if st.button("Salvar SWOT"):
            save_data(st.session_state.group, "swot", {"f":f})

# --- 6. MONETÁRIO ---
elif menu == "06 MONETÁRIO":
    st.title("Macroeconomia e Juros")
    dre_d = data.get('dre', {})
    rec = st.number_input("Receita", value=safe_float(dre_d.get('receita', 1000000)))
    if st.button("Salvar DRE"):
        save_data(st.session_state.group, "dre", {"receita":rec})

# --- 7. FINANCEIRO ---
elif menu == "07 FINANCEIRO":
    st.title("Viabilidade e Custo de Capital")
    w_d = data.get('wacc', {})
    ke = st.number_input("Ke %", value=safe_float(w_d.get('ke', 15)))
    if st.button("Salvar Financeiro"):
        save_data(st.session_state.group, "wacc", {"ke":ke})

# --- 8. RELATÓRIO FINAL ---
elif menu == "08 RELATÓRIO FINAL":
    st.title("Relatório Consolidado")
    st.write(f"Empresa: {data.get('company_info', {}).get('nome', 'N/A')}")
    st.button("Exportar (Ctrl + P)")

# --- 09. PORTAL DO ORIENTADOR ---
elif menu == "09 PORTAL DO ORIENTADOR" and st.session_state.is_teacher:
    st.title("Portal do Professor")
    target = st.selectbox("Grupo para Corrigir", ["Grupo 1", "Grupo 2", "Grupo 3"])
    dados_alvo = load_data(target)
    
    st.write(f"Empresa do grupo: {dados_alvo.get('company_info', {}).get('nome')}")
    
    if st.button("🤖 Rascunho IA"):
        st.session_state.ia_text = gerar_correcao_ia(dados_alvo)
    
    final_fb = st.text_area("Feedback Final", value=st.session_state.get('ia_text', dados_alvo.get('feedback', '')), height=300)
    if st.button("🚀 Liberar"):
        save_data(target, "feedback", final_fb)
        st.success("Feedback enviado!")
