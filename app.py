import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EcoStrategy Hub - Professional", layout="wide")

# --- OCULTAR ELEMENTOS DO STREAMLIT (GITHUB, MENU, FOOTER) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    /* Cores e fontes */
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 1px solid #e0e0e0; }
    h1, h2, h3 { color: #002e5d; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
    .risk-card { padding: 20px; border-radius: 10px; text-align: center; color: white; font-weight: bold; margin-bottom: 10px; border: 1px solid rgba(0,0,0,0.1); }
    .insight-box { background-color: #ffffff; padding: 20px; border-left: 5px solid #0052cc; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .stButton>button { background-color: #0052cc; color: white; border-radius: 4px; width: 100%; font-weight: bold; height: 45px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO SUPABASE ---
try:
    URL: str = st.secrets["SUPABASE_URL"]
    KEY: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("Erro Crítico: Chaves do Supabase não encontradas nos Secrets.")
    st.stop()

# --- FUNÇÕES DE SEGURANÇA ---
def safe_float(val, default=0.0):
    if val is None: return default
    try: return float(val)
    except: return default

def safe_json(val):
    if val is None or val == "": return {}
    if isinstance(val, dict): return val
    try: return json.loads(val)
    except: return {}

def save_data(gid, column, value):
    if isinstance(value, (dict, list)): value = json.dumps(value)
    supabase.table("eco_data").upsert({"group_id": gid, column: str(value)}).execute()

def load_data(gid):
    try:
        res = supabase.table("eco_data").select("*").eq("group_id", gid).execute()
        if res.data:
            row = res.data[0]
            row['porter'] = safe_json(row.get('porter'))
            row['dre'] = safe_json(row.get('dre'))
            row['wacc'] = safe_json(row.get('wacc'))
            return row
        return {'group_id': gid, 'participants': '', 'company_info': '', 'diary': '', 'hhi': '0', 'porter': {}, 'dre': {}, 'wacc': {}}
    except: return {}

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    st.subheader("Login de Consultoria")
    col_l1, col_l2 = st.columns([1, 2])
    with col_l1:
        group = st.selectbox("Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
        pwd = st.text_input("Senha", type="password")
        if st.button("Acessar Dashboard"):
            if pwd == "eco123":
                st.session_state.auth, st.session_state.group = True, group
                st.rerun()
            else: st.error("Senha incorreta.")
    st.stop()

# CARREGAR DADOS
data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    st.header("⚙️ Configurações Macro")
    selic_global = st.number_input("Taxa Selic Atual (%)", value=10.75, step=0.25)
    
    menu = st.radio("NAVEGAÇÃO", [
        "Dashboard Executivo", 
        "Identificação", 
        "Diário de Bordo (Campo)", 
        "Estratégia (Micro)", 
        "Monetário (Macro)", 
        "Financeiro (WACC/EVA)", 
        "Relatório Final"
    ])
    st.divider()
    st.caption("EcoStrategy Hub v2.5 - Professional")

# --- 1. DASHBOARD EXECUTIVO (CORRIGIDO) ---
if menu == "Dashboard Executivo":
    st.title("📈 Dashboard Executivo de Consultoria")
    
    comp_name = data.get('company_info', 'Empresa Não Definida')
    st.markdown(f'<div class="insight-box"><h4>Bem-vindo ao projeto: {comp_name}</h4><p>Este dashboard resume os principais indicadores de risco e viabilidade do seu cliente.</p></div>', unsafe_allow_html=True)
    
    # Cálculos para os Semáforos
    dre = data.get('dre', {})
    ebitda = safe_float(dre.get('receita')) - safe_float(dre.get('custos'))
    divida = safe_float(dre.get('divida'))
    break_even = (ebitda / divida * 100) if divida > 0 else 0
    
    hhi_val = 0
    try: hhi_val = sum([float(x)**2 for x in str(data.get('hhi', '0')).split(",") if x.strip()])
    except: hhi_val = 0

    w_obj = data.get('wacc', {})
    roi = safe_float(w_obj.get('roi'))
    w_val = safe_float(w_obj.get('wacc_final', 15.0))

    col1, col2, col3 = st.columns(3)
    with col1:
        color = "#28a745" if selic_global < break_even else "#dc3545" if break_even > 0 else "#6c757d"
        st.markdown(f'<div class="risk-card" style="background:{color}">RISCO DE CRÉDITO<br>Ruptura Selic: {break_even:.1f}%</div>', unsafe_allow_html=True)
        st.caption("Verde se Selic < Ponto de Ruptura da DRE.")

    with col2:
        m_color = "#28a745" if hhi_val < 1500 else "#ffc107" if hhi_val < 2500 else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{m_color}">RISCO DE MERCADO<br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
        st.caption("Verde se mercado for competitivo (HHI < 1500).")

    with col3:
        v_color = "#28a745" if roi > w_val else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{v_color}">CRIAÇÃO DE VALOR<br>ROI: {roi}%</div>', unsafe_allow_html=True)
        st.caption("Verde se ROI > WACC (Lucro Econômico).")

    st.divider()
    st.subheader("📋 Resumo de Preenchimento")
    st.write(f"- **Identificação:** {'✅ Concluído' if data.get('company_info') else '❌ Pendente'}")
    st.write(f"- **Diário de Bordo:** {'✅ Concluído' if data.get('diary') else '❌ Pendente'}")
    st.write(f"- **Análise de Porter:** {'✅ Concluído' if data.get('porter') else '❌ Pendente'}")
    st.write(f"- **Análise Monetária:** {'✅ Concluído' if data.get('dre') else '❌ Pendente'}")

# --- 2. IDENTIFICAÇÃO ---
elif menu == "Identificação":
    st.title("👥 Identificação do Projeto")
    with st.form("f_id"):
        membros = st.text_area("Integrantes do Grupo", value=data.get('participants', ''))
        empresa = st.text_input("Nome da Empresa Analisada", value=data.get('company_info', ''))
        if st.form_submit_button("Salvar Identificação"):
            save_data(st.session_state.group, "participants", membros)
            save_data(st.session_state.group, "company_info", empresa)
            st.success("Dados salvos!")
            st.rerun()

# --- 3. DIÁRIO DE BORDO ---
elif menu == "Diário de Bordo (Campo)":
    st.title("📔 Diário de Bordo")
    notas = st.text_area("Registro qualitativo das visitas e entrevistas", value=data.get('diary', ''), height=400)
    if st.button("Salvar Diário"):
        save_data(st.session_state.group, "diary", notas)
        st.success("Diário atualizado!")

# --- 4. ESTRATÉGIA (MICRO) ---
elif menu == "Estratégia (Micro)":
    st.title("🔬 Análise Microeconômica")
    t1, t2 = st.tabs(["5 Forças de Porter", "Cálculo HHI"])
    with t1:
        p = data.get('porter', {})
        c1, c2 = st.columns(2)
        p1 = c1.slider("Entrantes", 1, 5, int(p.get('p1', 3)))
        p2 = c1.slider("Fornecedores", 1, 5, int(p.get('p2', 3)))
        p3 = c1.slider("Clientes", 1, 5, int(p.get('p3', 3)))
        p4 = c2.slider("Substitutos", 1, 5, int(p.get('p4', 3)))
        p5 = c2.slider("Rivalidade", 1, 5, int(p.get('p5', 3)))
        if st.button("Salvar Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1,"p2":p2,"p3":p3,"p4":p4,"p5":p5})
            st.success("Salvo!")
    with t2:
        h_in = st.text_input("Market Shares (ex: 40,30,20)", value=data.get('hhi', ''))
        if h_in:
            try:
                sh = [float(x.strip()) for x in h_in.split(",") if x.strip()]
                hhi_val = sum([v**2 for v in sh])
                st.metric("Índice HHI", int(hhi_val))
                st.plotly_chart(px.pie(values=sh, names=[f"E{i+1}" for i in range(len(sh))], hole=0.4))
                if hhi_val > 2500: st.warning("ALERTA: Oligopólio Detectado.")
            except: st.error("Erro no formato.")
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", h_in)

# --- 5. MONETÁRIO (MACRO) ---
elif menu == "Monetário (Macro)":
    st.title("🏦 Monetário e Stress Test")
    dre = data.get('dre', {})
    c1, c2 = st.columns([1, 2])
    with c1:
        r = st.number_input("Receita Bruta", value=safe_float(dre.get('receita', 1000000)))
        c = st.number_input("Custos", value=safe_float(dre.get('custos', 700000)))
        d = st.number_input("Dívida", value=safe_float(dre.get('divida', 400000)))
        if st.button("Salvar DRE"):
            save_data(st.session_state.group, "dre", {"receita":r, "custos":c, "divida":d})
            st.rerun()
    with c2:
        ebitda = r - c
        sim = st.slider("Simular Selic %", 0.0, 30.0, selic_global)
        st.metric("Lucro Líquido Estimado", f"R$ {ebitda - (d * sim/100):,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (d * s/100) for s in range(0,31)], title="Ponto de Ruptura (Lucro Zero)")
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig)

# --- 6. FINANCEIRO (WACC/EVA) ---
elif menu == "Financeiro (WACC/EVA)":
    st.title("💰 Viabilidade Econômica")
    w = data.get('wacc', {})
    c1, c2 = st.columns(2)
    with c1:
        ke = st.number_input("Ke %", value=safe_float(w.get('ke', 15)))
        kd = st.number_input("Kd %", value=safe_float(w.get('kd', 12)))
        eq = st.slider("Equity Ratio %", 0, 100, int(safe_float(w.get('eq_ratio', 60)))) / 100
        wacc_calc = (eq * (ke/100)) + ((1 - eq) * (kd/100) * 0.66)
        st.metric("WACC Final", f"{wacc_calc*100:.2f}%")
    with c2:
        roi = st.number_input("ROI Atual %", value=safe_float(w.get('roi', 18)))
        eva = roi - (selic_global + 5.0)
        st.metric("EVA (ROI vs Selic+Risk)", f"{eva:.2f}%")
        if st.button("Salvar Financeiro"):
            save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":wacc_calc*100})

# --- 7. RELATÓRIO ---
elif menu == "Relatório Final":
    st.title("📄 Relatório Consolidado")
    st.write(f"Empresa: {data.get('company_info')} | Grupo: {st.session_state.group}")
    st.divider()
    st.subheader("Diário de Bordo")
    st.info(data.get('diary', 'Nenhuma nota registrada.'))
    st.button("Imprimir (Ctrl+P)")
