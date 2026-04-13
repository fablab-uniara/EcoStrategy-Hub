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
st.set_page_config(page_title="EcoStrategy Intelligence - Edição Acadêmica", layout="wide", initial_sidebar_state="expanded")

# --- CSS MASTER WHITELABEL & PEDAGÓGICO ---
st.markdown("""
    <style>
    /* Ocultar elementos técnicos do Streamlit */
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}

    /* Typography & Core Design */
    .stApp { background-color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-right: 1px solid #1e293b !important; min-width: 320px !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label { color: #f1f5f9 !important; }
    
    h1, h2, h3 { color: #002e5d !important; font-weight: 800; letter-spacing: -0.04em !important; }

    /* Blocos Pedagógicos */
    .guide-text { font-size: 0.92em; color: #475569 !important; line-height: 1.6; background: #eff6ff !important; padding: 18px; border-radius: 8px; border: 1px solid #dbeafe; margin-bottom: 20px;}
    .formula-box { font-family: 'Courier New', monospace; background-color: #f1f5f9 !important; padding: 12px; border-radius: 6px; font-size: 0.88em; color: #334155 !important; border: 1px solid #e2e8f0; display: block; margin: 10px 0; }
    .interpretation-box { background-color: #ffffff !important; padding: 15px; border-left: 5px solid #10b981; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-top: 10px; }

    /* Dashboard UI */
    .risk-card { padding: 22px; border-radius: 12px; text-align: center; color: white !important; font-weight: 600; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .stButton>button { background-color: #2563eb !important; color: white !important; border-radius: 6px; width: 100%; font-weight: 600; height: 48px; border: none; }
    .focus-card { background-color: #1e293b; padding: 10px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

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

# --- FUNÇÕES DE SEGURANÇA E PARSING ---
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
            for col in ['porter', 'dre', 'wacc', 'swot', 'participants', 'company_info', 'diary']:
                row[col] = safe_json(row.get(col))
            return row
    except: pass
    return {'group_id': gid, 'porter': {}, 'dre': {}, 'wacc': {}, 'swot': {}, 'hhi': '0', 'diary': {}, 'participants': {}, 'company_info': {}, 'feedback': ''}

def save_data(gid, column, value):
    if isinstance(value, (dict, list)): value = json.dumps(value)
    supabase.table("eco_data").upsert({"group_id": gid, column: str(value)}).execute()

def gerar_correcao_ia(dados):
    if "OPENAI_API_KEY" not in st.secrets: return "Configure a chave OpenAI."
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    prompt = f"Você é um orientador de economia. Analise este projeto de consultoria: {dados}"
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return f"Erro na IA: {e}"

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_teacher' not in st.session_state: st.session_state.is_teacher = False

if not st.session_state.auth:
    st.markdown("<h2 style='text-align: center; color: #0f172a; padding-top: 50px;'>ECOSTRATEGY INTELLIGENCE</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.6, 1])
    with col_l2:
        try: st.image("logo.png", use_container_width=True)
        except: pass
        group_sel = st.selectbox("Selecione seu Perfil", ["Grupo 1", "Grupo 2", "Grupo 3", "Acesso Professor"])
        pwd_input = st.text_input("Chave de Acesso", type="password")
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

# --- SIDEBAR (BCB FOCUS REAL-TIME) ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    st.markdown(f"<h2>{st.session_state.group.upper()}</h2>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("<p style='color:#94a3b8; font-weight:700; font-size:0.75rem; letter-spacing:0.1em;'>EXPECTATIVAS MERCADO (FOCUS/BCB)</p>", unsafe_allow_html=True)
    df_focus = get_focus_projections()
    if not df_focus.empty:
        for idx, row in df_focus.iterrows():
            st.markdown(f"<div class='focus-card'><small style='color:#94a3b8'>{row['Indicador']}</small><br><b style='color:white'>{row['Mediana']}%</b></div>", unsafe_allow_html=True)
    
    st.divider()
    selic_meta = get_live_selic()
    selic_ref = st.number_input("Benchmark de Trabalho (%)", value=selic_meta, step=0.25)
    
    menu = st.radio("SISTEMA DE GESTÃO", [
        "01 DASHBOARD EXECUTIVO", "02 EQUIPE E GOVERNANÇA", "03 PERFIL DO CLIENTE", 
        "04 DIAGNÓSTICO DE CAMPO", "05 ANÁLISE ESTRATÉGICA", "06 CENÁRIO MONETÁRIO", 
        "07 FINANCEIRO & VALOR", "08 RELATÓRIO FINAL"
    ] + (["09 PORTAL DO ORIENTADOR"] if st.session_state.is_teacher else []))
    
    if st.button("Finalizar Sessão"):
        st.session_state.auth = False
        st.rerun()

# --- 01. DASHBOARD ---
if menu == "01 DASHBOARD EXECUTIVO":
    st.title("Executive Intelligence Dashboard")
    
    # Feedback do Professor
    fb = data.get('feedback', '')
    if fb: st.warning(f"📬 NOTA DO ORIENTADOR: {fb}")
    
    info = data.get('company_info', {})
    st.markdown(f'<div class="insight-box"><h4>Cliente: {info.get("nome", "Pendente")}</h4><p>Análise consolidada de riscos e criação de valor econômico.</p></div>', unsafe_allow_html=True)
    
    # Cálculos Intelligence
    dre_d = data.get('dre', {})
    ebitda = safe_float(dre_d.get('receita')) - safe_float(dre_d.get('custos'))
    divida = safe_float(dre_d.get('divida'))
    idx_total = safe_float(dre_d.get('idx_valor', selic_ref))
    break_even = (ebitda / divida * 100) if divida > 0 else 0
    hhi_str = str(data.get('hhi', '0'))
    try: hhi_val = sum([float(x)**2 for x in hhi_str.split(",") if x.strip()])
    except: hhi_val = 0
    w_d = data.get('wacc', {})
    roi = safe_float(w_d.get('roi'))
    w_final = safe_float(w_d.get('wacc_final', 15.0))
    
    score = 0
    if divida == 0 or idx_total < break_even: score += 40
    if hhi_val < 2500: score += 30
    if roi > (selic_ref + 5): score += 30

    col_g, col_s = st.columns([1.5, 2])
    with col_g:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=score, title={'text':"Health Score Index"},
            gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#2563eb"},
            'steps':[{'range':[0,50],'color':"#ef4444"},{'range':[50,75],'color':"#f59e0b"},{'range':[75,100],'color':"#10b981"}]}))
        st.plotly_chart(fig, use_container_width=True)
    with col_s:
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="risk-card" style="background:{"#10b981" if selic_ref < break_even else "#ef4444"}">CRÉDITO<br>{idx_total:.1f}%</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="risk-card" style="background:{"#10b981" if hhi_val < 1500 else "#f59e0b"}">MERCADO<br>HHI:{int(hhi_val)}</div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="risk-card" style="background:{"#10b981" if roi > w_final else "#ef4444"}">VALOR<br>ROI:{roi}%</div>', unsafe_allow_html=True)

# --- 02. EQUIPE ---
elif menu == "02 EQUIPE E GOVERNANÇA":
    st.title("Estrutura da Equipe")
    st.markdown('<div class="guide-text"><b>Orientação:</b> Identifique individualmente os consultores responsáveis pelo projeto.</div>', unsafe_allow_html=True)
    part = data.get('participants', {})
    with st.form("f_eq"):
        c1, c2 = st.columns(2)
        al1 = c1.text_input("Consultor 1 (Líder)", value=part.get('al1', ''))
        al2 = c1.text_input("Consultor 2", value=part.get('al2', ''))
        al3 = c1.text_input("Consultor 3", value=part.get('al3', ''))
        al4 = c2.text_input("Consultor 4", value=part.get('al4', ''))
        al5 = c2.text_input("Consultor 5", value=part.get('al5', ''))
        prof = c2.text_input("Professor Orientador", value=part.get('prof', ''))
        if st.form_submit_button("Sincronizar Governança"):
            save_data(st.session_state.group, "participants", {"al1":al1, "al2":al2, "al3":al3, "al4":al4, "al5":al5, "prof":prof})
            st.success("Dados Salvos!")

# --- 03. PERFIL DO CLIENTE ---
elif menu == "03 PERFIL DO CLIENTE":
    st.title("Caracterização Corporativa")
    st.markdown('<div class="guide-text"><b>Orientação:</b> Defina os dados demográficos e o modelo de negócio para embasar as análises financeiras.</div>', unsafe_allow_html=True)
    info = data.get('company_info', {})
    with st.form("f_info"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Razão Social", value=info.get('nome', ''))
        s = c1.selectbox("Setor Econômico", ["Varejo", "Indústria", "Serviços", "Agro", "Tech"])
        f = c1.text_input("Ano de Fundação", value=info.get('fundacao', ''))
        colab = c2.number_input("Nº de Colaboradores", value=int(safe_float(info.get('colab', 0))))
        d = st.text_area("Descrição do Modelo de Negócio", value=info.get('desc', ''))
        if st.form_submit_button("Salvar Perfil"):
            save_data(st.session_state.group, "company_info", {"nome":n, "setor":s, "fundacao":f, "colab":colab, "desc":d})
            st.success("Perfil Atualizado!")

# --- 04. DIÁRIO ---
elif menu == "04 DIAGNÓSTICO DE CAMPO":
    st.title("Guia de Entrevista e Atividades")
    st.markdown('<div class="guide-text"><b>Roteiro:</b> Utilize estas perguntas durante a visita técnica. Este é o fundamento qualitativo da consultoria.</div>', unsafe_allow_html=True)
    dia = data.get('diary', {})
    with st.form("f_dia"):
        q1 = st.text_area("1. Qual o principal diferencial competitivo e histórico da empresa?", value=dia.get('q1', ''))
        q2 = st.text_area("2. Como a variação de juros e inflação impactou o caixa no último ano?", value=dia.get('q2', ''))
        q3 = st.text_area("3. Quem são os rivais diretos e qual a barreira de entrada no setor?", value=dia.get('q3', ''))
        if st.form_submit_button("Sincronizar Notas de Campo"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2, "q3":q3})
            st.success("Diário Sincronizado!")

# --- 05. ESTRATÉGIA ---
elif menu == "05 ANÁLISE ESTRATÉGICA":
    st.title("Análise Setorial e Competitiva")
    
    with st.expander("🎓 Fundamentação Teórica: Porter, HHI e SWOT"):
        st.markdown("**1. Michael Porter:** Avalia o lucro médio do setor. Scores altos indicam ambiente hostil.")
        st.markdown("**2. HHI:** Mede concentração. <span class='formula-box'>HHI = Σ (Share²)</span>", unsafe_allow_html=True)
        st.markdown("**Interpretando o HHI:** < 1500 (Desconcentrado), 1500-2500 (Moderado), > 2500 (Altamente Concentrado).")

    t1, t2, t3 = st.tabs(["5 Forças de Porter", "Concentração HHI", "Matriz SWOT"])
    with t1:
        p = data.get('porter', {})
        p1 = st.slider("Ameaça de Novos Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        p2 = st.slider("Poder dos Fornecedores", 1, 5, int(safe_float(p.get('p2', 3))))
        p3 = st.slider("Poder dos Clientes", 1, 5, int(safe_float(p.get('p3', 3))))
        p5 = st.slider("Rivalidade entre Concorrentes", 1, 5, int(safe_float(p.get('p5', 3))))
        if st.button("Salvar Matriz Porter"): 
            save_data(st.session_state.group, "porter", {"p1":p1, "p2":p2, "p3":p3, "p5":p5})
            st.success("Porter Salvo!")
    with t2:
        s1 = st.number_input("Share Empresa Líder %", 0.0, 100.0, 30.0)
        s2 = st.number_input("Share 2º Concorrente %", 0.0, 100.0, 20.0)
        rest = 100-(s1+s2)
        h_calc = s1**2 + s2**2 + rest**2
        st.metric("Índice HHI", int(h_calc))
        st.plotly_chart(px.pie(values=[s1,s2,rest], names=["Líder","2º","Outros"], hole=0.4))
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", f"{s1},{s2},{rest}")
    with t3:
        sw = data.get('swot', {})
        f = st.text_area("Forças (Interno)", value=sw.get('f', ''))
        fra = st.text_area("Fraquezas (Interno)", value=sw.get('fra', ''))
        o = st.text_area("Oportunidades (Externo)", value=sw.get('o', ''))
        a = st.text_area("Ameaças (Externo)", value=sw.get('a', ''))
        if st.button("Salvar SWOT"): save_data(st.session_state.group, "swot", {"f":f, "fra":fra, "o":o, "a":a})

# --- 06. MONETÁRIO ---
elif menu == "06 CENÁRIO MONETÁRIO":
    st.title("Stress Test e Transmissão de Juros")
    st.markdown('<div class="guide-text"><b>Orientação:</b> Compare a taxa de juros da empresa com as projeções do Focus exibidas na Sidebar. Simule o "Ponto de Ruptura" onde o juro consome todo o EBITDA.</div>', unsafe_allow_html=True)
    
    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_val = st.number_input("Taxa de Juros Empresa %", value=safe_float(dre_d.get('idx_valor', selic_ref)))
        rec = st.number_input("Receita Bruta Anual", value=safe_float(dre_d.get('receita', 1000000)))
        div = st.number_input("Dívida Total", value=safe_float(dre_d.get('divida', 400000)))
        if st.button("Salvar Monetário"): save_data(st.session_state.group, "dre", {"idx_valor":idx_val, "receita":rec, "divida":div})
    with c2:
        ebitda = rec * 0.3
        sim = st.slider("Simular Variação de Juros %", 0.0, 30.0, selic_ref)
        lucro_e = ebitda - (div * sim/100)
        st.metric("Lucro Líquido na Simulação", f"R$ {lucro_e:,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div*s/100) for s in range(0,31)], title="Análise de Sensibilidade EBITDA vs Juros")
        fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Insolvência")
        st.plotly_chart(fig)

# --- 07. FINANCEIRO ---
elif menu == "07 FINANCEIRO & VALOR":
    st.title("Custo de Capital e Valor do Negócio")
    
    with st.expander("🎓 Fundamentação Pedagógica: WACC e Gordon"):
        st.markdown("**1. WACC:** Taxa mínima de atratividade para o risco do negócio.")
        st.markdown("<span class='formula-box'>WACC = (E/V * Ke) + (D/V * Kd * 0.66)</span>", unsafe_allow_html=True)
        st.markdown("**2. Gordon Growth:** Valor presente da empresa considerando o futuro infinito.")
        st.markdown("<span class='formula-box'>Enterprise Value = EBITDA * (1+g) / (WACC - g)</span>", unsafe_allow_html=True)

    w_d = data.get('wacc', {})
    t1, t2 = st.tabs(["WACC & EVA", "Simulador Valuation (DCF)"])
    with t1:
        ke = st.number_input("Ke % (Custo Cap. Próprio)", value=safe_float(w_d.get('ke', 15)))
        kd = st.number_input("Kd % (Custo da Dívida)", value=safe_float(w_
