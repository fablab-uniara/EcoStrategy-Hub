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
    st.error("Erro Crítico: Chaves do Supabase não encontradas.")
    st.stop()

# --- FUNÇÕES DE SEGURANÇA (O SEGREDO PARA NÃO DAR ERRO) ---
def safe_float(val, default=0.0):
    if val is None: return default
    try: return float(val)
    except: return default

def safe_json(val):
    if val is None or val == "": return {}
    if isinstance(val, dict): return val
    try:
        # Se for string, tenta carregar o JSON
        return json.loads(val)
    except:
        return {}

def save_data(gid, column, value):
    if isinstance(value, (dict, list)): 
        value = json.dumps(value)
    supabase.table("eco_data").upsert({"group_id": gid, column: str(value)}).execute()

def load_data(gid):
    try:
        res = supabase.table("eco_data").select("*").eq("group_id", gid).execute()
        if res.data:
            row = res.data[0]
            # Proteção: Transforma campos NULL em dicionários vazios
            row['porter'] = safe_json(row.get('porter'))
            row['dre'] = safe_json(row.get('dre'))
            row['wacc'] = safe_json(row.get('wacc'))
            return row
        return {'group_id': gid, 'participants': '', 'company_info': '', 'company_desc': '', 'diary': '', 'porter': {}, 'hhi': '0', 'dre': {}, 'wacc': {}}
    except:
        return {}

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
    if st.text_input("Senha", type="password") == "eco123" and st.button("Acessar"):
        st.session_state.auth, st.session_state.group = True, group
        st.rerun()
    st.stop()

# CARREGAR DADOS COM PROTEÇÃO
data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    menu = st.radio("NAVEGAÇÃO", ["Dashboard", "Caracterização", "Micro (Porter/HHI)", "Macro (DRE/Stress)", "Financeiro (EVA)", "Relatório"])

# --- 1. DASHBOARD DE RISCOS ---
if menu == "Dashboard":
    st.title("🚦 Dashboard de Riscos Inteligente")
    
    # Extração segura de dados
    dre = data.get('dre', {})
    rec = safe_float(dre.get('receita'))
    cus = safe_float(dre.get('custos'))
    div = safe_float(dre.get('divida'))
    ebitda = rec - cus
    selic_atual = 10.75
    break_even = (ebitda / div * 100) if div > 0 else 0

    hhi_val = 0
    try: hhi_val = sum([float(x)**2 for x in str(data.get('hhi', '0')).split(",") if x.strip()])
    except: hhi_val = 0

    wacc_obj = data.get('wacc', {})
    roi = safe_float(wacc_obj.get('roi'))
    w_val = safe_float(wacc_obj.get('wacc_final', 15.0))

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Risco de Crédito")
        st_c = "status-green" if selic_atual < break_even else "status-red" if break_even > 0 else "status-yellow"
        color = "#28a745" if st_c == "status-green" else "#dc3545" if st_c == "status-red" else "#ffc107"
        st.markdown(f'<div style="background:{color};padding:15px;border-radius:8px;color:white;text-align:center;font-weight:bold">SELIC: {selic_atual}%<br>Ruptura: {break_even:.1f}%</div>', unsafe_allow_html=True)

    with col2:
        st.subheader("Risco de Mercado")
        st_m = "#28a745" if hhi_val < 1500 else "#ffc107" if hhi_val < 2500 else "#dc3545"
        st.markdown(f'<div style="background:{st_m};padding:15px;border-radius:8px;color:white;text-align:center;font-weight:bold">HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)

    with col3:
        st.subheader("Criação de Valor")
        st_v = "#28a745" if roi > w_val else "#dc3545"
        st.markdown(f'<div style="background:{st_v};padding:15px;border-radius:8px;color:white;text-align:center;font-weight:bold">ROI: {roi}%<br>WACC: {w_val:.1f}%</div>', unsafe_allow_html=True)

# --- 2. CARACTERIZAÇÃO ---
elif menu == "Caracterização":
    st.title("👥 Identificação do Projeto")
    with st.form("f_car"):
        membros = st.text_area("Membros", value=data.get('participants', ''))
        empresa = st.text_input("Empresa", value=data.get('company_info', ''))
        desc = st.text_area("Descrição", value=data.get('company_desc', ''))
        if st.form_submit_button("Salvar Identificação"):
            save_data(st.session_state.group, "participants", membros)
            save_data(st.session_state.group, "company_info", empresa)
            save_data(st.session_state.group, "company_desc", desc)
            st.success("Salvo!")
            st.rerun()
    
    st.subheader("Diário de Bordo")
    notas = st.text_area("Notas da Visita", value=data.get('diary', ''), height=200)
    if st.button("Salvar Diário"):
        save_data(st.session_state.group, "diary", notas)
        st.success("Diário salvo!")

# --- 3. MICRO (PORTER/HHI) ---
elif menu == "Micro (Porter/HHI)":
    st.title("🔬 Análise Microeconômica")
    tab1, tab2 = st.tabs(["Matriz de Porter", "HHI"])
    
    with tab1:
        p = data.get('porter', {})
        c1, c2 = st.columns(2)
        p1 = c1.slider("Novos Entrantes", 1, 5, int(p.get('p1', 3)))
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
                hhi = sum([v**2 for v in sh])
                st.metric("HHI", int(hhi))
                st.plotly_chart(px.pie(values=sh, names=[f"E{i+1}" for i in range(len(sh))]))
            except: st.error("Formato inválido.")
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", h_in)

# --- 4. MACRO (DRE/STRESS) ---
elif menu == "Macro (DRE/Stress)":
    st.title("🏦 Monetário e Stress Test")
    dre = data.get('dre', {})
    c1, c2 = st.columns([1, 2])
    with c1:
        r = st.number_input("Receita", value=safe_float(dre.get('receita', 1000000)))
        c = st.number_input("Custos", value=safe_float(dre.get('custos', 700000)))
        d = st.number_input("Dívida", value=safe_float(dre.get('divida', 400000)))
        if st.button("Salvar DRE"):
            save_data(st.session_state.group, "dre", {"receita":r, "custos":c, "divida":d})
            st.rerun()
    
    with c2:
        ebitda = r - c
        selics = list(range(0, 31))
        lucros = [ebitda - (d * s/100) for s in selics]
        fig = px.line(x=selics, y=lucros, title="Impacto da Selic no Lucro")
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig)

# --- 5. FINANCEIRO (EVA) ---
elif menu == "Financeiro (EVA)":
    st.title("💰 Financeiro")
    w = data.get('wacc', {})
    c1, c2 = st.columns(2)
    with c1:
        ke = st.number_input("Ke %", value=safe_float(w.get('ke', 15)))
        kd = st.number_input("Kd %", value=safe_float(w.get('kd', 12)))
        eq = st.slider("Equity %", 0, 100, int(safe_float(w.get('eq_ratio', 60)))) / 100
        wacc = (eq * ke/100) + ((1-eq) * kd/100 * 0.66)
        st.metric("WACC", f"{wacc*100:.2f}%")
        
    with c2:
        roi = st.number_input("ROI %", value=safe_float(w.get('roi', 18)))
        eva = roi - (wacc*100 + 5)
        st.metric("EVA", f"{eva:.2f}%")
        if st.button("Salvar Financeiro"):
            save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":wacc*100})

# --- 6. RELATÓRIO ---
elif menu == "Relatório":
    st.title("📄 Relatório")
    st.write(f"**Empresa:** {data.get('company_info')}")
    st.write(f"**Membros:** {data.get('participants')}")
    st.write(f"**Diário:** {data.get('diary')}")
