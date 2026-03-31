import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EcoStrategy Hub - Professional SaaS", layout="wide")

# --- CONEXÃO SUPABASE ---
try:
    URL: str = st.secrets["SUPABASE_URL"]
    KEY: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("Erro Crítico: Chaves do Supabase não encontradas nos Secrets.")
    st.stop()

# --- ESTILO CSS PROFISSIONAL ---
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 1px solid #e0e0e0; }
    .risk-card { padding: 15px; border-radius: 8px; text-align: center; color: white; font-weight: bold; margin-bottom: 5px; }
    .status-green { background-color: #28a745; }
    .status-yellow { background-color: #ffc107; color: black !important; }
    .status-red { background-color: #dc3545; }
    .insight-box { background-color: #f1f3f6; padding: 15px; border-left: 5px solid #0052cc; border-radius: 5px; margin: 10px 0; }
    h1, h2, h3 { color: #002e5d; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { background-color: #0052cc; color: white; border-radius: 4px; width: 100%; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE PERSISTÊNCIA E PARSING ---
def safe_float(val, default=0.0):
    try: return float(val)
    except: return default

def safe_json(val):
    if not val: return {}
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
            # Parsing automático de colunas JSON
            for col in ['porter', 'dre', 'wacc']:
                if row.get(col): row[col] = safe_json(row[col])
            return row
        return {}
    except: return {}

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    st.subheader("Plataforma de Consultoria Econômica")
    group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
    if st.text_input("Senha", type="password") == "eco123" and st.button("Acessar Sistema"):
        st.session_state.auth, st.session_state.group = True, group
        st.rerun()
    st.stop()

# Carregar Dados Globais
data = load_data(st.session_state.group)

# --- SIDEBAR NAVEGAÇÃO ---
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
    st.caption("v2.0 Full Stack BI Online")

# --- 1. DASHBOARD DE RISCOS (INTELLIGENCE) ---
if menu == "Dashboard de Riscos":
    st.title("🚦 Dashboard de Inteligência e Riscos")
    
    # Lógica de Semáforos baseada em dados reais
    dre = data.get('dre', {})
    ebitda = safe_float(dre.get('receita')) - safe_float(dre.get('custos'))
    divida = safe_float(dre.get('divida'))
    selic_atual = 10.75
    break_even = (ebitda / divida * 100) if divida > 0 else 0

    hhi_val = 0
    try: hhi_val = sum([float(x)**2 for x in data.get('hhi', '0').split(",")])
    except: hhi_val = 0

    wacc_data = data.get('wacc', {})
    roi = safe_float(wacc_data.get('roi'))
    wacc_val = safe_float(wacc_data.get('wacc_final', 15.0))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Risco de Crédito")
        st.caption("Sensibilidade à Selic")
        status = "status-green" if selic_atual < break_even * 0.7 else "status-yellow" if selic_atual < break_even else "status-red"
        st.markdown(f'<div class="risk-card {status}">SELIC: {selic_atual}%<br>Ponto Ruptura: {break_even:.1f}%</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("Risco de Mercado")
        st.caption("Concentração HHI")
        status_m = "status-green" if hhi_val < 1500 else "status-yellow" if hhi_val < 2500 else "status-red"
        st.markdown(f'<div class="risk-card {status_m}">HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)

    with col3:
        st.subheader("Criação de Valor")
        st.caption("ROI vs WACC")
        status_v = "status-green" if roi > wacc_val else "status-red"
        st.markdown(f'<div class="risk-card {status_v}">ROI: {roi}%<br>WACC: {wacc_val:.1f}%</div>', unsafe_allow_html=True)
    
    st.info("💡 Este dashboard é alimentado automaticamente pelos dados inseridos nos módulos Micro, Macro e Financeiro.")

# --- 2. CARACTERIZAÇÃO & CAMPO ---
elif menu == "Caracterização & Campo":
    st.title("👥 Gestão do Projeto")
    tab1, tab2 = st.tabs(["Identificação", "Diário de Bordo"])
    
    with tab1:
        with st.form("f_caract"):
            membros = st.text_area("Membros do Grupo", value=data.get('participants', ''))
            empresa = st.text_input("Nome da Empresa Analisada", value=data.get('company_info', ''))
            desc = st.text_area("Descrição do Negócio", value=data.get('company_desc', ''))
            if st.form_submit_button("Salvar Identificação"):
                save_data(st.session_state.group, "participants", membros)
                save_data(st.session_state.group, "company_info", empresa)
                save_data(st.session_state.group, "company_desc", desc)
                st.success("Dados de identificação salvos!")
                st.rerun()

    with tab2:
        st.subheader("Notas de Campo")
        notas = st.text_area("Registros das Visitas Técnicas", value=data.get('diary', ''), height=300)
        if st.button("Salvar Diário"):
            save_data(st.session_state.group, "diary", notas)
            st.success("Notas de campo sincronizadas!")

# --- 3. ESTRATÉGIA (MICRO) ---
elif menu == "Estratégia (Micro)":
    st.title("🔬 Análise Microeconômica")
    tab1, tab2 = st.tabs(["Matriz de Porter", "Calculadora HHI"])
    
    with tab1:
        st.subheader("As 5 Forças Competitivas")
        p = data.get('porter', {})
        c1, c2 = st.columns(2)
        p1 = c1.slider("Ameaça de Entrantes", 1, 5, int(p.get('p1', 3)))
        p2 = c1.slider("Poder dos Fornecedores", 1, 5, int(p.get('p2', 3)))
        p3 = c1.slider("Poder dos Clientes", 1, 5, int(p.get('p3', 3)))
        p4 = c2.slider("Ameaça de Substitutos", 1, 5, int(p.get('p4', 3)))
        p5 = c2.slider("Rivalidade", 1, 5, int(p.get('p5', 3)))
        if st.button("Salvar Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1,"p2":p2,"p3":p3,"p4":p4,"p5":p5})
            st.success("Matriz salva!")

    with tab2:
        st.subheader("HHI e Pricing Power")
        hhi_in = st.text_input("Market Shares (ex: 40, 30, 20)", value=data.get('hhi', ''))
        if hhi_in:
            shares = [float(x.strip()) for x in hhi_in.split(",")]
            hhi = sum([v**2 for v in shares])
            st.metric("HHI", int(hhi))
            st.plotly_chart(px.pie(values=shares, names=[f"E{i+1}" for i in range(len(shares))], hole=0.4))
            
            # Insight Intelligence
            if hhi < 1500: insight = "✅ **Competição Perfeita/Monopolística:** Baixo poder de precificação."
            elif hhi < 2500: insight = "⚠️ **Oligopólio Moderado:** A empresa possui Pricing Power estratégico."
            else: insight = "🚨 **Alta Concentração:** Domínio de mercado. Alto controle de preços."
            st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)
            if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", hhi_in)

# --- 4. MONETÁRIO (MACRO) ---
elif menu == "Monetário (Macro)":
    st.title("🏦 Cenário Monetário & DRE")
    dre = data.get('dre', {})
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Dados Operacionais")
        rec = st.number_input("Receita Bruta", value=safe_float(dre.get('receita', 1000000)))
        cus = st.number_input("Custos Totais", value=safe_float(dre.get('custos', 700000)))
        div = st.number_input("Dívida Total", value=safe_float(dre.get('divida', 400000)))
        if st.button("Salvar DRE"):
            save_data(st.session_state.group, "dre", {"receita":rec, "custos":cus, "divida":div})
            st.rerun()

    with c2:
        st.subheader("Stress Test de Fluxo de Caixa")
        ebitda = rec - cus
        selics = list(range(0, 31))
        lucros = [ebitda - (div * s/100) for s in selics]
        break_even = (ebitda / div * 100) if div > 0 else 0
        
        fig = px.line(x=selics, y=lucros, title="Impacto da Selic no Lucro Líquido", labels={'x':'Selic %', 'y':'Lucro R$'})
        fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Ponto de Ruptura")
        st.plotly_chart(fig)
        st.warning(f"💡 **Ponto de Morte:** Se a Selic atingir **{break_even:.2f}%**, o lucro da empresa é zerado.")

# --- 5. FINANCEIRO (WACC/EVA) ---
elif menu == "Financeiro (WACC/EVA)":
    st.title("💰 Viabilidade Econômica")
    w = data.get('wacc', {})
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Custo de Capital (WACC)")
        ke = st.number_input("Ke (Capital Próprio %)", value=safe_float(w.get('ke', 15)))
        kd = st.number_input("Kd (Dívida %)", value=safe_float(w.get('kd', 12)))
        eq = st.slider("Equity Ratio (%)", 0, 100, int(safe_float(w.get('eq_ratio', 60)))) / 100
        wacc = (eq * ke/100) + ((1-eq) * kd/100 * 0.66)
        st.metric("WACC Final", f"{wacc*100:.2f}%")
        
    with c2:
        st.subheader("Análise EVA (Economic Value Added)")
        roi = st.number_input("ROI da Empresa (%)", value=safe_float(w.get('roi', 18)))
        eva = roi - (wacc*100 + 5) # Selic + 5% prêmio
        st.metric("EVA (Criação de Valor)", f"{eva:.2f}%", delta=f"{eva:.2f}%")
        
        if eva > 0: st.success("💎 A empresa está **CRIANDO** valor econômico.")
        else: st.error("📉 A empresa está **DESTRUINDO** valor para o acionista.")
        
        if st.button("Salvar Financeiro"):
            save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":wacc*100})

# --- 6. RELATÓRIO FINAL ---
elif menu == "Relatório Final":
    st.title("📄 Relatório de Consultoria Estruturado")
    st.markdown(f"**Empresa Analisada:** {data.get('company_info', 'N/A')}")
    st.markdown(f"**Consultores:** {data.get('participants', 'N/A')}")
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Sumário Micro")
        st.write(f"HHI: {data.get('hhi', 'N/A')}")
        st.write(f"Análise de Porter concluída: Sim")
    with col2:
        st.subheader("Sumário Financeiro")
        w_res = data.get('wacc', {})
        st.write(f"WACC: {w_res.get('wacc_final', 'N/A')}%")
        st.write(f"ROI: {w_res.get('roi', 'N/A')}%")
    
    st.subheader("Notas de Campo")
    st.info(data.get('diary', 'Nenhuma nota registrada.'))
    st.button("Gerar PDF (Ctrl + P)")
