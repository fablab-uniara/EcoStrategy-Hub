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

# --- CSS WHITELABEL REFORÇADO (CORRIGIDO PARA SIDEBAR APARECER) ---
st.markdown("""
    <style>
    /* Esconde botões de desenvolvedor e marca d'água */
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    
    /* REMOVIDO: header {visibility: hidden;} - Isso matava a sidebar em alguns navegadores */
    
    /* Cores e Design Elite */
    .stApp { background-color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    .stApp p, .stApp span, .stApp label { color: #1e293b !important; }
    
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-right: 1px solid #1e293b !important; min-width: 300px !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label { color: #f1f5f9 !important; }
    
    h1, h2, h3 { color: #002e5d !important; font-weight: 800; letter-spacing: -0.04em !important; }
    
    .risk-card { padding: 20px; border-radius: 12px; text-align: center; color: white !important; font-weight: bold; margin-bottom: 10px; border: 1px solid rgba(0,0,0,0.1); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .insight-box { background-color: #ffffff !important; padding: 20px; border-left: 6px solid #0052cc; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
    .formula-text { font-family: 'Courier New', Courier, monospace; background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-size: 0.85em; color: #d63384; border: 1px solid #ddd; display: block; margin: 10px 0;}
    .guide-text { font-size: 0.92em; color: #444; line-height: 1.5; background: #fffbe6; padding: 12px; border-radius: 5px; border: 1px solid #ffe58f; margin-bottom: 15px;}
    .swot-card { padding: 12px; border-radius: 8px; height: 110px; color: white !important; font-size: 0.82em; overflow-y: auto; margin-bottom: 8px; }
    .stButton>button { background-color: #0052cc !important; color: white !important; border-radius: 6px; width: 100%; font-weight: bold; height: 45px; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE SEGURANÇA ---
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

# --- CONEXÃO SUPABASE ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("Erro de conexão. Verifique os Secrets.")
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
    if "OPENAI_API_KEY" not in st.secrets: return "Configure a chave da OpenAI."
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    prompt = f"Analise como professor de economia este projeto de consultoria: {dados}"
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
        # VOLTANDO A OPÇÃO DE PROFESSOR
        group_sel = st.selectbox("Selecione seu Perfil", ["Grupo 1", "Grupo 2", "Grupo 3", "Acesso Professor"])
        pwd_input = st.text_input("Chave de Acesso", type="password")
        
        if st.button("Entrar no Hub"):
            passwords = st.secrets.get("GROUP_PASSWORDS", {})
            dev_pwd = st.secrets.get("DEV_PASSWORD")
            
            if pwd_input == passwords.get(group_sel) or pwd_input == dev_pwd:
                st.session_state.auth = True
                st.session_state.group = "Grupo 1" if group_sel == "Acesso Professor" else group_sel
                st.session_state.is_teacher = (pwd_input == dev_pwd)
                st.rerun()
            else: st.error("Acesso negado.")
    st.stop()

# CARREGA DADOS
data = load_data(st.session_state.group)

# --- SIDEBAR (ESSENCIAL PARA NAVEGAÇÃO) ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    st.markdown(f"<h2>{st.session_state.group.upper()}</h2>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("**Cenário Macro (Real-Time)**")
    selic_meta = get_live_selic()
    st.caption(f"Selic Meta BCB: {selic_meta}%")
    selic_ref = st.number_input("Benchmark Trabalho (%)", value=selic_meta, step=0.25)
    
    st.divider()
    
    menu_options = [
        "01 DASHBOARD EXECUTIVO", "02 EQUIPE", "03 PERFIL EMPRESA", 
        "04 DIÁRIO DE CAMPO", "05 ESTRATÉGIA", "06 MONETÁRIO", 
        "07 FINANCEIRO & VALOR", "08 RELATÓRIO FINAL"
    ]
    if st.session_state.is_teacher:
        menu_options.append("09 PORTAL DO ORIENTADOR")
    
    menu = st.radio("NAVEGAÇÃO", menu_options)
    
    st.divider()
    if st.button("Sair / Logout"):
        st.session_state.auth = False
        st.rerun()

# --- 1. DASHBOARD ---
if menu == "01 DASHBOARD EXECUTIVO":
    st.title("Executive Management Dashboard")
    fb = data.get('feedback', '')
    if fb: st.markdown(f'<div class="feedback-box"><b>📬 PARECER DO PROFESSOR:</b><br>{fb}</div>', unsafe_allow_html=True)
    
    info = data.get('company_info', {})
    st.markdown(f'<div class="insight-box"><h4>Unidade: {st.session_state.group} | Cliente: {info.get("nome", "Pendente")}</h4></div>', unsafe_allow_html=True)
    
    # Cálculos Intelligence
    dre_d = data.get('dre', {})
    ebitda = safe_float(dre_d.get('receita')) - safe_float(dre_d.get('custos'))
    divida = safe_float(dre_d.get('divida'))
    idx_total = safe_float(dre_d.get('idx_valor', selic_ref)) + safe_float(dre_d.get('spread', 2.0))
    break_even = (ebitda / divida * 100) if divida > 0 else 0
    hhi_str = str(data.get('hhi', '0'))
    try: hhi_val = sum([float(x)**2 for x in hhi_str.split(",") if x.strip()])
    except: hhi_val = 0
    w_d = data.get('wacc', {})
    roi = safe_float(w_d.get('roi'))
    w_final = safe_float(w_d.get('wacc_final', 15.0))
    
    score = 0
    if divida == 0 or idx_total < (ebitda/divida*100 if divida > 0 else 100): score += 40
    if hhi_val < 2500: score += 30
    if roi > w_final: score += 30

    c_g, c_s = st.columns([1.5, 2])
    with c_g:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=score, title={'text':"Health Score"},
            gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#2563eb"},
            'steps':[{'range':[0,50],'color':"#dc3545"},{'range':[50,75],'color':"#ffc107"},{'range':[75,100],'color':"#28a745"}]}))
        st.plotly_chart(fig, use_container_width=True)
    with c_s:
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

# --- 2. EQUIPE ---
elif menu == "02 EQUIPE":
    st.title("Identificação da Equipe")
    part = data.get('participants', {})
    with st.form("f_part"):
        al1 = st.text_input("Líder", value=part.get('al1', ''))
        al2 = st.text_input("Consultor 2", value=part.get('al2', ''))
        prof = st.text_input("Professor", value=part.get('prof', ''))
        if st.form_submit_button("Salvar"):
            save_data(st.session_state.group, "participants", {"al1":al1, "al2":al2, "prof":prof})
            st.success("Salvo!")

# --- 3. PERFIL ---
elif menu == "03 PERFIL EMPRESA":
    st.title("Perfil do Cliente")
    info = data.get('company_info', {})
    with st.form("f_info"):
        nome = st.text_input("Nome", value=info.get('nome', ''))
        desc = st.text_area("Descrição", value=info.get('desc', ''))
        if st.form_submit_button("Salvar"):
            save_data(st.session_state.group, "company_info", {"nome":nome, "desc":desc})
            st.success("Salvo!")

# --- 4. DIÁRIO ---
elif menu == "04 DIÁRIO DE CAMPO":
    st.title("Guia de Entrevista")
    diary = data.get('diary', {})
    with st.form("f_diary"):
        q1 = st.text_area("1. Diferencial Estratégico", value=diary.get('q1', ''))
        q2 = st.text_area("2. Impacto Financeiro", value=diary.get('q2', ''))
        if st.form_submit_button("Salvar"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2})
            st.success("Salvo!")

# --- 5. ESTRATÉGIA ---
elif menu == "05 ESTRATÉGIA":
    st.title("Análise Microeconômica")
    t1, t2, t3 = st.tabs(["Porter", "HHI", "SWOT"])
    with t1:
        p = data.get('porter', {})
        p1 = st.slider("Ameaça Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        p5 = st.slider("Rivalidade", 1, 5, int(safe_float(p.get('p5', 3))))
        if st.button("Salvar Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1, "p5":p5})
    with t2:
        s1 = st.number_input("Share Líder %", 0.0, 100.0, 30.0)
        s2 = st.number_input("Share 2º %", 0.0, 100.0, 20.0)
        rest = 100 - (s1+s2)
        h_calc = s1**2 + s2**2 + rest**2
        st.metric("HHI", int(h_calc))
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", f"{s1},{s2},{rest}")
    with t3:
        sw = data.get('swot', {})
        f = st.text_area("Forças", value=sw.get('f', ''))
        fra = st.text_area("Fraquezas", value=sw.get('fra', ''))
        if st.button("Salvar SWOT"): save_data(st.session_state.group, "swot", {"f":f, "fra":fra})

# --- 6. MONETÁRIO ---
elif menu == "06 MONETÁRIO":
    st.title("Análise de Juros")
    dre = data.get('dre', {})
    rec = st.number_input("Receita", value=safe_float(dre.get('receita', 1000000)))
    div = st.number_input("Dívida", value=safe_float(dre.get('divida', 400000)))
    if st.button("Salvar Monetário"):
        save_data(st.session_state.group, "dre", {"receita":rec, "divida":div})

# --- 7. FINANCEIRO ---
elif menu == "07 FINANCEIRO & VALOR":
    st.title("WACC, EVA e Valuation")
    with st.expander("🎓 Fórmulas"):
        st.code("EV = EBITDA(1+g) / (WACC - g)")
    w = data.get('wacc', {})
    ke = st.number_input("Ke %", value=safe_float(w.get('ke', 15)))
    kd = st.number_input("Kd %", value=safe_float(w.get('kd', 12)))
    roi = st.number_input("ROI %", value=safe_float(w.get('roi', 18)))
    g = st.slider("g %", 0.0, 10.0, safe_float(w.get('g', 3)))
    if st.button("Salvar Financeiro"):
        save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "roi":roi, "g":g, "wacc_final": 14.5})

# --- 8. RELATÓRIO ---
elif menu == "08 RELATÓRIO FINAL":
    st.title("Relatório Consolidado")
    st.write(f"Empresa: {data.get('company_info', {}).get('nome', 'N/A')}")
    st.button("Exportar (Ctrl+P)")

# --- 09. PROFESSOR ---
elif menu == "09 PORTAL DO ORIENTADOR" and st.session_state.is_teacher:
    st.title("Portal do Professor")
    target = st.selectbox("Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
    dados_alvo = load_data(target)
    if st.button("🤖 IA"): st.session_state.ia = gerar_correcao_ia(dados_alvo)
    txt = st.text_area("Feedback", value=st.session_state.get('ia', dados_alvo.get('feedback', '')), height=300)
    if st.button("🚀 Liberar"): save_data(target, "feedback", txt)
