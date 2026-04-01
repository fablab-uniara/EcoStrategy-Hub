import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Hub - Master Intelligence", layout="wide", initial_sidebar_state="expanded")

# --- CSS WHITELABEL & DESIGN ---
st.markdown("""
    <style>
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 1px solid #e0e0e0; min-width: 280px !important; }
    h1, h2, h3 { color: #002e5d; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
    .risk-card { padding: 20px; border-radius: 12px; text-align: center; color: white; font-weight: bold; margin-bottom: 10px; border: 1px solid rgba(0,0,0,0.1); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .insight-box { background-color: #ffffff; padding: 20px; border-left: 6px solid #0052cc; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
    .swot-card { padding: 15px; border-radius: 8px; height: 120px; color: white; font-size: 0.85em; overflow-y: auto; margin-bottom: 10px; }
    .stButton>button { background-color: #0052cc; color: white; border-radius: 6px; width: 100%; font-weight: bold; height: 45px; border: none; }
    .formula-text { font-family: 'Courier New', Courier, monospace; background-color: #f4f4f4; padding: 5px; border-radius: 3px; }
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
        return {'group_id': gid, 'porter': {}, 'dre': {}, 'wacc': {}, 'swot': {}, 'hhi': '0', 'diary': '', 'participants': '', 'company_info': ''}
    except: return {}

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    st.subheader("Plataforma Acadêmica de Consultoria")
    col_l1, col_l2 = st.columns([1, 2])
    with col_l1:
        group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
        if st.text_input("Senha", type="password") == "eco123" and st.button("Acessar Dashboard"):
            st.session_state.auth, st.session_state.group = True, group
            st.rerun()
    st.stop()

data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    st.header("⚙️ Variáveis de Referência")
    selic_ref = st.number_input("Selic de Referência (%)", value=10.75, step=0.25)
    st.divider()
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
    st.title("📈 Dashboard Executivo Inteligente")
    
    comp_name = data.get('company_info', 'Empresa Não Definida')
    st.markdown(f'<div class="insight-box"><h4>Projeto: {comp_name}</h4><p>Resumo de performance, valor e riscos estratégicos.</p></div>', unsafe_allow_html=True)
    
    # Cálculos para Semáforos
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
    g_val = safe_float(w_d.get('g_growth', 3.0)) / 100

    col1, col2, col3 = st.columns(3)
    with col1:
        c = "#28a745" if idx_total < (ebitda/divida*100 if divida > 0 else 100) else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{c}">RISCO CRÉDITO<br>Taxa Atual: {idx_total:.2f}%</div>', unsafe_allow_html=True)
    with col2:
        mc = "#28a745" if hhi_val < 1500 else "#ffc107" if hhi_val < 2500 else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{mc}">RISCO MERCADO<br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
    with col3:
        vc = "#28a745" if roi > w_final else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{vc}">CRIAÇÃO VALOR<br>ROI: {roi}%</div>', unsafe_allow_html=True)

    st.divider()
    
    # NOVO: INDICADORES NO DASHBOARD
    cola, colb = st.columns(2)
    with cola:
        st.subheader("💎 Valuation do Negócio")
        if (w_final/100) > g_val:
            val_est = (ebitda * (1 + g_val)) / ((w_final/100) - g_val)
            st.metric("Enterprise Value Estimado", f"R$ {val_est:,.2f}")
        else: st.warning("Aguardando cálculos financeiros (WACC > G).")
    
    with colb:
        st.subheader("🎯 Resumo SWOT")
        sw = data.get('swot', {})
        st.write(f"**Força:** {sw.get('f', '-')[:50]}...")
        st.write(f"**Ameaça:** {sw.get('a', '-')[:50]}...")

# --- 2. IDENTIFICAÇÃO ---
elif menu == "2. Identificação e Empresa":
    st.title("👥 Identificação")
    with st.form("f_id"):
        membros = st.text_area("Integrantes", value=data.get('participants', ''))
        empresa = st.text_input("Empresa", value=data.get('company_info', ''))
        desc = st.text_area("Descrição do Negócio", value=data.get('company_desc', ''))
        if st.form_submit_button("Salvar Identificação"):
            save_data(st.session_state.group, "participants", membros)
            save_data(st.session_state.group, "company_info", empresa)
            save_data(st.session_state.group, "company_desc", desc)
            st.success("Salvo!")

# --- 3. DIÁRIO DE BORDO ---
elif menu == "3. Diário de Bordo (Campo)":
    st.title("📔 Diário de Bordo")
    notas = st.text_area("Registro qualitativo das visitas e entrevistas", value=data.get('diary', ''), height=450)
    if st.button("Sincronizar Diário"):
        save_data(st.session_state.group, "diary", notas)
        st.success("Diário atualizado!")

# --- 4. MÓDULO MICRO ---
elif menu == "4. Módulo Micro (Porter/HHI/SWOT)":
    st.title("🔬 Análise Microeconômica")
    
    with st.expander("🎓 Saiba mais: Porter, HHI e SWOT"):
        st.markdown("**Matriz de Porter:** Analisa a atratividade do setor através de 5 forças competitivas.")
        st.markdown("**Índice HHI:** Mede a concentração de mercado. <span class='formula-text'>HHI = Σ (Share²)</span>", unsafe_allow_html=True)
        st.markdown("**SWOT:** Ferramenta de planejamento estratégico que cruza fatores internos (Forças/Fraquezas) com externos (Oportunidades/Ameaças).")

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
            st.success("Porter Salvo!")
    with t2:
        h_in = st.text_input("Shares (ex: 40,30,20)", value=data.get('hhi', ''))
        if h_in:
            try:
                sh = [float(x.strip()) for x in h_in.split(",") if x.strip()]
                h_val = sum([v**2 for v in sh])
                st.metric("HHI", int(h_val))
                st.plotly_chart(px.pie(values=sh, names=[f"Empresa {i+1}" for i in range(len(sh))], hole=0.4))
            except: st.error("Erro no formato das shares.")
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", h_in)
    with t3:
        sw = data.get('swot', {})
        with st.form("f_swot"):
            c1, c2 = st.columns(2)
            f = c1.text_area("Forças", value=sw.get('f', ''))
            o = c1.text_area("Oportunidades", value=sw.get('o', ''))
            fra = c2.text_area("Fraquezas", value=sw.get('fra', ''))
            a = c2.text_area("Ameaças", value=sw.get('a', ''))
            if st.form_submit_button("Salvar SWOT"):
                save_data(st.session_state.group, "swot", {"f":f, "fra":fra, "o":o, "a":a})
                st.rerun()
        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="swot-card" style="background:#28a745"><b>FORÇAS</b><br>{f}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="swot-card" style="background:#dc3545"><b>FRAQUEZAS</b><br>{fra}</div>', unsafe_allow_html=True)
        c1.markdown(f'<div class="swot-card" style="background:#0052cc"><b>OPORTUNIDADES</b><br>{o}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="swot-card" style="background:#ffc107; color:black"><b>AMEAÇAS</b><br>{a}</div>', unsafe_allow_html=True)

# --- 5. MONETÁRIO ---
elif menu == "5. Módulo Macro (Monetário)":
    st.title("🏦 Monetário e Indexadores")
    
    with st.expander("🎓 Saiba mais: Indexadores e Stress Test"):
        st.markdown("**Taxa de Juros Real:** <span class='formula-text'>Juros Totais = Indexador + Spread</span>", unsafe_allow_html=True)
        st.markdown("**Stress Test:** Simula o impacto do aumento do indexador no Lucro Operacional. O ponto onde o lucro atinge zero é o 'Ponto de Ruptura'.")

    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_nome = st.selectbox("Indexador", ["Selic", "TJLP", "IGP-M", "IPCA", "Outro"], index=0)
        idx_val = st.number_input(f"Valor do {idx_nome} (%)", value=safe_float(dre_d.get('idx_valor', 10.75)))
        spread = st.number_input("Spread Bancário (+%)", value=safe_float(dre_d.get('spread', 2.0)))
        rec = st.number_input("Receita Bruta", value=safe_float(dre_d.get('receita', 1000000)))
        cus = st.number_input("Custos Totais", value=safe_float(dre_d.get('custos', 700000)))
        div = st.number_input("Dívida Total", value=safe_float(dre_d.get('divida', 400000)))
        if st.button("Salvar Macro"):
            save_data(st.session_state.group, "dre", {"idx_nome":idx_nome, "idx_valor":idx_val, "spread":spread, "receita":rec, "custos":cus, "divida":div})
            st.rerun()
    with c2:
        ebitda = rec - cus
        sim = st.slider(f"Simular {idx_nome} %", 0.0, 30.0, idx_val)
        lucro_est = ebitda - (div * (sim + spread) / 100)
        st.metric("Lucro Operacional Líquido", f"R$ {lucro_est:,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div * (s + spread) / 100) for s in range(0,31)], title="Análise de Sensibilidade")
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig)

# --- 6. FINANCEIRO ---
elif menu == "6. Módulo Financeiro (WACC/Valuation)":
    st.title("💰 Viabilidade e Valuation")
    
    with st.expander("🎓 Saiba mais: WACC, EVA e Gordon"):
        st.markdown("**WACC:** Custo médio ponderado de capital. <span class='formula-text'>WACC = (E/V * Ke) + (D/V * Kd * (1-T))</span>", unsafe_allow_html=True)
        st.markdown("**EVA:** Criação de valor real. <span class='formula-text'>EVA = ROI - (Selic + Risco)</span>", unsafe_allow_html=True)
        st.markdown("**Valuation (Modelo de Gordon):** Valor presente da perpetuidade. <span class='formula-text'>EV = Fluxo(1+g) / (WACC - g)</span>", unsafe_allow_html=True)

    t1, t2 = st.tabs(["WACC & EVA", "Simulador de Valuation"])
    with t1:
        w_d = data.get('wacc', {})
        c1, c2 = st.columns(2)
        with c1:
            ke = st.number_input("Ke %", value=safe_float(w_d.get('ke', 15)))
            kd = st.number_input("Kd %", value=safe_float(w_d.get('kd', 12)))
            eq = st.slider("Equity %", 0, 100, int(safe_float(w_d.get('eq_ratio', 60)))) / 100
            w_calc = (eq * (ke/100)) + ((1 - eq) * (kd/100) * 0.66)
            st.metric("WACC Final", f"{w_calc*100:.2f}%")
        with c2:
            roi = st.number_input("ROI da Empresa (%)", value=safe_float(w_d.get('roi', 18)))
            eva = roi - (selic_ref + 5.0)
            st.metric("EVA (ROI vs Selic + 5%)", f"{eva:.2f}%")
            if st.button("Salvar Financeiro"):
                save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":w_calc*100})
    with t2:
        st.subheader("Valuation por Perpetuidade")
        g = st.slider("Crescimento Anual (g) %", 0.0, 10.0, safe_float(w_d.get('g_growth', 3.0)))
        if st.button("Salvar g"): save_data(st.session_state.group, "wacc", {**w_d, "g_growth": g})
        
        ebitda_v = safe_float(data.get('dre', {}).get('receita')) - safe_float(data.get('dre', {}).get('custos'))
        w_v = safe_float(w_d.get('wacc_final')) / 100
        g_v = g / 100
        if w_v > g_v:
            val = (ebitda_v * (1 + g_v)) / (w_v - g_v)
            st.metric("Enterprise Value", f"R$ {val:,.2f}")
        else: st.error("WACC deve ser maior que 'g' para cálculo de perpetuidade.")

# --- 7. RELATÓRIO ---
elif menu == "7. Relatório Final":
    st.title("📄 Relatório Consolidado")
    st.write(f"Empresa: {data.get('company_info')} | Grupo: {st.session_state.group}")
    st.divider()
    st.subheader("Diário de Bordo")
    st.info(data.get('diary', 'Sem registros.'))
    st.button("Exportar para PDF (Ctrl+P)")
