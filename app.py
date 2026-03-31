import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EcoStrategy Hub - Professional", layout="wide")

# --- CONEXÃO SUPABASE ---
try:
    URL: str = st.secrets["SUPABASE_URL"]
    KEY: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("Erro Crítico: Verifique as chaves nos Secrets.")
    st.stop()

# --- FUNÇÕES DE SEGURANÇA E PARSING ---
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
        return {'group_id': gid, 'porter': {}, 'dre': {}, 'wacc': {}, 'hhi': '0', 'diary': '', 'participants': '', 'company_info': ''}
    except: return {}

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
    if st.text_input("Senha", type="password") == "eco123" and st.button("Acessar Sistema"):
        st.session_state.auth, st.session_state.group = True, group
        st.rerun()
    st.stop()

# CARREGAR DADOS
data = load_data(st.session_state.group)

# --- SIDEBAR (Configurações Globais) ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    st.header("⚙️ Variáveis de Mercado")
    # AJUSTE DA SELIC QUE AFETA TODO O APP
    selic_global = st.number_input("Taxa Selic Atual (%)", value=10.75, step=0.25, help="Taxa básica de juros para Stress Test e EVA.")
    
    menu = st.radio("NAVEGAÇÃO", [
        "Dashboard de Riscos", 
        "Identificação", 
        "Diário de Bordo (Campo)", # ABA RESTAURADA
        "Estratégia (Micro)", 
        "Monetário (Macro)", 
        "Financeiro (WACC/EVA)", 
        "Relatório Final"
    ])
    st.divider()
    st.caption("Uso Acadêmico - Consultoria Econômica")

