import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import openai
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Academic Excellence", layout="wide", initial_sidebar_state="expanded")

# --- CSS ACADÊMICO REFORÇADO ---
st.markdown("""
    <style>
    .stAppDeployButton, footer, #MainMenu, header {display:none !important;}
    .stApp { background-color: #fcfcfc !important; font-family: 'Segoe UI', Tahoma, sans-serif; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-right: 1px solid #1e293b !important; }
    
    /* Blocos Pedagógicos */
    .metodologia-card { 
        background-color: #f0f7ff; 
        border-left: 6px solid #0052cc; 
        padding: 20px; 
        border-radius: 8px; 
        margin-bottom: 25px;
    }
    .metodologia-card h4 { color: #0052cc !important; margin-top: 0; }
    
    .justificativa-card { 
        background-color: #fffdf0; 
        border: 1px solid #ffe58f; 
        padding: 15px; 
        border-radius: 8px; 
        margin-top: 15px;
        font-style: italic;
    }
    
    .formula-box { 
        font-family: 'Courier New', monospace; 
        background-color: #2d3436; 
        color: #fab1a0; 
        padding: 15px; 
        border-radius: 5px; 
        font-size: 0.9em;
        margin: 15px 0;
    }

    h1, h2, h3 { color: #1a1a1a; font-weight: 800; letter-spacing: -0.02em; }
    .stButton>button { background-color: #0052cc; color: white; border-radius: 6px; width: 100%; font-weight: 600; height: 45px; }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER UI: HEADER ACADÊMICO ---
def render_academic_header(titulo, objetivo, tarefa):
    st.markdown(f"""
    <div class="metodologia-card">
        <h4>🎓 Guia Acadêmico: {titulo}</h4>
        <p><b>Objetivo:</b> {objetivo}</p>
        <p><b>Tarefa:</b> {tarefa}</p>
    </div>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE API (BCB FOCUS) ---
@st.cache_data(ttl=3600)
def get_live_selic():
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        return float(requests.get(url, timeout=5).json()[0]['valor'])
    except: return 10.75

@st.cache_data(ttl=3600)
def get_focus_projections():
    try:
        url = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/aplicacao/recursos/ExpectativasMercadoAnuais?$top=10&$orderby=Data desc&$filter=Indicador eq 'IPCA' or Indicador eq 'PIB Total' or Indicador eq 'Selic'&$format=json"
        res = requests.get(url, timeout=5).json()
        df = pd.DataFrame(res['value'])
        atual = str(datetime.now().year)
        return df[df['DataReferencia'] == atual]
    except: return pd.DataFrame()

# --- CONEXÃO SUPABASE & SEGURANÇA ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("Erro de conexão.")
    st.stop()

def safe_float(val, default=0.0):
    try: return float(val)
    except: return default

def safe_json(val):
    if val is None or val == "" or val == "None": return {}
    if isinstance(val, dict): return val
    try: return json.loads(val)
    except: return {}

def load_data(gid):
    try:
        res = supabase.table("eco_data").select("*").eq("group_id", gid).execute()
        if res.data:
            row = res.data[0]
            cols = ['porter', 'dre', 'wacc', 'swot', 'participants', 'company_info', 'diary']
            for col in cols: row[col] = safe_json(row.get(col))
            return row
    except: pass
    return {'group_id': gid, 'porter': {}, 'dre': {}, 'wacc': {}, 'swot': {}, 'hhi': '0', 'diary': {}, 'participants': {}, 'company_info': {}}

def save_data(gid, column, value):
    if isinstance(value, (dict, list)): value = json.dumps(value)
    supabase.table("eco_data").upsert({"group_id": gid, column: str(value)}).execute()

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_teacher' not in st.session_state: st.session_state.is_teacher = False

if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Academic Platform")
    col_l1, col_l2, col_l3 = st.columns([1, 1.8, 1])
    with col_l2:
        try: st.image("logo.png", use_container_width=True)
        except: pass
        group_sel = st.selectbox("Selecione seu Perfil", ["Grupo 1", "Grupo 2", "Grupo 3", "Acesso Professor"])
        pwd_input = st.text_input("Senha de Acesso", type="password")
        if st.button("Autenticar Unidade"):
            passwords = st.secrets.get("GROUP_PASSWORDS", {})
            dev_pwd = st.secrets.get("DEV_PASSWORD")
            if pwd_input == passwords.get(group_sel) or pwd_input == dev_pwd:
                st.session_state.auth, st.session_state.group = True, ("Grupo 1" if group_sel == "Acesso Professor" else group_sel)
                st.session_state.is_teacher = (pwd_input == dev_pwd)
                st.rerun()
            else: st.error("Chave inválida.")
    st.stop()

data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2 style='color:white; text-align:center;'>{st.session_state.group.upper()}</h2>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("<p style='color:#94a3b8; font-weight:700; font-size:0.7rem;'>EXPECTATIVAS OFICIAIS (FOCUS)</p>", unsafe_allow_html=True)
    df_focus = get_focus_projections()
    if not df_focus.empty:
        for idx, row in df_focus.iterrows():
            st.markdown(f"<div style='background:#1e293b; padding:8px; border-radius:5px; margin-bottom:5px;'><small style='color:#94a3b8'>{row['Indicador']}</small><br><b style='color:white'>{row['Mediana']}%</b></div>", unsafe_allow_html=True)
    
    st.divider()
    selic_meta = get_live_selic()
    selic_ref = st.number_input("Selic Vigente (%)", value=selic_meta, step=0.25)
    
    menu = st.radio("ETAPAS METODOLÓGICAS", [
        "01 DASHBOARD GERAL", "02 GOVERNANÇA E EQUIPE", "03 PERFIL DO CLIENTE", 
        "04 DIÁRIO DE CAMPO", "05 ANÁLISE ESTRATÉGICA", "06 CENÁRIO MONETÁRIO", 
        "07 FINANCEIRO & VALOR", "08 FUNDAMENTAÇÃO TEÓRICA", "09 RELATÓRIO FINAL"
    ] + (["10 PORTAL DO ORIENTADOR"] if st.session_state.is_teacher else []))
    
    if st.button("Sair"): st.session_state.auth = False; st.rerun()

# --- 01. DASHBOARD ---
if menu == "01 DASHBOARD GERAL":
    st.title("Painel Geral de Inteligência")
    render_academic_header("Visão Integrada", "Consolidar todos os riscos e indicadores de valor.", "Analise o Health Score e os Pareceres do Orientador para ajustar sua estratégia.")
    
    if data.get('feedback'): st.warning(f"📬 PARECER DO ORIENTADOR: {data.get('feedback')}")
    
    # Cálculos dinâmicos simplificados para o gauge
    dre_d = data.get('dre', {})
    w_d = data.get('wacc', {})
    roi = safe_float(w_d.get('roi'))
    w_final = safe_float(w_d.get('wacc_final', 15.0))
    
    score = 70 # Mock score para visualização rápida
    st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=score, title={'text':"Índice de Saúde Econômica (Health Score)"},
        gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#2563eb"},
        'steps':[{'range':[0,50],'color':"#dc3545"},{'range':[50,80],'color':"#ffc107"},{'range':[80,100],'color':"#28a745"}]})), use_container_width=True)

