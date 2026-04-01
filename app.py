import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Hub", layout="wide", initial_sidebar_state="expanded")

# --- CSS WHITELABEL PROFISSIONAL (Esconde Streamlit, mantém Menu) ---
st.markdown("""
    <style>
    /* Esconde botões de desenvolvedor e marca d'água */
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    
    /* Cores e Design Elite */
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 1px solid #e0e0e0; min-width: 280px !important; }
    h1, h2, h3 { color: #002e5d; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
    
    /* Semáforos do Dashboard */
    .risk-card { padding: 20px; border-radius: 12px; text-align: center; color: white; font-weight: bold; margin-bottom: 10px; border: 1px solid rgba(0,0,0,0.1); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .insight-box { background-color: #ffffff; padding: 20px; border-left: 6px solid #0052cc; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
    
    /* Botões Customizados */
    .stButton>button { background-color: #0052cc; color: white; border-radius: 6px; width: 100%; font-weight: bold; height: 50px; border: none; transition: 0.3s; }
    .stButton>button:hover { background-color: #003d99; box-shadow: 0 4px 12px rgba(0,82,204,0.3); }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO SUPABASE ---
try:
    URL: str = st.secrets["SUPABASE_URL"]
    KEY: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("Erro Crítico: Chaves do Supabase não configuradas nos Secrets.")
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
            # Converte colunas JSON de volta para dicionários
            row['porter'] = safe_json(row.get('porter'))
            row['dre'] = safe_json(row.get('dre'))
            row['wacc'] = safe_json(row.get('wacc'))
            return row
        return {'group_id': gid, 'participants': '', 'company_info': '', 'company_desc': '', 'diary': '', 'hhi': '0', 'porter': {}, 'dre': {}, 'wacc': {}}
    except: return {}

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False

if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    st.subheader("Acesso à Plataforma de Consultoria")
    col_l1, col_l2 = st.columns([1, 2])
    with col_l1:
        group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
        pwd = st.text_input("Senha", type="password")
        if st.button("Entrar no Hub"):
            if pwd == "eco123":
                st.session_state.auth, st.session_state.group = True, group
                st.rerun()
            else: st.error("Senha incorreta.")
    st.stop()

# CARREGAR DADOS DO BANCO
data = load_data(st.session_state.group)

# --- SIDEBAR (Sempre Visível) ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    st.header("⚙️ Variáveis Macro")
    selic_global = st.number_input("Taxa Selic Atual (%)", value=10.75, step=0.25, help="Define a base para todos os cálculos de Stress Test e EVA.")
    
    st.divider()
    menu = st.radio("NAVEGAÇÃO", [
        "1. Dashboard Executivo", 
        "2. Identificação e Empresa", 
        "3. Diário de Bordo (Campo)", 
        "4. Análise Micro (Estratégia)", 
        "5. Análise Macro (Monetário)", 
        "6. Financeiro (WACC & EVA)", 
        "7. Relatório Final"
    ])
    st.divider()
    if st.button("Sair (Logout)"):
        st.session_state.auth = False
        st.rerun()

# --- 1. DASHBOARD EXECUTIVO ---
if menu == "1. Dashboard Executivo":
    st.title("📈 Dashboard Executivo")
    comp_name = data.get('company_info', 'Empresa Não Definida')
    st.markdown(f'<div class="insight-box"><h4>Consultoria para: {comp_name}</h4><p>Resumo de riscos e performance baseados nos módulos preenchidos.</p></div>', unsafe_allow_html=True)
    
    # Lógica Intelligence
    dre_d = data.get('dre', {})
    ebitda = safe_float(dre_d.get('receita')) - safe_float(dre_d.get('custos'))
    divida = safe_float(dre_d.get('divida'))
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
        st.markdown(f'<div class="risk-card" style="background:{color}">RISCO CRÉDITO<br>Ruptura Selic: {break_even:.1f}%</div>', unsafe_allow_html=True)
    with col2:
        m_color = "#28a745" if hhi_val < 1500 else "#ffc107" if hhi_val < 2500 else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{m_color}">RISCO MERCADO<br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
    with col3:
        v_color = "#28a745" if roi > (selic_global + 5) else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{v_color}">VALOR (EVA)<br>ROI: {roi}%</div>', unsafe_allow_html=True)

# --- 2. IDENTIFICAÇÃO ---
elif menu == "2. Identificação e Empresa":
    st.title("👥 Identificação do Projeto")
    with st.form("f_ident"):
        membros = st.text_area("Integrantes do Grupo", value=data.get('participants', ''))
        empresa = st.text_input("Nome da Empresa Analisada", value=data.get('company_info', ''))
        desc = st.text_area("Descrição do Modelo de Negócio", value=data.get('company_desc', ''))
        if st.form_submit_button("Salvar Identificação"):
            save_data(st.session_state.group, "participants", membros)
            save_data(st.session_state.group, "company_info", empresa)
            save_data(st.session_state.group, "company_desc", desc)
            st.success("Dados salvos!")
            st.rerun()

# --- 3. DIÁRIO DE BORDO ---
elif menu == "3. Diário de Bordo (Campo)":
    st.title("📔 Diário de Bordo")
    notas = st.text_area("Registro qualitativo das visitas técnicas e entrevistas", value=data.get('diary', ''), height=450)
    if st.button("Sincronizar Diário"):
        save_data(st.session_state.group, "diary", notas)
        st.success("Diário salvo no Supabase!")

# --- 4. MICRO ---
elif menu == "4. Análise Micro (Estratégia)":
    st.title("🔬 Estratégia Microeconômica")
    t1, t2 = st.tabs(["Matriz de Porter", "Concentração (HHI)"])
    with t1:
        p = data.get('porter', {})
        c1, c2 = st.columns(2)
        p1 = c1.slider("Entrantes", 1, 5, int(p.get('p1', 3)))
        p2 = c1.slider("Fornecedores", 1, 5, int(p.get('p2', 3)))
        p3 = c1.slider("Clientes", 1, 5, int(p.get('p3', 3)))
        p4 = c2.slider("Substitutos", 1, 5, int(p.get('p4', 3)))
        p5 = c2.slider("Rivalidade", 1, 5, int(p.get('p5', 3)))
        if st.button("Salvar Matriz Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1,"p2":p2,"p3":p3,"p4":p4,"p5":p5})
            st.success("Matriz Salva!")
    with t2:
        h_in = st.text_input("Market Shares (ex: 40,30,20)", value=data.get('hhi', ''))
        if h_in:
            try:
                sh = [float(x.strip()) for x in h_in.split(",") if x.strip()]
                h_val = sum([v**2 for v in sh])
                st.metric("Índice HHI", int(h_val))
                st.plotly_chart(px.pie(values=sh, hole=0.4, title="Estrutura de Mercado"))
                if h_val > 2500: st.warning("Oligopólio: Alto Pricing Power.")
            except: st.error("Erro no formato das shares.")
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", h_in)

# --- 5. MACRO ---
elif menu == "5. Análise Macro (Monetário)":
    st.title("🏦 Monetário e Stress Test")
    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("DRE Simplificada")
        r = st.number_input("Receita Bruta", value=safe_float(dre_d.get('receita', 1000000)))
        c = st.number_input("Custos Operacionais", value=safe_float(dre_d.get('custos', 700000)))
        d = st.number_input("Dívida Bancária", value=safe_float(dre_d.get('divida', 400000)))
        if st.button("Salvar DRE"):
            save_data(st.session_state.group, "dre", {"receita":r, "custos":c, "divida":d})
            st.success("DRE Salva!")
            st.rerun()
    with c2:
        ebitda = r - c
        sim = st.slider("Simular Selic %", 0.0, 30.0, selic_global)
        st.metric("Lucro Estimado", f"R$ {ebitda - (d * sim/100):,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (d * s/100) for s in range(0,31)], title="Ponto de Ruptura (EBITDA vs Juros)")
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig)

# --- 6. FINANCEIRO ---
elif menu == "6. Financeiro (WACC & EVA)":
    st.title("💰 Viabilidade Econômica")
    w_d = data.get('wacc', {})
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Cálculo do WACC")
        ke = st.number_input("Ke %", value=safe_float(w_d.get('ke', 15)))
        kd = st.number_input("Kd %", value=safe_float(w_d.get('kd', 12)))
        eq = st.slider("Equity Ratio %", 0, 100, int(safe_float(w_d.get('eq_ratio', 60)))) / 100
        w_calc = (eq * (ke/100)) + ((1 - eq) * (kd/100) * 0.66)
        st.metric("WACC Final", f"{w_calc*100:.2f}%")
    with c2:
        st.subheader("Análise EVA")
        roi = st.number_input("ROI Atual %", value=safe_float(w_d.get('roi', 18)))
        eva = roi - (selic_global + 5.0)
        st.metric("EVA (ROI vs Selic+Risk)", f"{eva:.2f}%")
        if st.button("Salvar Dados Financeiros"):
            save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":w_calc*100})

# --- 7. RELATÓRIO ---
elif menu == "7. Relatório Final":
    st.title("📄 Relatório Consolidado")
    st.write(f"**Empresa:** {data.get('company_info')} | **Grupo:** {st.session_state.group}")
    st.divider()
    st.subheader("Sumário do Diário de Bordo")
    st.info(data.get('diary', 'Nenhum registro encontrado.'))
    st.subheader("Análises Realizadas")
    st.write("- Matriz de Porter e HHI Setorial")
    st.write("- Stress Test Monetário e Ruptura Selic")
    st.write("- Cálculo de WACC e Economic Value Added (EVA)")
    st.button("Exportar / Imprimir Relatório (Ctrl+P)")
