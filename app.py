import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import openai # IMPORTANTE: Adicione 'openai' no seu requirements.txt
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Intelligence", layout="wide", initial_sidebar_state="expanded")

# --- CSS MASTER (Whitelabel + Melhorias de Visibilidade) ---
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
    .risk-card { padding: 22px; border-radius: 8px; text-align: center; color: white !important; font-weight: 600; }
    .insight-box { background-color: #ffffff !important; padding: 25px; border-left: 5px solid #3b82f6; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 25px; border: 1px solid #f1f5f9; }
    .stButton>button { background-color: #2563eb !important; color: white !important; border-radius: 6px; width: 100%; font-weight: 600; height: 48px; border: none; }
    .stButton>button:hover { background-color: #1d4ed8 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE APOIO ---
def safe_float(val, default=0.0):
    try: return float(val)
    except: return default

def safe_json(val):
    if val is None or val == "" or val == "None": return {}
    if isinstance(val, dict): return val
    try: return json.loads(val)
    except: return {}

def get_live_selic():
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        return float(requests.get(url, timeout=5).json()[0]['valor'])
    except: return 10.75

# --- CONEXÃO SUPABASE ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("Erro de conexão com o banco de dados.")
    st.stop()

def save_data(gid, column, value):
    if isinstance(value, (dict, list)): value = json.dumps(value)
    supabase.table("eco_data").upsert({"group_id": gid, column: str(value)}).execute()

def load_data(gid):
    res = supabase.table("eco_data").select("*").eq("group_id", gid).execute()
    if res.data:
        row = res.data[0]
        for col in ['porter', 'dre', 'wacc', 'swot', 'participants', 'company_info', 'diary']:
            row[col] = safe_json(row.get(col))
        return row
    return {'group_id': gid, 'porter': {}, 'dre': {}, 'wacc': {}, 'swot': {}, 'hhi': '0', 'diary': {}, 'participants': {}, 'company_info': {}, 'feedback': ''}

# --- FUNÇÃO DE IA (CORREÇÃO) ---
def ia_corrigir_trabalho(dados):
    if "OPENAI_API_KEY" not in st.secrets: return "Chave da OpenAI não configurada."
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    
    prompt = f"""
    Como um Professor de Economia, analise estes dados de consultoria:
    EMPRESA: {dados.get('company_info', {}).get('nome')}
    SWOT - Forças: {dados.get('swot', {}).get('f')}
    FINANCEIRO - ROI: {dados.get('wacc', {}).get('roi')}% | WACC: {dados.get('wacc', {}).get('wacc_final')}%
    
    FORNEÇA:
    1. Crítica técnica da SWOT.
    2. Análise da viabilidade financeira (ROI vs WACC).
    3. Sugestão de melhoria para o relatório.
    Seja formal e pedagógico.
    """
    try:
        response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content
    except Exception as e: return f"Erro na IA: {e}"

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h2 style='text-align: center; color: #0f172a; padding-top: 50px;'>ECOSTRATEGY INTELLIGENCE</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.6, 1])
    with col_l2:
        try: st.image("logo.png", use_container_width=True)
        except: pass
        group_input = st.selectbox("Unidade de Consultoria", ["Grupo 1", "Grupo 2", "Grupo 3", "Professor (Acesso Mestre)"])
        pwd_input = st.text_input("Chave de Acesso", type="password")
        
        if st.button("Acessar Plataforma"):
            passwords = st.secrets.get("GROUP_PASSWORDS", {})
            dev_pwd = st.secrets.get("DEV_PASSWORD")
            
            if pwd_input == passwords.get(group_input) or pwd_input == dev_pwd:
                st.session_state.auth = True
                st.session_state.group = group_input
                st.session_state.is_teacher = (pwd_input == dev_pwd)
                st.rerun()
            else: st.error("Acesso negado.")
    st.stop()

# --- CARREGAR DADOS ---
# Se for professor, ele carrega o Grupo 1 por padrão para começar
grupo_atual = st.session_state.group if not st.session_state.is_teacher else "Grupo 1"
data = load_data(grupo_atual)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h2>{st.session_state.group.upper()}</h2>", unsafe_allow_html=True)
    st.divider()
    selic_meta = get_live_selic()
    st.caption(f"Taxa Selic Oficial: {selic_meta}%")
    selic_ref = st.number_input("Benchmark Trabalho (%)", value=selic_meta, step=0.25)
    
    opcoes_menu = [
        "01 DASHBOARD EXECUTIVO", "02 GOVERNANÇA E EQUIPE", "03 PERFIL CORPORATIVO",
        "04 DIAGNÓSTICO DE CAMPO", "05 ANÁLISE ESTRATÉGICA", "06 CENÁRIO MONETÁRIO", 
        "07 VIABILIDADE E VALOR", "08 RELATÓRIO FINAL"
    ]
    if st.session_state.is_teacher:
        opcoes_menu.append("09 PORTAL DO ORIENTADOR")
    
    menu = st.radio("NAVEGAÇÃO", opcoes_menu, label_visibility="collapsed")
    if st.button("Sair"):
        st.session_state.auth = False
        st.rerun()

# --- 1. DASHBOARD (ALUNO VÊ FEEDBACK AQUI) ---
if menu == "01 DASHBOARD EXECUTIVO":
    st.title("Executive Management Dashboard")
    
    # BOX DE FEEDBACK DO PROFESSOR (Aparece se houver conteúdo)
    if data.get('feedback'):
        st.markdown(f"""
        <div style="background-color: #fffbe6; padding: 20px; border-radius: 8px; border: 1px solid #ffe58f; margin-bottom: 20px;">
            <h4 style="color: #856404; margin-top: 0;">📬 Comentários do Orientador</h4>
            <p style="color: #856404;">{data.get('feedback')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.info(f"Unidade: {data.get('company_info',{}).get('nome', 'Pendente')}")
    # ... (Restante dos gráficos de semáforo e gauge que já tínhamos)

# --- 9. PORTAL DO ORIENTADOR (EXCLUSIVO) ---
elif menu == "09 PORTAL DO ORIENTADOR":
    st.title("🎓 Portal de Avaliação e IA")
    grupo_alvo = st.selectbox("Selecione o Grupo para Corrigir", ["Grupo 1", "Grupo 2", "Grupo 3"])
    dados_alvo = load_data(grupo_alvo)
    
    st.divider()
    col_ia1, col_ia2 = st.columns(2)
    
    with col_ia1:
        st.subheader("Análise dos Alunos")
        st.write(f"**Empresa:** {dados_alvo.get('company_info', {}).get('nome')}")
        st.write(f"**Membros:** {dados_alvo.get('participants', {}).get('aluno1')}")
        
        if st.button("🤖 Gerar Rascunho via IA"):
            with st.spinner("Analisando dados do grupo..."):
                st.session_state.rascunho_ia = ia_corrigir_trabalho(dados_alvo)
    
    with col_ia2:
        st.subheader("Parecer do Professor")
        # O professor edita o texto da IA aqui
        feedback_final = st.text_area("Edite o feedback antes de liberar:", 
                                      value=st.session_state.get('rascunho_ia', dados_alvo.get('feedback', '')), 
                                      height=350)
        
        if st.button("🚀 Liberar Feedback para o Grupo"):
            supabase.table("eco_data").update({"feedback": feedback_final}).eq("group_id", grupo_alvo).execute()
            st.success(f"O {grupo_alvo} já pode ler seus comentários!")

# ... (MANTENHA OS OUTROS MENUS 02 A 08 EXATAMENTE COMO ESTAVAM)