# --- 02. EQUIPE ---
elif menu == "02 EQUIPE E GOVERNANÇA":
    st.title("Identificação de Governança")
    render_academic_header("Governança", "Definir os responsáveis técnicos.", "Insira os dados dos consultores e do professor.")
    part = data.get('participants', {})
    with st.form("f_eq"):
        al1 = st.text_input("Consultor Líder", value=part.get('al1', ''))
        prof = st.text_input("Professor Responsável", value=part.get('prof', ''))
        if st.form_submit_button("Sincronizar"):
            save_data(st.session_state.group, "participants", {"al1":al1, "prof":prof})
            st.success("Salvo!")

# --- 03. PERFIL CLIENTE ---
elif menu == "03 PERFIL DO CLIENTE":
    st.title("Caracterização Corporativa")
    render_academic_header("Entendimento do Negócio", "Contextualizar o ambiente de operação da empresa.", "Preencha os dados demográficos e operacionais do cliente.")
    info = data.get('company_info', {})
    with st.form("f_info"):
        n = st.text_input("Razão Social", value=info.get('nome', ''))
        s = st.selectbox("Setor", ["Varejo", "Indústria", "Serviços", "Agro"])
        d = st.text_area("Modelo de Negócio", value=info.get('desc', ''))
        if st.form_submit_button("Salvar Perfil"):
            save_data(st.session_state.group, "company_info", {"nome":n, "setor":s, "desc":d})
            st.success("Salvo!")

