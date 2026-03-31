import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="EcoStrategy Hub - Acadêmico", layout="wide")

# --- CONEXÃO ---
try:
    URL: str = st.secrets["SUPABASE_URL"]
    KEY: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("Erro nas chaves do Supabase.")
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
        return {'group_id': gid, 'porter': {}, 'dre': {}, 'wacc': {}, 'hhi': '0'}
    except: return {}

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
    if st.text_input("Senha", type="password") == "eco123" and st.button("Acessar"):
        st.session_state.auth, st.session_state.group = True, group
        st.rerun()
    st.stop()

data = load_data(st.session_state.group)

# --- SIDEBAR (Ajuste Global de Selic) ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    st.header("⚙️ Variáveis Macro")
    # AQUI VOCÊ AJUSTA A SELIC QUE IMPACTA TODO O APP
    selic_global = st.number_input("Taxa Selic Vigente (%)", value=10.75, step=0.25, help="Defina aqui a Selic atual para os cálculos de Stress Test e Custo de Oportunidade.")
    
    menu = st.radio("NAVEGAÇÃO", ["Dashboard", "Identificação", "Estratégia (Micro)", "Monetário (Macro)", "Financeiro (EVA)", "Relatório"])
    st.divider()
    st.caption("Foco Acadêmico - Economia")

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.title("🚦 Dashboard de Riscos e Insights")
    
    with st.expander("🎓 Entenda os Semáforos (Teoria)"):
        st.write("""
        - **Risco de Crédito:** Avalia se a geração de caixa (EBITDA) é suficiente para cobrir os juros da dívida. Se a Selic ultrapassar o ponto de ruptura, a empresa entra em insolvência financeira.
        - **Risco de Mercado (HHI):** Mede a concentração do setor. Mercados muito concentrados permitem maior poder de preço (Pricing Power).
        - **Criação de Valor (EVA):** Indica se o retorno (ROI) supera o custo de capital. Se for negativo, a empresa está 'destruindo riqueza'.
        """)

    dre = data.get('dre', {})
    rec = safe_float(dre.get('receita'))
    cus = safe_float(dre.get('custos'))
    div = safe_float(dre.get('divida'))
    ebitda = rec - cus
    break_even = (ebitda / div * 100) if div > 0 else 0

    hhi_val = 0
    try: hhi_val = sum([float(x)**2 for x in str(data.get('hhi', '0')).split(",") if x.strip()])
    except: hhi_val = 0

    wacc_obj = data.get('wacc', {})
    roi = safe_float(wacc_obj.get('roi'))
    w_val = safe_float(wacc_obj.get('wacc_final', 15.0))

    c1, c2, c3 = st.columns(3)
    with c1:
        color = "#28a745" if selic_global < break_even else "#dc3545" if break_even > 0 else "#6c757d"
        st.markdown(f'<div style="background:{color};padding:15px;border-radius:8px;color:white;text-align:center"><b>RISCO CRÉDITO</b><br>Ruptura: {break_even:.1f}%</div>', unsafe_allow_html=True)
    with c2:
        m_color = "#28a745" if hhi_val < 1500 else "#ffc107" if hhi_val < 2500 else "#dc3545"
        st.markdown(f'<div style="background:{m_color};padding:15px;border-radius:8px;color:white;text-align:center"><b>RISCO MERCADO</b><br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
    with c3:
        v_color = "#28a745" if roi > w_val else "#dc3545"
        st.markdown(f'<div style="background:{v_color};padding:15px;border-radius:8px;color:white;text-align:center"><b>VALOR (EVA)</b><br>ROI: {roi}%</div>', unsafe_allow_html=True)

# --- 2. IDENTIFICAÇÃO ---
elif menu == "Identificação":
    st.title("👥 Identificação do Projeto")
    with st.form("f_id"):
        membros = st.text_area("Integrantes do Grupo", value=data.get('participants', ''))
        empresa = st.text_input("Empresa Analisada", value=data.get('company_info', ''))
        if st.form_submit_button("Salvar Identificação"):
            save_data(st.session_state.group, "participants", membros)
            save_data(st.session_state.group, "company_info", empresa)
            st.success("Identificação salva!")

# --- 3. MICRO (STRATEGY) ---
elif menu == "Estratégia (Micro)":
    st.title("🔬 Análise Microeconômica")
    
    with st.expander("🎓 O que é a Matriz de Porter?"):
        st.write("""
        Desenvolvida por Michael Porter, avalia as 5 forças que determinam a atratividade de um setor. 
        Quanto mais fortes as forças, menor a rentabilidade média das empresas no longo prazo.
        """)
        
    with st.expander("🎓 O que é o Índice HHI?"):
        st.write("""
        O **Herfindahl-Hirschman Index** mede a concentração de mercado. 
        - **Abaixo de 1500:** Mercado competitivo.
        - **1500 a 2500:** Concentração moderada.
        - **Acima de 2500:** Mercado altamente concentrado (Oligopólio/Monopólio).
        """)

    tab1, tab2 = st.tabs(["5 Forças de Porter", "HHI"])
    with tab1:
        p = data.get('porter', {})
        c1, c2 = st.columns(2)
        p1 = c1.slider("Ameaça de Novos Entrantes", 1, 5, int(p.get('p1', 3)))
        p2 = c1.slider("Poder dos Fornecedores", 1, 5, int(p.get('p2', 3)))
        p3 = c1.slider("Poder dos Clientes", 1, 5, int(p.get('p3', 3)))
        p4 = c2.slider("Ameaça de Substitutos", 1, 5, int(p.get('p4', 3)))
        p5 = c2.slider("Rivalidade entre Concorrentes", 1, 5, int(p.get('p5', 3)))
        if st.button("Salvar Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1,"p2":p2,"p3":p3,"p4":p4,"p5":p5})
            st.success("Salvo!")

    with tab2:
        h_in = st.text_input("Market Shares (ex: 40,30,20)", value=data.get('hhi', ''))
        if h_in:
            try:
                sh = [float(x.strip()) for x in h_in.split(",") if x.strip()]
                hhi = sum([v**2 for v in sh])
                st.metric("HHI Calculado", int(hhi))
                st.plotly_chart(px.pie(values=sh, names=[f"E{i+1}" for i in range(len(sh))], hole=0.4))
                if hhi > 2500: st.warning("Alerta de Oligopólio: Alto Pricing Power.")
            except: st.error("Erro no formato.")
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", h_in)

# --- 4. MONETÁRIO (MACRO) ---
elif menu == "Monetário (Macro)":
    st.title("🏦 Cenário Monetário e Transmissão de Juros")
    
    with st.expander("🎓 Teoria: O Canal do Custo de Capital"):
        st.write("""
        O aumento da Taxa Selic impacta diretamente as empresas endividadas. 
        A análise de **Stress Test** abaixo mostra o 'Ponto de Ruptura', ou seja, a taxa de juros máxima 
        que a empresa suporta antes de começar a ter prejuízo operacional (EBITDA < Juros).
        """)

    dre = data.get('dre', {})
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Dados da DRE")
        r = st.number_input("Receita Bruta", value=safe_float(dre.get('receita', 1000000)))
        cus = st.number_input("Custos Operacionais", value=safe_float(dre.get('custos', 700000)))
        div = st.number_input("Dívida Bancária Total", value=safe_float(dre.get('divida', 400000)))
        if st.button("Salvar DRE"):
            save_data(st.session_state.group, "dre", {"receita":r, "custos":cus, "divida":div})
            st.rerun()

    with c2:
        st.subheader("Stress Test de Sensibilidade")
        ebitda = r - cus
        selic_test = st.slider("Simular Selic (%)", 0.0, 25.0, selic_global)
        custo_juros = div * (selic_test/100)
        lucro_est = ebitda - custo_juros
        
        st.metric("Lucro Estimado", f"R$ {lucro_est:,.2f}", delta=f"- R$ {custo_juros:,.2f} em juros")
        
        # Gráfico de Ruptura
        ss = list(range(0, 31))
        ls = [ebitda - (div * s/100) for s in ss]
        fig = px.line(x=ss, y=ls, title="Sensibilidade: Lucro vs Selic", labels={'x':'Selic %', 'y':'Lucro'})
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig)

# --- 5. FINANCEIRO (EVA) ---
elif menu == "Financeiro (EVA)":
    st.title("💰 Viabilidade Econômica")
    
    with st.expander("🎓 O que é WACC e EVA?"):
        st.write("""
        - **WACC (Weighted Average Cost of Capital):** É o custo médio ponderado de capital. Representa o retorno mínimo que a empresa deve gerar para satisfazer sócios e credores.
        - **EVA (Economic Value Added):** É o lucro econômico real. Se o ROI (Retorno sobre Investimento) for maior que o custo de capital, a empresa cria valor.
        """)

    w = data.get('wacc', {})
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Cálculo do WACC")
        ke = st.number_input("Custo Cap. Próprio (Ke %)", value=safe_float(w.get('ke', 15)))
        kd = st.number_input("Custo da Dívida (Kd %)", value=safe_float(w.get('kd', 12)))
        eq = st.slider("Participação Cap. Próprio (%)", 0, 100, int(safe_float(w.get('eq_ratio', 60)))) / 100
        wacc = (eq * ke/100) + ((1-eq) * kd/100 * 0.66) # 0.66 considera benefício fiscal
        st.metric("WACC Final", f"{wacc*100:.2f}%")
        
    with c2:
        st.subheader("Geração de Valor")
        roi = st.number_input("ROI Atual da Empresa (%)", value=safe_float(w.get('roi', 18)))
        # EVA considerando um prêmio de risco sobre a Selic Global definida na Sidebar
        custo_oportunidade = selic_global + 5.0
        eva = roi - custo_oportunidade
        
        st.metric("EVA (ROI vs Selic+Risk)", f"{eva:.2f}%", help="Compara o ROI com a Selic + prêmio de risco de 5%.")
        
        if eva > 0: st.success("Criação de Valor Detectada.")
        else: st.error("Destruição de Valor: O ROI não cobre o custo de oportunidade.")
        
        if st.button("Salvar Financeiro"):
            save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":wacc*100})

# --- 6. RELATÓRIO ---
elif menu == "Relatório":
    st.title("📄 Relatório de Consultoria")
    st.write(f"**Empresa:** {data.get('company_info')}")
    st.write(f"**Selic de Referência:** {selic_global}%")
    st.divider()
    st.write("Sumário Executivo:")
    st.info(data.get('diary', 'Nenhuma nota de campo.'))