# --- 1. DASHBOARD DE RISCOS ---
if menu == "Dashboard de Riscos":
    st.title("🚦 Dashboard de Inteligência e Riscos")
    
    with st.expander("🎓 Teoria: Como ler este Dashboard?"):
        st.write("""
        Este painel consolida os riscos da empresa. O **Risco de Crédito** analisa a solvência perante os juros (Selic). 
        O **Risco de Mercado** foca na competição (HHI). O **EVA** mostra se o lucro é 'real' ou se a empresa 
        perde para o custo de oportunidade (Selic + Risco).
        """)

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

    c1, c2, c3 = st.columns(3)
    with c1:
        color = "#28a745" if selic_global < break_even else "#dc3545" if break_even > 0 else "#6c757d"
        st.markdown(f'<div style="background:{color};padding:20px;border-radius:10px;color:white;text-align:center"><b>RISCO CRÉDITO</b><br>Ruptura: {break_even:.1f}%</div>', unsafe_allow_html=True)
    with c2:
        m_color = "#28a745" if hhi_val < 1500 else "#ffc107" if hhi_val < 2500 else "#dc3545"
        st.markdown(f'<div style="background:{m_color};padding:20px;border-radius:10px;color:white;text-align:center"><b>RISCO MERCADO</b><br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
    with c3:
        v_color = "#28a745" if roi > w_val else "#dc3545"
        st.markdown(f'<div style="background:{v_color};padding:20px;border-radius:10px;color:white;text-align:center"><b>VALOR (EVA)</b><br>ROI: {roi}%</div>', unsafe_allow_html=True)

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

# --- 3. DIÁRIO DE BORDO (RESTAURADO) ---
elif menu == "Diário de Bordo (Campo)":
    st.title("📔 Diário de Bordo e Visitas")
    with st.expander("🎓 Por que registrar o Diário?"):
        st.write("O registro qualitativo é a base da consultoria. Use este espaço para transcrever entrevistas, descrever o layout da empresa e gargalos produtivos observados.")
    
    notas = st.text_area("Notas da Visita Técnica / Entrevista", value=data.get('diary', ''), height=400)
    if st.button("Salvar Registro de Campo"):
        save_data(st.session_state.group, "diary", notas)
        st.success("Diário de bordo sincronizado com sucesso!")

# --- 4. ESTRATÉGIA (MICRO) ---
elif menu == "Estratégia (Micro)":
    st.title("🔬 Módulo Microeconômico")
    tab1, tab2 = st.tabs(["5 Forças de Porter", "Cálculo HHI"])
    
    with tab1:
        st.subheader("Matriz de Porter")
        p = data.get('porter', {})
        c1, c2 = st.columns(2)
        p1 = c1.slider("Novos Entrantes", 1, 5, int(p.get('p1', 3)))
        p2 = c1.slider("Fornecedores", 1, 5, int(p.get('p2', 3)))
        p3 = c1.slider("Clientes", 1, 5, int(p.get('p3', 3)))
        p4 = c2.slider("Substitutos", 1, 5, int(p.get('p4', 3)))
        p5 = c2.slider("Rivalidade", 1, 5, int(p.get('p5', 3)))
        if st.button("Salvar Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1,"p2":p2,"p3":p3,"p4":p4,"p5":p5})
            st.success("Matriz salva!")

    with tab2:
        st.subheader("HHI e Poder de Preço")
        h_in = st.text_input("Market Shares (ex: 40,30,20)", value=data.get('hhi', ''))
        if h_in:
            try:
                sh = [float(x.strip()) for x in h_in.split(",") if x.strip()]
                hhi_res = sum([v**2 for v in sh])
                st.metric("Índice HHI", int(hhi_res))
                st.plotly_chart(px.pie(values=sh, names=[f"E{i+1}" for i in range(len(sh))], hole=0.4))
                if hhi_res > 2500: st.warning("ALERTA: Mercado altamente concentrado (Oligopólio).")
            except: st.error("Erro de formato.")
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", h_in)

# --- 5. MONETÁRIO (MACRO) ---
elif menu == "Monetário (Macro)":
    st.title("🏦 Monetário e Stress Test")
    with st.expander("🎓 Explicação Acadêmica: O Canal de Juros"):
        st.write("Aqui analisamos a 'saúde financeira' sob estresse monetário. O gráfico mostra o 'Ponto de Ruptura', indicando até que Selic a empresa sobrevive sem prejuízo operacional.")
    
    dre = data.get('dre', {})
    c1, c2 = st.columns([1, 2])
    with c1:
        r = st.number_input("Receita Bruta", value=safe_float(dre.get('receita', 1000000)))
        c = st.number_input("Custos Totais", value=safe_float(dre.get('custos', 700000)))
        d = st.number_input("Dívida Bancária", value=safe_float(dre.get('divida', 400000)))
        if st.button("Salvar DRE"):
            save_data(st.session_state.group, "dre", {"receita":r, "custos":c, "divida":d})
            st.rerun()
    
    with c2:
        ebitda = r - c
        sim_selic = st.slider("Simular Selic %", 0.0, 30.0, selic_global)
        lucro_est = ebitda - (d * sim_selic/100)
        st.metric("Lucro Estimado na Selic Simulada", f"R$ {lucro_est:,.2f}")
        
        fig = px.line(x=list(range(0,31)), y=[ebitda - (d*s/100) for s in range(0,31)], title="Ponto de Ruptura do Fluxo de Caixa")
        fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Ponto de Morte")
        st.plotly_chart(fig)

# --- 6. FINANCEIRO ---
elif menu == "Financeiro (WACC/EVA)":
    st.title("💰 Viabilidade Econômica")
    w = data.get('wacc', {})
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Cálculo do WACC")
        ke = st.number_input("Ke (Cap. Próprio %)", value=safe_float(w.get('ke', 15)))
        kd = st.number_input("Kd (Dívida %)", value=safe_float(w.get('kd', 12)))
        eq = st.slider("Equity %", 0, 100, int(safe_float(w.get('eq_ratio', 60)))) / 100
        wacc = (eq * ke/100) + ((1-eq) * kd/100 * 0.66)
        st.metric("WACC Final",