# --- 04. DIÁRIO ---
elif menu == "04 DIAGNÓSTICO DE CAMPO":
    st.title("Diário de Bordo Estruturado")
    render_academic_header("Diagnóstico Qualitativo", "Coletar evidências reais através de entrevistas.", "Siga o roteiro de perguntas durante a visita técnica.")
    dia = data.get('diary', {})
    with st.form("f_dia"):
        q1 = st.text_area("1. Histórico e Diferencial Competitivo", value=dia.get('q1', ''))
        q2 = st.text_area("2. Impacto da Taxa de Juros no Fluxo de Caixa", value=dia.get('q2', ''))
        if st.form_submit_button("Sincronizar Diário"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2})
            st.success("Salvo!")

# --- 05. ESTRATÉGIA ---
elif menu == "05 ANÁLISE ESTRATÉGICA":
    st.title("Inteligência Competitiva e de Mercado")
    render_academic_header("Microeconomia Aplicada", "Avaliar a hostilidade competitiva e concentração setorial.", "Preencha Porter e HHI.")
    
    t1, t2, t3 = st.tabs(["5 Forças de Porter", "Concentração (HHI)", "SWOT"])
    with t1:
        st.markdown("**Metodologia:** Notas de 1 (Hostilidade Mínima) a 5 (Hostilidade Máxima).")
        p = data.get('porter', {})
        p1 = st.slider("Ameaça de Novos Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        p5 = st.slider("Rivalidade entre Rivais", 1, 5, int(safe_float(p.get('p5', 3))))
        p_just = st.text_area("Justificativa das Notas (Teórica)", value=p.get('just', ''), help="Cite evidências observadas.")
        if st.button("Salvar Porter"): save_data(st.session_state.group, "porter", {"p1":p1, "p5":p5, "just":p_just})

    with t2:
        st.markdown("**Fórmula HHI:** Soma do quadrado das participações de mercado.")
        st.markdown("<div class='formula-box'>HHI = s1² + s2² + ... + sn²</div>", unsafe_allow_html=True)
        s1 = st.number_input("Market Share Líder %", 0.0, 100.0, 30.0)
        h_calc = s1**2 + (100-s1)**2 # Simplificado
        st.metric("Índice HHI", int(h_calc))
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", str(s1))

    with t3:
        sw = data.get('swot', {})
        f = st.text_area("Forças Internas", value=sw.get('f', ''))
        fra = st.text_area("Fraquezas Internas", value=sw.get('fra', ''))
        if st.button("Salvar SWOT"): save_data(st.session_state.group, "swot", {"f":f, "fra":fra})

# --- 06. MONETÁRIO ---
elif menu == "06 CENÁRIO MONETÁRIO":
    st.title("Diagnóstico Monetário e Sensibilidade")
    render_academic_header("Macroeconomia Aplicada", "Avaliar a transmissão da política monetária no balanço da empresa.", "Compare a taxa da empresa com o Relatório Focus.")
    
    dre_d = data.get('dre', {})
    idx = st.number_input("Taxa de Juros da Empresa %", value=safe_float(dre_d.get('idx_valor', selic_ref)))
    div = st.number_input("Endividamento Total (R$)", value=safe_float(dre_d.get('divida', 400000)))
    if st.button("Salvar Cenário"): save_data(st.session_state.group, "dre", {"idx_valor":idx, "divida":div})
    
    st.markdown("### Stress Test: Ponto de Ruptura")
    sim = st.slider("Simular Variação da Selic %", 0.0, 30.0, selic_ref)
    fig = px.line(x=list(range(0,31)), y=[100000 - (div*s/100) for s in range(0,31)], title="EBITDA vs Juros")
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    st.plotly_chart(fig)

# --- 07. FINANCEIRO ---
elif menu == "07 FINANCEIRO & VALOR":
    st.title("💰 Engenharia Financeira e Valuation")
    render_academic_header("Viabilidade e Valor", "Determinar o custo de capital e o valor intrínseco do negócio.", "Calcule o WACC e projete a perpetuidade (Gordon).")
    
    t1, t2 = st.tabs(["WACC & EVA", "Simulador Valuation (DCF)"])
    w_d = data.get('wacc', {})
    with t1:
        st.markdown("<div class='formula-box'>WACC = (E/V * Ke) + (D/V * Kd * 0.66)</div>", unsafe_allow_html=True)
        ke = st.number_input("Ke % (Custo Cap. Próprio)", value=safe_float(w_d.get('ke', 15)))
        kd = st.number_input("Kd % (Custo da Dívida)", value=safe_float(w_d.get('kd', 12)))
        wacc = (ke*0.6) + (kd*0.4*0.66)
        st.metric("WACC Final", f"{wacc:.2f}%")
        if st.button("Salvar Financeiro"): save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "wacc_final":wacc})
    
    with t2:
        st.markdown("<div class='formula-box'>EV = Fluxo(1+g) / (WACC - g)</div>", unsafe_allow_html=True)
        pib = float(df_focus[df_focus['Indicador'] == 'PIB Total'].iloc[0]['Mediana']) if not df_focus.empty else 2.0
        st.write(f"💡 **Benchmark PIB (Focus):** {pib}%")
        g = st.slider("Crescimento Perpétuo (g) %", 0.0, 10.0, pib)
        g_just = st.text_area("Justificativa da Taxa g (Base Metodológica)", value=w_d.get('g_just', ''))
        if st.button("Sincronizar Valuation"): save_data(st.session_state.group, "wacc", {**w_d, "g":g, "g_just":g_just})

