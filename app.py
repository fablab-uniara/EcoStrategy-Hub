import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EcoStrategy Hub - Elite BI", layout="wide")

# --- CONEXÃO SUPABASE ---
URL: str = st.secrets["SUPABASE_URL"]
KEY: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .risk-card { padding: 15px; border-radius: 8px; text-align: center; color: white; font-weight: bold; margin-bottom: 5px; border: 1px solid rgba(0,0,0,0.1); }
    .status-green { background-color: #28a745; }
    .status-yellow { background-color: #ffc107; color: black; }
    .status-red { background-color: #dc3545; }
    .insight-box { background-color: #f0f4f8; padding: 15px; border-left: 5px solid #0052cc; border-radius: 5px; font-style: italic; }
    h1, h2, h3 { color: #002e5d; }
    .stButton>button { background-color: #0052cc; color: white; border-radius: 4px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE PERSISTÊNCIA ---
def save_data(gid, column, value):
    if isinstance(value, (dict, list)): value = json.dumps(value)
    supabase.table("eco_data").upsert({"group_id": gid, column: str(value)}).execute()

def load_data(gid):
    res = supabase.table("eco_data").select("*").eq("group_id", gid).execute()
    if res.data:
        row = res.data[0]
        for col in ['porter', 'dre', 'wacc']:
            if row.get(col):
                try: row[col] = json.loads(row[col])
                except: pass
        return row
    return {}

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    group = st.selectbox("Grupo de Consultoria", ["Grupo 1", "Grupo 2", "Grupo 3"])
    if st.text_input("Senha", type="password") == "eco123" and st.button("Acessar Hub"):
        st.session_state.auth, st.session_state.group = True, group
        st.rerun()
    st.stop()

# Carregar dados globais do grupo
data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    menu = st.radio("NAVEGAÇÃO", [
        "Dashboard de Riscos", 
        "Caracterização & Campo",
        "Estratégia (Micro)", 
        "Monetário (Macro)", 
        "Financeiro (WACC/EVA)", 
        "Relatório Final"
    ])
    st.divider()
    st.info("Sincronizado com Supabase Cloud")

# --- 1. DASHBOARD DE RISCOS ---
if menu == "Dashboard de Riscos":
    st.title("🚦 Intelligence Risk Dashboard")
    
    # Cálculos Dinâmicos para os Semáforos
    dre = data.get('dre', {})
    ebitda = float(dre.get('receita', 0)) - float(dre.get('custos', 0))
    divida = float(dre.get('divida', 0))
    selic_atual = 10.75
    break_even = (ebitda / divida * 100) if divida > 0 else 100

    hhi_val = 0
    try: hhi_val = sum([float(x)**2 for x in data.get('hhi', '0').split(",")])
    except: pass

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Risco de Crédito")
        st.caption("Sensibilidade à Selic")
        status = "status-green" if selic_atual < break_even * 0.7 else "status-yellow" if selic_atual < break_even else "status-red"
        st.markdown(f'<div class="risk-card {status}">SELIC: {selic_atual}%<br>Ruptura: {break_even:.1f}%</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("Risco de Mercado")
        st.caption("Concentração HHI")
        status_m = "status-green" if hhi_val < 1500 else "status-yellow" if hhi_val < 2500 else "status-red"
        st.markdown(f'<div class="risk-card {status_m}">HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)

    with col3:
        st.subheader("Criação de Valor")
        st.caption("ROI vs Capital")
        wacc_data = data.get('wacc', {})
        roi = float(wacc_data.get('roi', 0))
        wacc_val = float(wacc_data.get('wacc_final', 15))
        status_v = "status-green" if roi > wacc_val else "status-red"
        st.markdown(f'<div class="risk-card {status_v}">ROI: {roi}%<br>WACC: {wacc_val:.1f}%</div>', unsafe_allow_html=True)

# --- 2. CARACTERIZAÇÃO & CAMPO ---
elif menu == "Caracterização & Campo":
    st.title("👥 Gestão do Projeto de Consultoria")
    tab1, tab2 = st.tabs(["Dados do Grupo e Empresa", "Diário de Bordo"])
    
    with tab1:
        with st.form("f_caract"):
            membros = st.text_area("Membros do Grupo", value=data.get('participants', ''))
            empresa = st.text_input("Nome da Empresa Analisada", value=data.get('company_info', ''))
            descricao = st.text_area("Descrição do Modelo de Negócio", value=data.get('company_desc', ''))
            if st.form_submit_button("Salvar Identificação"):
                save_data(st.session_state.group, "participants", membros)
                save_data(st.session_state.group, "company_info", empresa)
                st.success("Dados de identificação salvos!")

    with tab2:
        notas = st.text_area("Notas das Visitas Técnicas", value=data.get('diary', ''), height=300)
        if st.button("Salvar Diário"):
            save_data(st.session_state.group, "diary", notas)
            st.success("Notas de campo sincronizadas!")

# --- 3. ESTRATÉGIA (MICRO) ---
elif menu == "Estratégia (Micro)":
    st.title("🔬 Análise Microeconômica")
    tab1, tab2 = st.tabs(["Matriz de Porter", "Concentração (HHI)"])
    
    with tab1:
        st.subheader("As 5 Forças Competitivas")
        p_data = data.get('porter', {})
        colp1, colp2 = st.columns(2)
        with colp1:
            p1 = st.slider("Ameaça de Novos Entrantes", 1, 5, int(p_data.get('p1', 3)))
            p2 = st.slider("Poder dos Fornecedores", 1, 5, int(p_data.get('p2', 3)))
            p3 = st.slider("Poder dos Clientes", 1, 5, int(p_data.get('p3', 3)))
        with colp2:
            p4 = st.slider("Ameaça de Substitutos", 1, 5, int(p_data.get('p4', 3)))
            p5 = st.slider("Rivalidade Competitiva", 1, 5, int(p_data.get('p5', 3)))
        if st.button("Salvar Matriz de Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1, "p2":p2, "p3":p3, "p4":p4, "p5":p5})
            st.success("Análise de Porter salva!")

    with tab2:
        shares_input = st.text_input("Shares do Setor (ex: 40, 30, 20)", value=data.get('hhi', ''))
        if shares_input:
            vals = [float(x.strip()) for x in shares_input.split(",")]
            hhi = sum([v**2 for v in vals])
            st.metric("HHI Calculado", int(hhi))
            st.plotly_chart(px.pie(values=vals, names=[f"E{i+1}" for i in range(len(vals))], hole=0.4))
            
            # Insight Intelligence
            if hhi < 1500: insight = "✅ Mercado Competitivo: Baixo poder de precificação."
            elif hhi < 2500: insight = "⚠️ Mercado Moderado: Algum Pricing Power detectado."
            else: insight = "🚨 Oligopólio: Alto poder de precificação e risco regulatório."
            st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)
            if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", shares_input)

# --- 4. MONETÁRIO (MACRO) ---
elif menu == "Monetário (Macro)":
    st.title("🏦 Cenário Monetário e DRE")
    dre_data = data.get('dre', {})
    
    col_d1, col_d2 = st.columns([1, 2])
    with col_d1:
        st.subheader("DRE Simplificada")
        rec = st.number_input("Receita Bruta", value=float(dre_data.get('receita', 1000000)))
        cust = st.number_input("Custos/Despesas", value=float(dre_data.get('custos', 700000)))
        div = st.number_input("Dívida Total", value=float(dre_data.get('divida', 500000)))
        if st.button("Salvar DRE"):
            save_data(st.session_state.group, "dre", {"receita":rec, "custos":cust, "divida":div})
    
    with col_d2:
        st.subheader("Stress Test: Sensibilidade Selic")
        ebitda = rec - cust
        selic_sim = st.slider("Simular Selic (%)", 0.0, 30.0, 10.75)
        lucro = ebitda - (div * selic_sim/100)
        break_even = (ebitda / div * 100) if div > 0 else 0
        
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div*s/100) for s in range(0,31)], title="Ponto de Ruptura (Lucro Zero)")
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig)
        st.warning(f"Insight: A empresa entra em prejuízo financeiro se a Selic atingir **{break_even:.2f}%**")

# --- 5. FINANCEIRO (WACC/EVA) ---
elif menu == "Financeiro (WACC/EVA)":
    st.title("💰 Viabilidade e Criação de Valor")
    w_data = data.get('wacc', {})
    
    colw1, colw2 = st.columns(2)
    with colw1:
        st.subheader("Cálculo do WACC")
        ke = st.number_input("Ke (Cap. Próprio %)", value=float(w_data.get('ke', 15)))
        kd = st.number_input("Kd (Dívida %)", value=float(w_data.get('kd', 12)))
        eq_ratio = st.slider("Equity Ratio (%)", 0, 100, int(w_data.get('eq_ratio', 60))) / 100
        wacc = (eq_ratio * ke/100) + ((1-eq_ratio) * kd/100 * 0.66)
        st.metric("WACC Final", f"{wacc*100:.2f}%")
        
    with colw2:
        st.subheader("Análise EVA")
        roi = st.number_input("ROI da Empresa (%)", value=float(w_data.get('roi', 18)))
        eva = roi - (wacc*100 + 5) # Selic + Prêmio de 5%
        st.metric("Economic Value Added (EVA)", f"{eva:.2f}%", delta=f"{eva:.2f}%")
        if st.button("Salvar Dados Financeiros"):
            save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq_ratio*100, "roi":roi, "wacc_final":wacc*100})

# --- 6. RELATÓRIO FINAL ---
elif menu == "Relatório Final":
    st.title("📄 Relatório Consolidado")
    st.write(f"**Empresa:** {data.get('company_info', 'N/A')} | **Grupo:** {st.session_state.group}")
    st.divider()
    
    colr1, colr2 = st.columns(2)
    with colr1:
        st.subheader("Análise Micro")
        st.write(f"Market Share (HHI): {data.get('hhi')}")
        st.json(data.get('porter', {}))
    with colr2:
        st.subheader("Análise Financeira")
        st.write(f"WACC: {data.get('wacc', {}).get('wacc_final')}%")
        st.write(f"ROI: {data.get('wacc', {}).get('roi')}%")
    
    st.subheader("Notas de Campo")
    st.info(data.get('diary', 'Nenhuma nota registrada.'))
    st.button("Exportar para PDF (Ctrl+P)")
