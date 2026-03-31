import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="EcoStrategy Hub - Intelligence", layout="wide")

# --- CONEXÃO SUPABASE ---
URL: str = st.secrets["SUPABASE_URL"]
KEY: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .risk-card { padding: 20px; border-radius: 10px; text-align: center; color: white; font-weight: bold; margin-bottom: 10px; }
    .status-green { background-color: #28a745; }
    .status-yellow { background-color: #ffc107; color: black; }
    .status-red { background-color: #dc3545; }
    .insight-box { background-color: #eef2f7; padding: 15px; border-left: 5px solid #0052cc; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE PERSISTÊNCIA ---
def save_data(gid, column, value):
    if isinstance(value, (dict, list)): value = json.dumps(value)
    supabase.table("eco_data").upsert({"group_id": gid, column: str(value)}).execute()

def load_data(gid):
    res = supabase.table("eco_data").select("*").eq("group_id", gid).execute()
    return res.data[0] if res.data else {}

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub - Business Intelligence")
    group = st.selectbox("Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
    if st.text_input("Senha", type="password") == "eco123" and st.button("Acessar"):
        st.session_state.auth, st.session_state.group = True, group
        st.rerun()
    st.stop()

data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    menu = st.radio("MÓDULOS", ["Dashboard de Riscos", "Estratégia (Micro)", "Monetário (Macro)", "Financeiro (EVA)", "Relatório"])

# --- 1. DASHBOARD DE RISCOS (SEMÁFOROS) ---
if menu == "Dashboard de Riscos":
    st.title("🚦 Dashboard de Gestão de Riscos")
    
    # Lógica de Risco de Crédito (Baseado na Selic vs Ruptura)
    # Valores fictícios/base vindos do banco se existirem
    divida = 400000 
    ebitda = 100000 # Exemplo de EBITDA
    selic_atual = 10.75
    break_even_selic = (ebitda / divida) * 100 if divida > 0 else 100
    
    # Lógica Risco Mercado (HHI)
    hhi_str = data.get('hhi', '0')
    try:
        shares = [float(x) for x in hhi_str.split(",")]
        hhi_val = sum([x**2 for x in shares])
    except: hhi_val = 0

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Risco de Crédito")
        status = "status-green" if selic_atual < break_even_selic * 0.7 else "status-yellow" if selic_atual < break_even_selic else "status-red"
        st.markdown(f'<div class="risk-card {status}">TAXA SELIC<br>{selic_atual}%</div>', unsafe_allow_html=True)
        st.caption(f"Ponto de Ruptura: {break_even_selic:.2f}% Selic")

    with col2:
        st.subheader("Risco de Mercado")
        status_m = "status-green" if hhi_val < 1500 else "status-yellow" if hhi_val < 2500 else "status-red"
        st.markdown(f'<div class="risk-card {status_m}">HHI<br>{int(hhi_val)}</div>', unsafe_allow_html=True)
        st.caption("Concentração Setorial")

    with col3:
        st.subheader("Risco Cambial")
        cambio_exp = st.select_slider("Exposição ao Dólar", options=["Baixa", "Média", "Alta"], value="Média")
        status_c = "status-green" if cambio_exp == "Baixa" else "status-yellow" if cambio_exp == "Média" else "status-red"
        st.markdown(f'<div class="risk-card {status_c}">CÂMBIO<br>{cambio_exp}</div>', unsafe_allow_html=True)

# --- 2. MÓDULO MICRO (INTELLIGENCE HHI) ---
elif menu == "Estratégia (Micro)":
    st.title("🔬 Análise Microeconômica Avançada")
    shares_input = st.text_input("Market Shares (ex: 40, 30, 10)", value=data.get('hhi', ''))
    
    if shares_input:
        shares = [float(x.strip()) for x in shares_input.split(",")]
        hhi = sum([x**2 for x in shares])
        
        col_m1, col_m2 = st.columns([1, 1])
        with col_m1:
            st.plotly_chart(px.pie(values=shares, hole=0.4, title="Market Share"))
        
        with col_m2:
            st.subheader("Intelligence Insight: HHI")
            if hhi < 1500:
                insight = "✅ **Mercado Competitivo:** A empresa tem baixo poder de precificação. A estratégia deve focar em eficiência operacional e escala."
            elif hhi < 2500:
                insight = "⚠️ **Mercado Moderado:** Existe interdependência entre os concorrentes. A empresa possui algum poder de marca (Pricing Power)."
            else:
                insight = "🚨 **Mercado Altamente Concentrado:** Oligopólio detectado. Alto poder de precificação. Risco de regulação antitruste elevado."
            
            st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)
            if st.button("Salvar Análise HHI"): save_data(st.session_state.group, "hhi", shares_input)

# --- 3. MÓDULO MACRO (PONTO DE RUPTURA) ---
elif menu == "Monetário (Macro)":
    st.title("🏦 Sensibilidade de Fluxo de Caixa")
    
    col_d1, col_d2 = st.columns([1, 2])
    with col_d1:
        ebitda = st.number_input("EBITDA Anual (R$)", value=200000)
        divida = st.number_input("Dívida Total (R$)", value=1000000)
        selic_break = (ebitda / divida) * 100 if divida > 0 else 0
        
    with col_d2:
        selics = [x for x in range(0, 30)]
        lucros = [ebitda - (divida * (s/100)) for s in selics]
        
        fig = px.line(x=selics, y=lucros, title="Sensitivity Analysis: EBITDA vs Juros", labels={'x':'Taxa Selic %', 'y':'Lucro Líquido'})
        fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Ponto de Ruptura")
        fig.add_vline(x=selic_break, line_color="black")
        st.plotly_chart(fig)
        
        st.warning(f"**Insight Econômico:** O 'Ponto de Morte' da empresa ocorre com a Selic em **{selic_break:.2f}%**. Acima disso, a operação não gera caixa suficiente para pagar os juros da dívida.")

# --- 4. MÓDULO FINANCEIRO (EVA) ---
elif menu == "Módulo Financeiro":
    st.title("💰 Economic Value Added (EVA)")
    
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        roi = st.number_input("ROI da Empresa (%)", value=18.0)
        selic_ref = 10.75
        premio_risco = 5.0
        custo_capital = selic_ref + premio_risco
        eva = roi - custo_capital
        
        st.subheader("Cálculo de Criação de Valor")
        st.write(f"Custo de Capital (Selic + 5%): **{custo_capital}%**")
        st.write(f"ROI Atual: **{roi}%**")
        
        delta_color = "normal" if eva > 0 else "inverse"
        st.metric("EVA (Spread de Valor)", f"{eva:.2f}%", delta=f"{eva:.2f}%", delta_color=delta_color)

    with col_e2:
        if eva > 0:
            st.success("💎 **Criação de Valor:** O negócio é rentável acima do seu custo de oportunidade ajustado ao risco.")
        else:
            st.error("📉 **Destruição de Valor:** A empresa está rendendo menos que uma aplicação de baixo risco. O acionista está perdendo dinheiro em termos reais.")
        
        # Gráfico EVA
        fig_eva = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = roi,
            title = {'text': "ROI vs Custo Cap."},
            gauge = {'axis': {'range': [0, 30]},
                     'steps' : [{'range': [0, custo_capital], 'color': "lightcoral"},
                                {'range': [custo_capital, 30], 'color': "lightgreen"}],
                     'threshold' : {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': custo_capital}}))
        st.plotly_chart(fig_eva)

elif menu == "Relatório":
    st.header("Gerador de Insights Finais")
    st.write("Dados consolidados para apresentação.")
    st.button("Exportar Inteligência de Consultoria")