# --- 08. REFERENCIAL TEÓRICO ---
elif menu == "08 FUNDAMENTAÇÃO TEÓRICA":
    st.title("📚 Referencial Metodológico")
    st.markdown("""
    Este Web App baseia-se nos seguintes pilares da ciência econômica:
    - **Porter, M.** (1986). *Estratégia Competitiva*.
    - **Assaf Neto, A.** (2021). *Finanças Corporativas e Valor*.
    - **Damodaran, A.** (2012). *Valuation*.
    - **Bacen.** Relatório Focus e Sistema Gerenciador de Séries Temporais (SGS).
    """)

# --- 09. RELATÓRIO ---
elif menu == "09 RELATÓRIO FINAL":
    st.title("📄 Relatório de Consultoria")
    st.write(f"Empresa: {data.get('company_info', {}).get('nome', 'N/A')}")
    st.divider()
    st.info("Pressione Ctrl+P para salvar em PDF.")

# --- 10. PROFESSOR ---
elif menu == "10 PORTAL DO ORIENTADOR" and st.session_state.is_teacher:
    st.title("🎓 Portal do Orientador")
    target = st.selectbox("Grupo para Avaliar", ["Grupo 1", "Grupo 2", "Grupo 3"])
    dados = load_data(target)
    st.write(f"**Justificativa de Porter:** {dados.get('porter', {}).get('just')}")
    st.write(f"**Justificativa g:** {dados.get('wacc', {}).get('g_just')}")
    txt = st.text_area("Feedback Final", value=dados.get('feedback', ''), height=300)
    if st.button("🚀 Liberar Feedback"): save_data(target, "feedback", txt); st.success("Feedback Enviado!")
