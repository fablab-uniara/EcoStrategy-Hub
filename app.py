import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Hub - Intelligence Elite", layout="wide", initial_sidebar_state="expanded")

# --- CSS WHITELABEL PROFISSIONAL ---
st.markdown("""
    <style>
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 1px solid #e0e0e0; min-width: 280px !important; }
    h1, h2, h3 { color: #002e5d; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
    .risk-card { padding: 20px; border-radius: 12px; text-align: center; color: white; font-weight: bold; margin-bottom: 10px; border: 1px solid rgba(0,0,0,0.1); }
    .insight-box { background-color: #ffffff; padding: 20px; border-left: 6px solid #0052cc; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
    .swot-card { padding: 15px; border-radius: 8px; height: 150px; color: white; font-size: 0.9em; overflow-y: auto; }
    .stButton>button { background-color: #0052cc; color: white; border-radius: 6px; width: 100%; font-weight: bold; height: 45px; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO SUPABASE ---
try:
    URL: str = st.secrets["SUPABASE_URL"]
    KEY: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("Erro Crítico: Chaves do Supabase não configuradas.")
    st.stop()

# --- FUNÇÕES DE SEGURANÇA ---
def safe_float(val, default=0.0):
    if val is None: return default
    try: return float(val)
    except: return default

def safe_json(val):
    if val is None or val == "" or val == "None": return {}
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
            for col in ['porter', 'dre', 'wacc', 'swot']:
                row[col] = safe_json(row.get(col))
            return row
        return {'group_id': gid, 'porter': {}, 'dre': {}, 'wacc': {}, 'swot': {}, 'hhi': '0'}
    except: return {}

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    st.subheader("Login de Consultoria")
    col_l1, col_l2 = st.columns([1, 2])
    with col_l1:
        group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
        if st.text_input("Senha", type="password") == "eco123" and st.button("Acessar"):
            st.session_state.auth, st.session_state.group = True, group
            st.rerun()
    st.stop()

data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    st.header("⚙️ Variáveis Macro")
    selic_ref = st.number_input("Selic de Referência (%)", value=10.75, step=0.25)
    
    menu = st.radio("NAVEGAÇÃO", [
        "1. Dashboard Executivo", 
        "2. Identificação e Empresa", 
        "3. Diário de Bordo (Campo)", 
        "4. Módulo Micro (Porter/HHI/SWOT)", 
        "5. Módulo Macro (Monetário)", 
        "6. Módulo Financeiro (WACC/Valuation)", 
        "7. Relatório Final"
    ])
    st.divider()
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# --- 1. DASHBOARD EXECUTIVO ---
if menu == "1. Dashboard Executivo":
    st.title("📈 Dashboard Executivo")
    dre_d = data.get('dre', {})
    ebitda = safe_float(dre_d.get('receita')) - safe_float(dre_d.get('custos'))
    divida = safe_float(dre_d.get('divida'))
    idx_total = safe_float(dre_d.get('idx_valor')) + safe_float(dre_d.get('spread'))
    break_even = (ebitda / divida * 100) if divida > 0 else 0

    hhi_val = 0
    try: hhi_val = sum([float(x)**2 for x in str(data.get('hhi', '0')).split(",") if x.strip()])
    except: hhi_val = 0

    w_d = data.get('wacc', {})
    roi = safe_float(w_d.get('roi'))
    w_final = safe_float(w_d.get('wacc_final', 15.0))

    col1, col2, col3 = st.columns(3)
    with col1:
        c = "#28a745" if idx_total < (ebitda/divida*100 if divida > 0 else 100) else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{c}">RISCO CRÉDITO<br>Taxa: {idx_total:.2f}%</div>', unsafe_allow_html=True)
    with col2:
        mc = "#28a745" if hhi_val < 1500 else "#ffc107" if hhi_val < 2500 else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{mc}">RISCO MERCADO<br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
    with col3:
        vc = "#28a745" if roi > w_final else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{vc}">CRIAÇÃO VALOR<br>ROI: {roi}%</div>', unsafe_allow_html=True)

# --- 2. IDENTIFICAÇÃO ---
elif menu == "2. Identificação e Empresa":
    st.title("👥 Identificação")
    with st.form("f_id"):
        membros = st.text_area("Integrantes", value=data.get('participants', ''))
        empresa = st.text_input("Empresa", value=data.get('company_info', ''))
        desc = st.text_area("Descrição", value=data.get('company_desc', ''))
        if st.form_submit_button("Salvar"):
            save_data(st.session_state.group, "participants", membros)
            save_data(st.session_state.group, "company_info", empresa)
            save_data(st.session_state.group, "company_desc", desc)
            st.success("Salvo!")

# --- 3. DIÁRIO DE BORDO ---
elif menu == "3. Diário de Bordo (Campo)":
    st.title("📔 Diário de Bordo")
    notas = st.text_area("Notas das Visitas", value=data.get('diary', ''), height=400)
    if st.button("Sincronizar"):
        save_data(st.session_state.group, "diary", notas)
        st.success("Sincronizado!")

# --- 4. MÓDULO MICRO (ADICIONADO SWOT) ---
elif menu == "4. Módulo Micro (Porter/HHI/SWOT)":
    st.title("🔬 Análise Microeconômica e Estratégica")
    t1, t2, t3 = st.tabs(["Matriz de Porter", "HHI", "Matriz SWOT (FOFA)"])
    
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
            st.success("Matriz Salva!")

    with t2:
        h_in = st.text_input("Shares (ex: 40,30,20)", value=data.get('hhi', ''))
        if h_in:
            try:
                sh = [float(x.strip()) for x in h_in.split(",") if x.strip()]
                h_val = sum([v**2 for v in sh])
                st.metric("HHI", int(h_val))
                st.plotly_chart(px.pie(values=sh, names=[f"E{i+1}" for i in range(len(sh))], hole=0.4))
            except: st.error("Erro no formato.")
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", h_in)

    with t3:
        sw = data.get('swot', {})
        st.subheader("Matriz FOFA Interativa")
        with st.form("f_swot"):
            c1, c2 = st.columns(2)
            f = c1.text_area("Forças (Strengths)", value=sw.get('f', ''))
            o = c1.text_area("Oportunidades (Opportunities)", value=sw.get('o', ''))
            fra = c2.text_area("Fraquezas (Weaknesses)", value=sw.get('fra', ''))
            a = c2.text_area("Ameaças (Threats)", value=sw.get('a', ''))
            if st.form_submit_button("Salvar SWOT"):
                save_data(st.session_state.group, "swot", {"f":f, "fra":fra, "o":o, "a":a})
                st.rerun()
        
        st.markdown("### Visualização Estratégica")
        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="swot-card" style="background:#28a745"><b>FORÇAS</b><br>{f}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="swot-card" style="background:#dc3545"><b>FRAQUEZAS</b><br>{fra}</div>', unsafe_allow_html=True)
        c1.markdown(f'<div class="swot-card" style="background:#0052cc; margin-top:10px"><b>OPORTUNIDADES</b><br>{o}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="swot-card" style="background:#ffc107; color:black; margin-top:10px"><b>AMEAÇAS</b><br>{a}</div>', unsafe_allow_html=True)

# --- 5. MONETÁRIO ---
elif menu == "5. Módulo Macro (Monetário)":
    st.title("🏦 Monetário e Indexadores")
    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_nome = st.selectbox("Indexador", ["Selic", "TJLP", "IGP-M", "IPCA", "Outro"], index=0)
        idx_val = st.number_input(f"Valor do {idx_nome} (%)", value=safe_float(dre_d.get('idx_valor', 10.75)))
        spread = st.number_input("Spread (+%)", value=safe_float(dre_d.get('spread', 2.0)))
        rec = st.number_input("Receita Bruta", value=safe_float(dre_d.get('receita', 1000000)))
        cus = st.number_input("Custos Operacionais", value=safe_float(dre_d.get('custos', 700000)))
        div = st.number_input("Dívida Total", value=safe_float(dre_d.get('divida', 400000)))
        if st.button("Salvar Macro"):
            save_data(st.session_state.group, "dre", {"idx_nome":idx_nome, "idx_valor":idx_val, "spread":spread, "receita":rec, "custos":cus, "divida":div})
            st.rerun()
    with c2:
        ebitda = rec - cus
        sim = st.slider(f"Simular {idx_nome} %", 0.0, 30.0, idx_val)
        st.metric("Lucro Estimado", f"R$ {ebitda - (div*(sim+spread)/100):,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div*(s+spread)/100) for s in range(0,31)], title="Análise de Ruptura")
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig)

# --- 6. MÓDULO FINANCEIRO (ADICIONADO VALUATION) ---
elif menu == "6. Módulo Financeiro (WACC/Valuation)":
    st.title("💰 Viabilidade e Valuation")
    tab1, tab2 = st.tabs(["WACC & EVA", "Simulador de Valuation (DCF)"])
    
    with tab1:
        w_d = data.get('wacc', {})
        c1, c2 = st.columns(2)
        with c1:
            ke = st.number_input("Ke %", value=safe_float(w_d.get('ke', 15)))
            kd = st.number_input("Kd %", value=safe_float(w_d.get('kd', 12)))
            eq = st.slider("Equity %", 0, 100, int(safe_float(w_d.get('eq_ratio', 60)))) / 100
            w_calc = (eq * (ke/100)) + ((1 - eq) * (kd/100) * 0.66)
            st.metric("WACC Final", f"{w_calc*100:.2f}%")
        with c2:
            roi = st.number_input("ROI %", value=safe_float(w_d.get('roi', 18)))
            eva = roi - (selic_ref + 5.0)
            st.metric("EVA", f"{eva:.2f}%")
            if st.button("Salvar Financeiro"):
                save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":w_calc*100})

    with tab2:
        st.subheader("Simulador de Valor da Empresa (Perpetuidade)")
        st.write("Baseado no EBITDA atual e no WACC calculado anteriormente.")
        dre_d = data.get('dre', {})
        ebitda_base = safe_float(dre_d.get('receita')) - safe_float(dre_d.get('custos'))
        wacc_base = safe_float(w_d.get('wacc_final')) / 100
        
        g = st.slider("Taxa de Crescimento na Perpetuidade (g) %", 0.0, 10.0, 3.0) / 100
        
        if wacc_base > g:
            valuation = (ebitda_base * (1 + g)) / (wacc_base - g)
            st.metric("Enterprise Value (Valor de Mercado)", f"R$ {valuation:,.2f}")
            st.info(f"Fórmula: EBITDA(1+g) / (WACC - g). O valor reflete a capacidade de geração de caixa futura descontada ao presente.")
        else:
            st.error("Erro Matemático: O WACC deve ser maior que o Crescimento (g) para o cálculo de perpetuidade.")

# --- 7. RELATÓRIO ---
elif menu == "7. Relatório Final":
    st.title("📄 Relatório Consolidado")
    st.write(f"Empresa: {data.get('company_info')} | Grupo: {st.session_state.group}")
    st.divider()
    st.subheader("Matriz SWOT")
    sw = data.get('swot', {})
    st.write(f"**Forças:** {sw.get('f')} | **Fraquezas:** {sw.get('fra')}")
    st.divider()
    st.subheader("Diário de Bordo")
    st.info(data.get('diary', 'Sem registros.'))
    st.button("Imprimir (Ctrl+P)")
