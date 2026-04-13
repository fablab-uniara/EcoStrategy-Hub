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
st.set_page_config(page_title="EcoStrategy Intelligence", layout="wide", initial_sidebar_state="expanded")

# --- CSS MASTER WHITELABEL ---
st.markdown("""
    <style>
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stApp { background-color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; min-width: 320px !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label { color: #f1f5f9 !important; }
    h1, h2, h3 { color: #002e5d !important; font-weight: 800; letter-spacing: -0.04em !important; }
    .risk-card { padding: 20px; border-radius: 12px; text-align: center; color: white !important; font-weight: 600; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .insight-box { background-color: #ffffff !important; padding: 20px; border-left: 6px solid #0052cc; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
    .formula-text { font-family: 'Courier New', Courier, monospace; background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-size: 0.85em; color: #d63384; border: 1px solid #ddd; display: block; margin: 10px 0;}
    .focus-box { background-color: #1e293b; padding: 12px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 10px; }
    .focus-title { color: #94a3b8; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; }
    .focus-value { color: #ffffff; font-size: 1.1rem; font-weight: 700; }
    .swot-card { padding: 12px; border-radius: 8px; height: 110px; color: white !important; font-size: 0.82em; overflow-y: auto; margin-bottom: 8px; }
    .stButton>button { background-color: #0052cc !important; color: white !important; border-radius: 6px; width: 100%; font-weight: 600; height: 45px; border: none; }
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
    st.error("Erro de conexão. Verifique os Secrets.")
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
    prompt = f"Analise como professor sênior de economia este projeto: {dados}"
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return f"Erro na IA: {e}"

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_teacher' not in st.session_state: st.session_state.is_teacher = False

if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    col_l1, col_l2, col_l3 = st.columns([1, 1.6, 1])
    with col_l2:
        try: st.image("logo.png", use_container_width=True)
        except: pass
        group_sel = st.selectbox("Selecione seu Perfil", ["Grupo 1", "Grupo 2", "Grupo 3", "Acesso Professor"])
        pwd_input = st.text_input("Chave de Acesso", type="password")
        if st.button("Entrar no Hub"):
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
    
    st.markdown("<p style='color:#94a3b8; font-weight:700; font-size:0.8rem;'>EXPECTATIVAS FOCUS (BCB)</p>", unsafe_allow_html=True)
    df_focus = get_focus_projections()
    if not df_focus.empty:
        for idx, row in df_focus.iterrows():
            st.markdown(f"<div class='focus-box'><div class='focus-title'>{row['Indicador']}</div><div class='focus-value'>{row['Mediana']}%</div></div>", unsafe_allow_html=True)
    
    st.divider()
    selic_meta = get_live_selic()
    st.info(f"Selic Atual: {selic_meta}%")
    selic_ref = st.number_input("Selic de Trabalho (%)", value=selic_meta, step=0.25)
    
    menu = st.radio("NAVEGAÇÃO", ["01 DASHBOARD", "02 EQUIPE", "03 PERFIL EMPRESA", "04 DIÁRIO DE CAMPO", "05 ESTRATÉGIA", "06 MONETÁRIO", "07 FINANCEIRO & VALOR", "08 RELATÓRIO FINAL"] + (["09 PORTAL DO ORIENTADOR"] if st.session_state.is_teacher else []))
    if st.button("Sair"): st.session_state.auth = False; st.rerun()

# --- 01. DASHBOARD ---
if menu == "01 DASHBOARD":
    st.title("📈 Dashboard Geral de Inteligência")
    fb = data.get('feedback', '')
    if fb: st.warning(f"📬 NOTA DO PROFESSOR: {fb}")
    
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
            gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#2563eb"}, 'steps':[{'range':[0,50],'color':"#dc3545"},{'range':[50,75],'color':"#ffc107"},{'range':[75,100],'color':"#28a745"}]}))
        st.plotly_chart(fig, use_container_width=True)
    with col_s:
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="risk-card" style="background:{"#28a745" if selic_ref < break_even else "#dc3545"}">CRÉDITO<br>{idx_total:.1f}%</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="risk-card" style="background:{"#28a745" if hhi_val < 1500 else "#ffc107"}">MERCADO<br>HHI:{int(hhi_val)}</div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="risk-card" style="background:{"#28a745" if roi > w_final else "#dc3545"}">VALOR<br>ROI:{roi}%</div>', unsafe_allow_html=True)

# --- 02. EQUIPE ---
elif menu == "02 EQUIPE":
    st.title("👥 Equipe de Consultoria")
    part = data.get('participants', {})
    with st.form("f_eq"):
        c1, c2 = st.columns(2)
        al1 = c1.text_input("Consultor 1 (Líder)", value=part.get('al1', ''))
        al2 = c1.text_input("Consultor 2", value=part.get('al2', ''))
        prof = c2.text_input("Professor Orientador", value=part.get('prof', ''))
        if st.form_submit_button("Salvar Equipe"):
            save_data(st.session_state.group, "participants", {"al1":al1, "al2":al2, "prof":prof})
            st.success("Salvo!")

# --- 03. PERFIL EMPRESA ---
elif menu == "03 PERFIL EMPRESA":
    st.title("🏢 Perfil do Cliente")
    info = data.get('company_info', {})
    with st.form("f_info"):
        n = st.text_input("Razão Social", value=info.get('nome', ''))
        s = st.selectbox("Setor", ["Varejo", "Indústria", "Serviços", "Agro", "Tech"])
        d = st.text_area("Modelo de Negócio", value=info.get('desc', ''))
        if st.form_submit_button("Salvar Perfil"):
            save_data(st.session_state.group, "company_info", {"nome":n, "setor":s, "desc":d})
            st.success("Salvo!")

# --- 04. DIÁRIO ---
elif menu == "04 DIÁRIO DE CAMPO":
    st.title("📔 Guia de Entrevista e Campo")
    dia = data.get('diary', {})
    with st.form("f_dia"):
        q1 = st.text_area("1. Histórico e Diferencial Estratégico", value=dia.get('q1', ''))
        q2 = st.text_area("2. Impacto de Juros no Caixa", value=dia.get('q2', ''))
        if st.form_submit_button("Salvar Notas"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2})
            st.success("Salvo!")

# --- 05. ESTRATÉGIA ---
elif menu == "05 ESTRATÉGIA":
    st.title("🔬 Porter, HHI e SWOT")
    t1, t2, t3 = st.tabs(["5 Forças de Porter", "Concentração HHI", "Matriz SWOT"])
    with t1:
        p = data.get('porter', {})
        p1 = st.slider("Ameaça Novos Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        p5 = st.slider("Rivalidade Rivais", 1, 5, int(safe_float(p.get('p5', 3))))
        if st.button("Salvar Porter"): save_data(st.session_state.group, "porter", {"p1":p1, "p5":p5})
    with t2:
        s1 = st.number_input("Share Líder %", 0.0, 100.0, 30.0)
        s2 = st.number_input("Share 2º %", 0.0, 100.0, 20.0)
        rest = 100-(s1+s2)
        st.metric("HHI", int(s1**2+s2**2+rest**2))
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", f"{s1},{s2},{rest}")
    with t3:
        sw = data.get('swot', {})
        f = st.text_area("Forças", value=sw.get('f', ''))
        fra = st.text_area("Fraquezas", value=sw.get('fra', ''))
        if st.button("Salvar SWOT"): save_data(st.session_state.group, "swot", {"f":f, "fra":fra})

# --- 06. MONETÁRIO ---
elif menu == "06 MONETÁRIO":
    st.title("🏦 Cenário Monetário e Stress Test")
    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_val = st.number_input("Taxa de Juros Empresa %", value=safe_float(dre_d.get('idx_valor', selic_ref)))
        rec = st.number_input("Receita Bruta", value=safe_float(dre_d.get('receita', 1000000)))
        div = st.number_input("Dívida Total", value=safe_float(dre_d.get('divida', 400000)))
        if st.button("Salvar Monetário"): save_data(st.session_state.group, "dre", {"idx_valor":idx_val, "receita":rec, "divida":div})
    with c2:
        sim = st.slider("Simular Taxa %", 0.0, 25.0, selic_ref)
        st.metric("Resultado Simulado", f"R$ {rec - rec*0.7 - (div*sim/100):,.2f}")
        fig = px.line(x=list(range(0,31)), y=[rec*0.3 - (div*s/100) for s in range(0,31)], title="Análise de Sensibilidade")
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig)

# --- 07. FINANCEIRO ---
elif menu == "07 FINANCEIRO & VALOR":
    st.title("💰 Custo de Capital e Valuation")
    w_d = data.get('wacc', {})
    t1, t2 = st.tabs(["WACC & EVA", "Simulador Valuation"])
    with t1:
        ke = st.number_input("Ke % (Sócio)", value=safe_float(w_d.get('ke', 15)))
        kd = st.number_input("Kd % (Banco)", value=safe_float(w_d.get('kd', 12)))
        wacc = (ke*0.6) + (kd*0.4*0.66)
        st.metric("WACC Final", f"{wacc:.2f}%")
        roi = st.number_input("ROI Operacional %", value=safe_float(w_d.get('roi', 18)))
        if st.button("Salvar Financeiro"): save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "roi":roi, "wacc_final":wacc})
    with t2:
        pib_proj = float(df_focus[df_focus['Indicador'] == 'PIB Total'].iloc[0]['Mediana']) if not df_focus.empty else 2.0
        g = st.slider("Taxa Crescimento (g) %", 0.0, 10.0, pib_proj)
        ebitda = safe_float(data.get('dre', {}).get('receita', 1000000)) * 0.3
        if wacc/100 > g/100:
            ev = (ebitda*(1+g/100)) / (wacc/100 - g/100)
            st.metric("Valor do Negócio", f"R$ {ev:,.2f}")
        else: st.error("Erro: WACC < g")

# --- 08. RELATÓRIO ---
elif menu == "08 RELATÓRIO FINAL":
    st.title("📄 Relatório Técnico")
    st.write(f"Empresa: {data.get('company_info', {}).get('nome', 'N/A')}")
    st.button("Exportar Consultoria (Ctrl+P)")

# --- 09. PROFESSOR ---
elif menu == "09 PORTAL DO ORIENTADOR" and st.session_state.is_teacher:
    st.title("🎓 Portal de Avaliação")
    target = st.selectbox("Selecione o Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
    dados = load_data(target)
    if st.button("🤖 IA"): st.session_state.ia = gerar_correcao_ia(dados)
    txt = st.text_area("Feedback", value=st.session_state.get('ia', dados.get('feedback', '')), height=300)
    if st.button("🚀 Liberar"): save_data(target, "feedback", txt)
