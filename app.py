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

# --- CSS MASTER WHITELABEL & PEDAGÓGICO REFORÇADO ---
st.markdown("""
    <style>
    .stAppDeployButton, footer, #MainMenu, header {display:none !important;}
    .stApp { background-color: #fcfcfc !important; font-family: 'Segoe UI', Tahoma, sans-serif; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-right: 1px solid #1e293b !important; min-width: 300px !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label { color: #f1f5f9 !important; }
    h1, h2, h3 { color: #1a1a1a !important; font-weight: 800; letter-spacing: -0.02em !important; }

    /* Blocos Metodológicos */
    .metodologia-card { 
        background-color: #f0f7ff !important; 
        border-left: 6px solid #0052cc !important; 
        padding: 20px !important; 
        border-radius: 8px !important; 
        margin-bottom: 25px !important;
        color: #1e40af !important;
    }
    .metodologia-card h4 { color: #0052cc !important; margin-top: 0 !important; font-weight: 700 !important; }
    
    .justificativa-card { background-color: #fffdf0 !important; border: 1px solid #ffe58f !important; padding: 15px !important; border-radius: 8px !important; margin-top: 15px !important; }
    .formula-box { font-family: 'Courier New', monospace !important; background-color: #2d3436 !important; color: #fab1a0 !important; padding: 15px !important; border-radius: 5px !important; font-size: 0.9em !important; margin: 15px 0 !important; border: 1px solid #636e72 !important; display: block; }
    .risk-card { padding: 22px; border-radius: 12px; text-align: center; color: white !important; font-weight: 600; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .swot-card { padding: 15px; border-radius: 8px; height: 130px; color: white !important; font-size: 0.85em; overflow-y: auto; margin-bottom: 10px; }
    .stButton>button { background-color: #0052cc !important; color: white !important; border-radius: 6px; width: 100%; font-weight: 600; height: 45px; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- HELPER UI: CABEÇALHO PEDAGÓGICO ---
def render_academic_header(titulo, objetivo, tarefa):
    st.markdown(f"""<div class="metodologia-card"><h4>🎓 GUIA METODOLÓGICO: {titulo}</h4><p><b>Objetivo Acadêmico:</b> {objetivo}</p><p><b>Ação Requerida:</b> {tarefa}</p></div>""", unsafe_allow_html=True)

# --- FUNÇÕES DE API (BCB SGS & FOCUS) ---
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

# --- CONEXÃO SUPABASE ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("Erro Crítico de Conexão com o Banco de Dados.")
    st.stop()

# --- FUNÇÕES DE SEGURANÇA E DADOS ---
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
    return {'group_id': gid, 'porter': {}, 'dre': {}, 'wacc': {}, 'swot': {}, 'hhi': '0', 'diary': {}, 'participants': {}, 'company_info': {}, 'feedback': ''}

def save_data(gid, column, value):
    if isinstance(value, (dict, list)): value = json.dumps(value)
    supabase.table("eco_data").upsert({"group_id": gid, column: str(value)}).execute()

def gerar_correcao_ia(dados):
    if "OPENAI_API_KEY" not in st.secrets: return "Configure a chave OpenAI nos Secrets."
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    prompt = f"Analise este projeto acadêmico de consultoria e forneça um parecer técnico: {dados}"
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return f"Erro na IA: {e}"

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_teacher' not in st.session_state: st.session_state.is_teacher = False

if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Intelligence")
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
            else: st.error("Acesso Negado.")
    st.stop()

data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    st.markdown(f"<h2 style='text-align:center;'>{st.session_state.group.upper()}</h2>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("<p style='color:#94a3b8; font-weight:700; font-size:0.75rem;'>EXPECTATIVAS FOCUS (BCB)</p>", unsafe_allow_html=True)
    df_focus = get_focus_projections()
    if not df_focus.empty:
        for idx, row in df_focus.iterrows():
            st.markdown(f"<div style='background:#1e293b; padding:10px; border-radius:8px; margin-bottom:5px; border-left:4px solid #3b82f6;'><small style='color:#94a3b8'>{row['Indicador']}</small><br><b style='color:white'>{row['Mediana']}%</b></div>", unsafe_allow_html=True)
    
    st.divider()
    selic_ref = st.number_input("Benchmark Selic Trabalho (%)", value=get_live_selic(), step=0.25)
    
    menu = st.radio("ROTEIRO METODOLÓGICO", [
        "01 DASHBOARD GERAL", "02 GOVERNANÇA E EQUIPE", "03 PERFIL DO CLIENTE", 
        "04 DIÁRIO DE CAMPO", "05 ANÁLISE ESTRATÉGICA", "06 CENÁRIO MONETÁRIO", 
        "07 FINANCEIRO & VALOR", "08 REFERENCIAL TEÓRICO", "09 RELATÓRIO FINAL"
    ] + (["10 PORTAL DO ORIENTADOR"] if st.session_state.is_teacher else []), label_visibility="collapsed")
    
    if st.button("Sair"): st.session_state.auth = False; st.rerun()

# --- 01. DASHBOARD ---
if menu == "01 DASHBOARD GERAL":
    st.title("Executive Intelligence Dashboard")
    render_academic_header("Visão do Projeto", "Consolidar indicadores de risco e valor.", "Analise o score de saúde e os comentários do seu orientador.")
    if data.get('feedback'): st.warning(f"📬 PARECER DO PROFESSOR: {data.get('feedback')}")
    
    col_g, col_s = st.columns([1.5, 2])
    with col_g:
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=75, title={'text':"Health Score Index"},
            gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#2563eb"}, 'steps':[{'range':[0,50],'color':"#dc3545"},{'range':[50,80],'color':"#ffc107"},{'range':[80,100],'color':"#28a745"}]})), use_container_width=True)
    with col_s:
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown('<div class="risk-card" style="background:#10b981">RISCO<br>CRÉDITO</div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="risk-card" style="background:#f59e0b">RISCO<br>MERCADO</div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="risk-card" style="background:#10b981">VALOR<br>EVA</div>', unsafe_allow_html=True)

# --- 02. EQUIPE ---
elif menu == "02 EQUIPE E GOVERNANÇA":
    st.title("Estrutura de Governança")
    render_academic_header("Identificação", "Definir os responsáveis técnicos.", "Insira o nome de todos os alunos e do orientador.")
    part = data.get('participants', {})
    with st.form("f_eq"):
        c1, c2 = st.columns(2)
        al1 = c1.text_input("Aluno 1 (Líder)", value=part.get('al1', ''))
        al2 = c1.text_input("Aluno 2", value=part.get('al2', ''))
        prof = c2.text_input("Professor Orientador", value=part.get('prof', ''))
        if st.form_submit_button("Salvar Equipe"):
            save_data(st.session_state.group, "participants", {"al1":al1, "al2":al2, "prof":prof})
            st.success("Salvo!")

# --- 03. PERFIL DO CLIENTE ---
elif menu == "03 PERFIL DO CLIENTE":
    st.title("Caracterização Corporativa")
    render_academic_header("Entendimento do Negócio", "Contextualizar o ambiente de operação.", "Descreva a empresa e seu modelo de negócio.")
    info = data.get('company_info', {})
    with st.form("f_info"):
        n = st.text_input("Razão Social", value=info.get('nome', ''))
        s = st.selectbox("Setor", ["Varejo", "Indústria", "Serviços", "Agro", "Tech"])
        d = st.text_area("Descrição do Negócio", value=info.get('desc', ''))
        if st.form_submit_button("Salvar Perfil"):
            save_data(st.session_state.group, "company_info", {"nome":n, "setor":s, "desc":d})
            st.success("Salvo!")

# --- 04. DIÁRIO DE CAMPO ---
elif menu == "04 DIAGNÓSTICO DE CAMPO":
    st.title("Guia de Entrevista e Diagnóstico")
    render_academic_header("Diagnóstico Qualitativo", "Coletar evidências reais in loco.", "Responda o roteiro durante a visita técnica.")
    dia = data.get('diary', {})
    with st.form("f_dia"):
        q1 = st.text_area("1. Qual o diferencial estratégico observado?", value=dia.get('q1', ''))
        q2 = st.text_area("2. Como a taxa de juros afeta o caixa atual?", value=dia.get('q2', ''))
        if st.form_submit_button("Sincronizar Notas"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2})
            st.success("Salvo!")

# --- 05. ESTRATÉGIA ---
elif menu == "05 ANÁLISE ESTRATÉGICA":
    st.title("Inteligência Competitiva")
    render_academic_header("Estratégia Micro", "Avaliar hostilidade setorial e competitividade.", "Preencha Porter, HHI e SWOT.")
    t1, t2, t3 = st.tabs(["Michael Porter", "HHI", "Matriz SWOT"])
    with t1:
        p = data.get('porter', {})
        p1 = st.slider("Ameaça Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        p5 = st.slider("Rivalidade", 1, 5, int(safe_float(p.get('p5', 3))))
        p_just = st.text_area("Fundamentação Teórica das Notas:", value=p.get('just', ''))
        if st.button("Salvar Porter"): save_data(st.session_state.group, "porter", {"p1":p1, "p5":p5, "just":p_just})
    with t2:
        st.markdown("<div class='formula-box'>HHI = Σ (Share)²</div>", unsafe_allow_html=True)
        s1 = st.number_input("Market Share Líder %", 0.0, 100.0, 30.0)
        h_calc = s1**2 + (100-s1)**2
        st.metric("Índice HHI", int(h_calc))
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", str(s1))
    with t3:
        sw = data.get('swot', {})
        f = st.text_area("Forças Internas", value=sw.get('f', ''))
        fra = st.text_area("Fraquezas Internas", value=sw.get('fra', ''))
        if st.button("Salvar SWOT"): save_data(st.session_state.group, "swot", {"f":f, "fra":fra})

# --- 06. MONETÁRIO ---
elif menu == "06 CENÁRIO MONETÁRIO":
    st.title("Diagnóstico Monetário")
    render_academic_header("Transmissão de Juros", "Analisar o impacto macro no balanço.", "Compare a taxa da empresa com o Relatório Focus.")
    dre_d = data.get('dre', {})
    idx = st.number_input("Taxa Empresa %", value=safe_float(dre_d.get('idx_valor', selic_ref)))
    div = st.number_input("Endividamento (R$)", value=safe_float(dre_d.get('divida', 400000)))
    if st.button("Salvar Macro"): save_data(st.session_state.group, "dre", {"idx_valor":idx, "divida":div})
    sim = st.slider("Simular Selic %", 0.0, 30.0, selic_ref)
    st.plotly_chart(px.line(x=list(range(0,31)), y=[100000 - (div*s/100) for s in range(0,31)], title="Análise de Sensibilidade"))

# --- 07. FINANCEIRO ---
elif menu == "07 FINANCEIRO & VALOR":
    st.title("Engenharia Financeira")
    render_academic_header("Custo de Capital e Valor", "Determinar o valor intrínseco do negócio.", "Calcule o WACC e fundamente o crescimento (g).")
    w_d = data.get('wacc', {})
    t1, t2 = st.tabs(["WACC & EVA", "Valuation"])
    with t1:
        st.markdown("<div class='formula-box'>WACC = (E/V * Ke) + (D/V * Kd * 0.66)</div>", unsafe_allow_html=True)
        ke = st.number_input("Ke %", value=safe_float(w_d.get('ke', 15)))
        kd = st.number_input("Kd %", value=safe_float(w_d.get('kd', 12)))
        w_res = (ke*0.6) + (kd*0.4*0.66)
        st.metric("WACC Final", f"{w_res:.2f}%")
        if st.button("Salvar Financeiro"): save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "wacc_final":w_res})
    with t2:
        st.markdown("<div class='formula-box'>Enterprise Value = EBITDA(1+g) / (WACC - g)</div>", unsafe_allow_html=True)
        g = st.slider("Taxa de Crescimento (g) %", 0.0, 10.0, 3.0)
        g_just = st.text_area("Justificativa da Taxa g (Base Focus/PIB):", value=w_d.get('g_just', ''))
        if st.button("Sincronizar Valuation"): save_data(st.session_state.group, "wacc", {**w_d, "g":g, "g_just":g_just})

# --- 08. REFERENCIAL ---
elif menu == "08 REFERENCIAL TEÓRICO":
    st.title("📚 Fundamentação Metodológica")
    st.markdown("""
    Este sistema acadêmico utiliza os seguintes referenciais bibliográficos:
    - **PORTER, Michael.** Estratégia Competitiva. Elsevier.
    - **ASSAF NETO, Alexandre.** Finanças Corporativas e Valor. Atlas.
    - **DAMODARAN, Aswath.** Valuation. Wiley.
    - **BANCO CENTRAL DO BRASIL.** Relatório Focus e Sistema SGS.
    """)

# --- 09. RELATÓRIO ---
elif menu == "09 RELATÓRIO FINAL":
    st.title("📄 Relatório Técnico")
    st.write(f"Empresa: {data.get('company_info', {}).get('nome', 'N/A')}")
    st.divider(); st.button("Imprimir (Ctrl+P)")

# --- 10. PROFESSOR ---
elif menu == "10 PORTAL DO ORIENTADOR" and st.session_state.is_teacher:
    st.title("🎓 Portal do Professor")
    target = st.selectbox("Grupo para Avaliar", ["Grupo 1", "Grupo 2", "Grupo 3"])
    dados = load_data(target)
    if st.button("🤖 IA: Rascunho de Feedback"): st.session_state.ia = gerar_correcao_ia(dados)
    txt = st.text_area("Feedback Final do Professor:", value=st.session_state.get('ia', dados.get('feedback', '')), height=300)
    if st.button("🚀 Liberar Feedback"): save_data(target, "feedback", txt); st.success("Enviado!")
