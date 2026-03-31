import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="EcoStrategy Hub", layout="wide")

# --- CONEXÃO ---
try:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Erro nas chaves do Supabase nos Secrets.")
    st.stop()

# --- FUNÇÕES DE SEGURANÇA (Para não dar erro de tipo) ---
def safe_float(val, default=0.0):
    try: return float(val)
    except: return default

def safe_json(val):
    if not val: return {}
    if isinstance(val, dict): return val
    try: return json.loads(val)
    except: return {}

# --- PERSISTÊNCIA ---
def save_data(gid, column, value):
    if isinstance(value, (dict, list)): value = json.dumps(value)
    supabase.table("eco_data").upsert({"group_id": gid, column: str(value)}).execute()

def load_data(gid):
    try:
        res = supabase.table("eco_data").select("*").eq("group_id", gid).execute()
        if res.data: return res.data[0]
        return {}
    except: return {}

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    group = st.selectbox("Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
    if st.text_input("Senha", type="password") == "eco123" and st.button("Entrar"):
        st.session_state.auth, st.session_state.group = True, group
        st.rerun()
    st.stop()

# Carregar dados
data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    menu = st.radio("NAVEGAÇÃO", ["Dashboard de Riscos", "Caracterização", "Estratégia (Micro)", "Monetário (Macro)", "Financeiro", "Relatório"])

# --- 1. DASHBOARD DE RISCOS ---
if menu == "Dashboard de Riscos":
    st.title("🚦 Intelligence Risk Dashboard")
    
    dre = safe_json(data.get('dre'))
    ebitda = safe_float(dre.get('receita')) - safe_float(dre.get('custos'))
    divida = safe_float(dre.get('divida'))
    selic_atual = 10.75
    break_even = (ebitda / divida * 100) if divida > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Risco de Crédito")
        color = "#28a745" if selic_atual < break_even else "#dc3545"
        st.markdown(f'<div style="background:{color};padding:20px;border-radius:10px;color:white;text-align:center">SELIC: {selic_atual}%<br>Ruptura: {break_even:.1f}%</div>', unsafe_allow_html=True)
    
    st.info("Preencha os dados nas abas de Estratégia e Monetário para atualizar este dashboard.")

# --- 2. CARACTERIZAÇÃO ---
elif menu == "Caracterização":
    st.title("👥 Identificação")
    with st.form("f1"):
        membros = st.text_area("Membros", value=data.get('participants', ''))
        empresa = st.text_input("Empresa", value=data.get('company_info', ''))
        if st.form_submit_button("Salvar"):
            save_data(st.session_state.group, "participants", membros)
            save_data(st.session_state.group, "company_info", empresa)
            st.success("Salvo!")
            st.rerun()

# --- 3. ESTRATÉGIA (MICRO) ---
elif menu == "Estratégia (Micro)":
    st.title("🔬 Análise Micro")
    shares_input = st.text_input("HHI - Shares (ex: 40,30,10)", value=data.get('hhi', ''))
    if st.button("Salvar HHI"):
        save_data(st.session_state.group, "hhi", shares_input)
        st.rerun()
    
    if shares_input:
        try:
            vals = [float(x) for x in shares_input.split(",")]
            st.plotly_chart(px.pie(values=vals, names=[f"E{i+1}" for i in range(len(vals))]))
        except: st.error("Use apenas números e vírgulas.")

# --- 4. MONETÁRIO (MACRO) ---
elif menu == "Monetário (Macro)":
    st.title("🏦 Monetário e Stress Test")
    dre = safe_json(data.get('dre'))
    with st.form("f2"):
        rec = st.number_input("Receita", value=safe_float(dre.get('receita')))
        cus = st.number_input("Custos", value=safe_float(dre.get('custos')))
        div = st.number_input("Dívida", value=safe_float(dre.get('divida')))
        if st.form_submit_button("Salvar DRE"):
            save_data(st.session_state.group, "dre", {"receita":rec, "custos":cus, "divida":div})
            st.rerun()
    
    ebitda = rec - cus
    s_sim = st.slider("Simular Selic %", 0.0, 25.0, 10.75)
    lucro = ebitda - (div * s_sim/100)
    st.metric("Lucro Estimado", f"R$ {lucro:,.2f}")

# --- 5. FINANCEIRO ---
elif menu == "Financeiro":
    st.title("💰 Financeiro")
    w_data = safe_json(data.get('wacc'))
    with st.form("f3"):
        roi = st.number_input("ROI %", value=safe_float(w_data.get('roi')))
        if st.form_submit_button("Salvar ROI"):
            save_data(st.session_state.group, "wacc", {"roi":roi})
            st.rerun()
    st.write(f"O ROI atual é de {roi}%")

# --- 6. RELATÓRIO ---
elif menu == "Relatório":
    st.title("📄 Relatório Final")
    st.write(f"Empresa: {data.get('company_info')}")
    st.write(f"Membros: {data.get('participants')}")
