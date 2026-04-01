import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Hub - Professional", layout="wide", initial_sidebar_state="expanded")

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
    .stButton>button { background-color: #0052cc; color: white; border-radius: 6px; width: 100%; font-weight: bold; height: 50px; border: none; }
    .stButton>button:hover { background-color: #003d99; }
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
        return {'group_id': gid, 'participants': '', 'company_info': '', 'company_desc': '', 'diary': '', 'hhi': '0', 'porter': {}, 'dre': {}, 'wacc': {}}
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

# CARREGAR DADOS
data = load_data(st.session_state.group)

# --- SIDEBAR (Configurações Macroeconômicas) ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    st.header("🌍 Conjuntura Global")
    
    # Selic de Referência para Custo de Oportunidade (EVA)
    selic_ref = st.number_input("Selic de Referência (%)", value=10.75, step=0.25, help="Usada para comparar ROI vs Renda Fixa.")
    
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
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# --- 1. DASHBOARD EXECUTIVO ---
if menu == "1. Dashboard Executivo":
    st.title("📈 Dashboard Executivo")
    
    dre_d = data.get('dre', {})
    ebitda = safe_float(dre_d.get('receita')) - safe_float(dre_d.get('custos'))
    divida = safe_float(dre_d.get('divida'))
    
    # Lógica de Risco de Crédito baseada no Indexador escolhido no Módulo Macro
    idx_val = safe_float(dre_d.get('idx_valor', 10.75))
    spread_val = safe_float(dre_d.get('spread', 2.0))
    taxa_total = idx_val + spread_val
    break_even = (ebitda / divida * 100) - spread_val if divida > 0 else 0

    hhi_val = 0
    try: hhi_val = sum([float(x)**2 for x in str(data.get('hhi', '0')).split(",") if x.strip()])
    except: hhi_val = 0

    roi = safe_float(data.get('wacc', {}).get('roi'))
    w_val = safe_float(data.get('wacc', {}).get('wacc_final', 15.0))

    col1, col2, col3 = st.columns(3)
    with col1:
        color = "#28a745" if taxa_total < (ebitda/divida*100 if divida > 0 else 100) else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{color}">RISCO CRÉDITO<br>Taxa Atual: {taxa_total:.2f}%</div>', unsafe_allow_html=True)
    with col2:
        m_color = "#28a745" if hhi_val < 1500 else "#ffc107" if hhi_val < 2500 else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{m_color}">RISCO MERCADO<br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
    with col3:
        v_color = "#28a745" if roi > w_val else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{v_color}">VALOR (EVA)<br>ROI: {roi}%</div>', unsafe_allow_html=True)

# --- 2. IDENTIFICAÇÃO ---
elif menu == "2. Identificação e Empresa":
    st.title("👥 Identificação")
    with st.form("f_ident"):
        membros = st.text_area("Integrantes do Grupo", value=data.get('participants', ''))
        empresa = st.text_input("Nome da Empresa", value=data.get('company_info', ''))
        desc = st.text_area("Modelo de Negócio", value=data.get('company_desc', ''))
        if st.form_submit_button("Salvar"):
            save_data(st.session_state.group, "participants", membros)
            save_data(st.session_state.group, "company_info", empresa)
            save_data(st.session_state.group, "company_desc", desc)
            st.success("Salvo!")

# --- 3. DIÁRIO DE BORDO ---
elif menu == "3. Diário de Bordo (Campo)":
    st.title("📔 Diário de Bordo")
    notas = st.text_area("Notas das Visitas", value=data.get('diary', ''), height=450)
    if st.button("Sincronizar"):
        save_data(st.session_state.group, "diary", notas)
        st.success("Sincronizado!")

# --- 4. MICRO ---
elif menu == "4. Análise Micro (Estratégia)":
    st.title("🔬 Análise Micro")
    tab1, tab2 = st.tabs(["Matriz de Porter", "HHI"])
    with tab1:
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
    with tab2:
        h_in = st.text_input("Market Shares (ex: 40,30,20)", value=data.get('hhi', ''))
        if h_in:
            try:
                sh = [float(x.strip()) for x in h_in.split(",") if x.strip()]
                h_val = sum([v**2 for v in sh])
                st.metric("HHI", int(h_val))
                st.plotly_chart(px.pie(values=sh, names=[f"E{i+1}" for i in range(len(sh))], hole=0.4))
            except: st.error("Erro no formato.")
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", h_in)

# --- 5. MONETÁRIO (MACRO) ---
elif menu == "5. Análise Macro (Monetário)":
    st.title("🏦 Monetário, Indexadores e Stress Test")
    
    with st.expander("🎓 Explicação: Indexadores de Dívida"):
        st.write("""
        Empresas podem se financiar por diferentes taxas. A **Selic** é a base, mas o BNDES usa a **TJLP/TLP**, 
        contratos podem usar o **IGP-M** (inflação do atacado) ou **IPCA** (consumidor). 
        A taxa final é sempre o **Indexador + Spread (Margem de risco do banco)**.
        """)

    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st.subheader("Configuração da Dívida")
        idx_nome = st.selectbox("Indexador da Dívida", ["Selic", "TJLP", "IGP-M", "IPCA", "Outro"], index=0)
        idx_val = st.number_input(f"Valor atual do {idx_nome} (%)", value=safe_float(dre_d.get('idx_valor', 10.75)))
        spread = st.number_input("Spread Bancário (+ % a.a.)", value=safe_float(dre_d.get('spread', 2.0)))
        
        st.divider()
        rec = st.number_input("Receita Bruta", value=safe_float(dre_d.get('receita', 1000000)))
        cus = st.number_input("Custos Operacionais", value=safe_float(dre_d.get('custos', 700000)))
        div = st.number_input("Dívida Total", value=safe_float(dre_d.get('divida', 400000)))
        
        if st.button("Salvar Cenário Macro"):
            save_data(st.session_state.group, "dre", {"idx_nome":idx_nome, "idx_valor":idx_val, "spread":spread, "receita":rec, "custos":cus, "divida":div})
            st.rerun()
            
    with c2:
        taxa_total = idx_val + spread
        ebitda = rec - cus
        st.subheader(f"Stress Test: Variação do {idx_nome}")
        sim_idx = st.slider(f"Simular {idx_nome} (%)", 0.0, 30.0, idx_val)
        
        custo_juros = div * ((sim_idx + spread)/100)
        st.metric(f"Custo Juros ({idx_nome} + {spread}%)", f"R$ {custo_juros:,.2f}")
        st.metric("Lucro Operacional Líquido", f"R$ {ebitda - custo_juros:,.2f}")
        
        # Gráfico de Ruptura
        ss = list(range(0, 31))
        ls = [ebitda - (div * (s + spread)/100) for s in ss]
        fig = px.line(x=ss, y=ls, title=f"Sensibilidade: Lucro vs {idx_nome}", labels={'x':f'{idx_nome} %', 'y':'Lucro'})
        fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Insolvência")
        st.plotly_chart(fig)

# --- 6. FINANCEIRO ---
elif menu == "6. Financeiro (WACC/EVA)":
    st.title("💰 Viabilidade Econômica")
    w_d = data.get('wacc', {})
    dre_d = data.get('dre', {})
    
    # Busca a taxa de juros real da dívida configurada no Módulo Macro
    custo_divida_macro = safe_float(dre_d.get('idx_valor')) + safe_float(dre_d.get('spread'))
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Cálculo do WACC")
        ke = st.number_input("Ke (Custo Cap. Próprio %)", value=safe_float(w_d.get('ke', 15)))
        kd = st.number_input("Kd (Custo da Dívida %)", value=custo_divida_macro if custo_divida_macro > 0 else 12.0)
        eq = st.slider("Equity Ratio %", 0, 100, int(safe_float(w_d.get('eq_ratio', 60)))) / 100
        w_calc = (eq * (ke/100)) + ((1 - eq) * (kd/100) * 0.66)
        st.metric("WACC Final", f"{w_calc*100:.2f}%")
    with c2:
        st.subheader("Análise EVA")
        roi = st.number_input("ROI da Empresa (%)", value=safe_float(w_d.get('roi', 18)))
        # EVA comparado à Selic Global definida na Sidebar + Prêmio de Risco Acadêmico (5%)
        eva = roi - (selic_ref + 5.0)
        st.metric("EVA (ROI vs Selic Ref + 5%)", f"{eva:.2f}%")
        if st.button("Salvar Financeiro"):
            save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":w_calc*100})

# --- 7. RELATÓRIO ---
elif menu == "7. Relatório Final":
    st.title("📄 Relatório Consolidado")
    st.write(f"Empresa: {data.get('company_info')} | Grupo: {st.session_state.group}")
    st.divider()
    st.subheader("Diário de Bordo")
    st.info(data.get('diary', 'Sem registros.'))
    st.subheader("Diagnóstico de Endividamento")
    dre_r = data.get('dre', {})
    st.write(f"- Indexador Principal: {dre_r.get('idx_nome', 'Selic')}")
    st.write(f"- Taxa Final (Indexador + Spread): {safe_float(dre_r.get('idx_valor')) + safe_float(dre_r.get('spread'))}%")
    st.button("Exportar (Ctrl+P)")
