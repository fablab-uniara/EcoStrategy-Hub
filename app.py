import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Hub - Master BI", layout="wide", initial_sidebar_state="expanded")

# --- CSS WHITELABEL & DESIGN ACADÊMICO ---
st.markdown("""
    <style>
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 1px solid #e0e0e0; min-width: 320px !important; }
    h1, h2, h3 { color: #002e5d; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
    .risk-card { padding: 20px; border-radius: 12px; text-align: center; color: white; font-weight: bold; margin-bottom: 10px; border: 1px solid rgba(0,0,0,0.1); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .insight-box { background-color: #ffffff; padding: 20px; border-left: 6px solid #0052cc; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
    .formula-text { font-family: 'Courier New', Courier, monospace; background-color: #f4f4f4; padding: 10px; border-radius: 5px; font-size: 0.85em; color: #d63384; border: 1px solid #ddd; display: block; margin: 10px 0;}
    .guide-text { font-size: 0.95em; color: #444; line-height: 1.6; background: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #ddd; margin-bottom: 15px;}
    .interpretation-box { padding: 15px; border-radius: 8px; margin-top: 10px; font-weight: 500; }
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
            for col in ['porter', 'dre', 'wacc', 'swot', 'participants', 'company_info', 'diary']:
                row[col] = safe_json(row.get(col))
            return row
        return {'group_id': gid, 'porter': {}, 'dre': {}, 'wacc': {}, 'swot': {}, 'hhi': '0', 'diary': {}, 'participants': {}, 'company_info': {}}
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
    st.divider()
    menu = st.radio("ETAPAS DA CONSULTORIA", [
        "1. Dashboard Executivo", 
        "2. Identificação da Equipe", 
        "3. Perfil da Empresa",
        "4. Guia de Entrevista (Diário)", 
        "5. Módulo Micro (Estratégia)", 
        "6. Módulo Macro (Monetário)", 
        "7. Módulo Financeiro & Valor", 
        "8. Relatório Final"
    ])
    st.divider()
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# --- 1. DASHBOARD ---
if menu == "1. Dashboard Executivo":
    st.title("📈 Painel de Inteligência Financeira")
    info = data.get('company_info', {})
    st.markdown(f'<div class="insight-box"><h4>Consultoria Acadêmica: {info.get("nome", "Aguardando Perfil")}</h4><p>Status atual da viabilidade econômica e riscos estruturais.</p></div>', unsafe_allow_html=True)
    
    dre_d = data.get('dre', {})
    ebitda = safe_float(dre_d.get('receita')) - safe_float(dre_d.get('custos'))
    divida = safe_float(dre_d.get('divida'))
    idx_total = safe_float(dre_d.get('idx_valor')) + safe_float(dre_d.get('spread'))
    break_even = (ebitda / divida * 100) if divida > 0 else 0

    hhi_str = str(data.get('hhi', '0'))
    hhi_val = 0
    try: hhi_val = sum([float(x)**2 for x in hhi_str.split(",") if x.strip()])
    except: hhi_val = 0

    w_d = data.get('wacc', {})
    roi = safe_float(w_d.get('roi'))
    w_final = safe_float(w_d.get('wacc_final', 15.0))
    g_val = safe_float(w_d.get('g_growth', 3.0)) / 100

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

# --- 2. IDENTIFICAÇÃO EQUIPE ---
elif menu == "2. Identificação da Equipe":
    st.title("👥 Consultores Responsáveis")
    part = data.get('participants', {})
    with st.form("f_equipe"):
        c1, c2 = st.columns(2)
        al1 = c1.text_input("Líder do Grupo", value=part.get('aluno1', ''))
        al2 = c1.text_input("Aluno 2", value=part.get('aluno2', ''))
        al3 = c1.text_input("Aluno 3", value=part.get('aluno3', ''))
        al4 = c2.text_input("Aluno 4", value=part.get('aluno4', ''))
        al5 = c2.text_input("Aluno 5", value=part.get('aluno5', ''))
        prof = c2.text_input("Professor Orientador", value=part.get('professor', ''))
        if st.form_submit_button("Salvar Equipe"):
            save_data(st.session_state.group, "participants", {"aluno1":al1, "aluno2":al2, "aluno3":al3, "aluno4":al4, "aluno5":al5, "professor":prof})
            st.success("Equipe Atualizada!")

# --- 3. PERFIL DA EMPRESA ---
elif menu == "3. Perfil da Empresa":
    st.title("🏢 Caracterização do Cliente")
    info = data.get('company_info', {})
    with st.form("f_empresa"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Nome da Empresa", value=info.get('nome', ''))
        setor = c1.selectbox("Setor", ["Varejo", "Indústria", "Serviços", "Agro", "Tech"], index=0)
        colab = c2.number_input("Nº Funcionários", value=int(safe_float(info.get('colab', 0))))
        desc = st.text_area("Modelo de Negócio", value=info.get('desc', ''))
        if st.form_submit_button("Salvar Perfil"):
            save_data(st.session_state.group, "company_info", {"nome":nome, "setor":setor, "colab":colab, "desc":desc})
            st.success("Perfil Salvo!")

# --- 4. GUIA DE ENTREVISTA ---
elif menu == "4. Guia de Entrevista (Diário)":
    st.title("📔 Diagnóstico de Campo")
    diary = data.get('diary', {})
    with st.form("f_diary"):
        q1 = st.text_area("1. Qual o diferencial competitivo da empresa?", value=diary.get('q1', ''))
        q2 = st.text_area("2. Como os juros afetam o caixa hoje?", value=diary.get('q2', ''))
        q3 = st.text_area("3. Quem são os principais concorrentes?", value=diary.get('q3', ''))
        if st.form_submit_button("Salvar Entrevista"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2, "q3":q3})
            st.success("Dados Salvos!")

# --- 5. MÓDULO MICRO ---
elif menu == "5. Módulo Micro (Estratégia)":
    st.title("🔬 Estratégia e Concentração")
    t1, t2 = st.tabs(["Porter", "HHI"])
    with t1:
        p = data.get('porter', {})
        p1 = st.slider("Ameaça Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        p5 = st.slider("Rivalidade", 1, 5, int(safe_float(p.get('p5', 3))))
        if st.button("Salvar Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1, "p5":p5})
            st.success("Porter Salvo!")
    with t2:
        st.subheader("Cálculo de HHI")
        s1 = st.number_input("Share Líder %", 0.0, 100.0, 30.0)
        s2 = st.number_input("Share 2º %", 0.0, 100.0, 20.0)
        rest = 100 - (s1+s2)
        h_calc = s1**2 + s2**2 + rest**2
        st.metric("HHI", int(h_calc))
        if st.button("Salvar HHI"):
            save_data(st.session_state.group, "hhi", f"{s1},{s2},{rest}")

# --- 6. MONETÁRIO ---
elif menu == "6. Módulo Macro (Monetário)":
    st.title("🏦 Stress Test Monetário")
    dre_d = data.get('dre', {})
    rec = st.number_input("Receita Bruta", value=safe_float(dre_d.get('receita', 1000000)))
    cus = st.number_input("Custos", value=safe_float(dre_d.get('custos', 700000)))
    div = st.number_input("Dívida", value=safe_float(dre_d.get('divida', 400000)))
    if st.button("Salvar Macro"):
        save_data(st.session_state.group, "dre", {"receita":rec, "custos":cus, "divida":div})

# --- 7. MÓDULO FINANCEIRO (GUIA COMPLETO) ---
elif menu == "7. Módulo Financeiro & Valor":
    st.title("💰 Viabilidade, Custo de Capital e Valor")
    
    tab1, tab2, tab3 = st.tabs(["WACC: O Custo de Capital", "EVA: Criação de Valor", "Valuation: Valor do Negócio"])
    
    w_d = data.get('wacc', {})
    
    with tab1:
        st.markdown('<div class="guide-text"><b>Orientação:</b> O WACC é a "taxa mínima" que a empresa deve render para ser viável. Ele pondera quanto custa o dinheiro dos sócios (Ke) e o dinheiro dos bancos (Kd).</div>', unsafe_allow_html=True)
        
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.subheader("Inputs de Capital")
            ke = st.number_input("Custo de Capital Próprio - Ke (%)", value=safe_float(w_d.get('ke', 15.0)), help="Expectativa de retorno dos sócios.")
            kd = st.number_input("Custo da Dívida - Kd (%)", value=safe_float(w_d.get('kd', 12.0)), help="Juros médios pagos aos bancos.")
            eq = st.slider("Estrutura de Capital (% de Capital Próprio)", 0, 100, int(safe_float(w_d.get('eq_ratio', 60)))) / 100
            
            # Cálculo WACC
            w_calc = (eq * (ke/100)) + ((1 - eq) * (kd/100) * 0.66)
            st.markdown(f'<span class="formula-text">WACC = ({eq:.2f} * {ke}%) + ({1-eq:.2f} * {kd}% * 0.66)</span>', unsafe_allow_html=True)
            st.metric("WACC Final", f"{w_calc*100:.2f}%")
        
        with col_w2:
            st.subheader("Interpretando o WACC")
            st.info(f"O WACC de **{w_calc*100:.2f}%** significa que para cada R$ 100,00 investidos, a empresa precisa gerar pelo menos R$ {w_calc*100:.2f} de lucro operacional apenas para 'ficar no zero a zero' com investidores e bancos.")
            if w_calc*100 > 20:
                st.warning("Atenção: Um WACC acima de 20% é considerado alto, exigindo que o negócio tenha margens muito elevadas para ser viável.")

    with tab2:
        st.markdown('<div class="guide-text"><b>Orientação:</b> O EVA (Lucro Econômico) mostra se a empresa está realmente ficando rica ou se seria melhor fechar as portas e investir o dinheiro na Selic.</div>', unsafe_allow_html=True)
        
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            roi = st.number_input("ROI da Empresa (%)", value=safe_float(w_d.get('roi', 18.0)), help="Retorno sobre o Investimento gerado pela operação.")
            # EVA comparado ao WACC (Visão Corporativa)
            eva_result = roi - (w_calc * 100)
            
            st.markdown(f'<span class="formula-text">EVA = ROI ({roi}%) - WACC ({w_calc*100:.2f}%)</span>', unsafe_allow_html=True)
            st.metric("EVA (Economic Value Added)", f"{eva_result:.2f}%", delta=f"{eva_result:.2f}%")
        
        with col_e2:
            st.subheader("Análise de Valor")
            if eva_result > 0:
                st.success(f"✅ **Criação de Valor:** O ROI ({roi}%) é maior que o custo de capital. A empresa está gerando um excedente real de {eva_result:.2f}% além do que é exigido pelo mercado.")
            else:
                st.error(f"🚨 **Destruição de Valor:** A empresa rende menos que o seu custo. Mesmo que haja lucro na contabilidade, economicamente os sócios estão perdendo dinheiro, pois o capital poderia estar rendendo mais em outro lugar.")
        
        if st.button("Salvar Dados Financeiros"):
            save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":w_calc*100})

    with tab3:
        st.markdown('<div class="guide-text"><b>Orientação:</b> O Valuation projeta quanto a empresa vale hoje considerando toda a sua capacidade de gerar dinheiro no futuro (Perpetuidade).</div>', unsafe_allow_html=True)
        
        g = st.slider("Crescimento Perpétuo - g (%)", 0.0, 10.0, safe_float(w_d.get('g_growth', 3.0)), help="Quanto a empresa crescerá por ano para sempre.")
        
        # Puxa EBITDA da DRE
        ebitda_base = safe_float(data.get('dre', {}).get('receita')) - safe_float(data.get('dre', {}).get('custos'))
        w_base = w_calc
        g_base = g / 100
        
        if w_base > g_base:
            enterprise_value = (ebitda_base * (1 + g_base)) / (w_base - g_base)
            st.markdown(f'<span class="formula-text">Valor = EBITDA (R$ {ebitda_base:,.2f}) * (1 + {g}%) / ({w_calc*100:.2f}% - {g}%)</span>', unsafe_allow_html=True)
            st.metric("Enterprise Value Estimado", f"R$ {enterprise_value:,.2f}")
            
            st.info(f"**Interpretação:** Com base na geração de caixa atual e no risco (WACC), este negócio vale aproximadamente **R$ {enterprise_value:,.2f}**. Este é o valor que um investidor pagaria para comprar a empresa inteira.")
        else:
            st.error("Erro Crítico: A taxa de crescimento (g) não pode ser maior que o WACC. Isso implicaria que a empresa se tornará maior que a economia mundial, o que é matematicamente impossível no modelo de Gordon.")

# --- 8. RELATÓRIO ---
elif menu == "8. Relatório Final":
    st.title("📄 Relatório Consolidado")
    st.divider()
    info = data.get('company_info', {})
    st.header(f"Projeto: {info.get('nome', 'N/A')}")
    st.subheader("Diário de Bordo")
    st.info(data.get('diary', {}).get('q1', 'Sem notas.'))
    st.button("Exportar (Ctrl+P)")
