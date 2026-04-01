import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Hub - Master BI", layout="wide", initial_sidebar_state="expanded")

# --- CSS WHITELABEL & DESIGN ACADÊMICO ELITE ---
st.markdown("""
    <style>
    /* Esconder elementos do Streamlit */
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}

    /* Design Profissional */
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 1px solid #e0e0e0; min-width: 310px !important; }
    h1, h2, h3 { color: #002e5d; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
    
    /* Componentes Visuais */
    .risk-card { padding: 20px; border-radius: 12px; text-align: center; color: white; font-weight: bold; margin-bottom: 10px; border: 1px solid rgba(0,0,0,0.1); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .insight-box { background-color: #ffffff; padding: 20px; border-left: 6px solid #0052cc; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
    .formula-text { font-family: 'Courier New', Courier, monospace; background-color: #f4f4f4; padding: 10px; border-radius: 5px; font-size: 0.85em; color: #d63384; border: 1px solid #ddd; display: block; margin: 10px 0;}
    .guide-text { font-size: 0.95em; color: #444; line-height: 1.6; background: #fffbe6; padding: 15px; border-radius: 5px; border: 1px solid #ffe58f; margin-bottom: 15px;}
    .swot-card { padding: 15px; border-radius: 8px; height: 130px; color: white; font-size: 0.85em; overflow-y: auto; margin-bottom: 10px; }
    .stButton>button { background-color: #0052cc; color: white; border-radius: 6px; width: 100%; font-weight: bold; height: 45px; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO SUPABASE ---
try:
    URL: str = st.secrets["SUPABASE_URL"]
    KEY: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("Erro Crítico de Conexão: Verifique os Secrets.")
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
    st.subheader("Login de Consultoria Acadêmica")
    col_l1, col_l2 = st.columns([1, 2])
    with col_l1:
        group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
        if st.text_input("Senha", type="password") == "eco123" and st.button("Acessar Plataforma"):
            st.session_state.auth, st.session_state.group = True, group
            st.rerun()
    st.stop()

data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    st.header("🌍 Conjuntura Global")
    selic_ref = st.number_input("Selic de Referência (%)", value=10.75, step=0.25)
    st.divider()
    menu = st.radio("ETAPAS DA CONSULTORIA", [
        "1. Dashboard Executivo", 
        "2. Identificação da Equipe", 
        "3. Perfil da Empresa",
        "4. Guia de Entrevista (Campo)", 
        "5. Módulo Micro (Estratégia)", 
        "6. Módulo Macro (Monetário)", 
        "7. Módulo Financeiro & Valor", 
        "8. Relatório Final"
    ])
    st.divider()
    if st.button("Logout / Sair"):
        st.session_state.auth = False
        st.rerun()

# --- 1. DASHBOARD ---
if menu == "1. Dashboard Executivo":
    st.title("📈 Dashboard Inteligente de BI")
    info = data.get('company_info', {})
    st.markdown(f'<div class="insight-box"><h4>Cliente: {info.get("nome", "Aguardando Cadastro")}</h4><p>Resumo automatizado de riscos econômicos e avaliação de mercado.</p></div>', unsafe_allow_html=True)
    
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

    st.divider()
    cola, colb = st.columns(2)
    with cola:
        st.subheader("💎 Enterprise Value (DCF)")
        if (w_final/100) > g_val:
            val_est = (ebitda * (1 + g_val)) / ((w_final/100) - g_val)
            st.metric("Valor da Empresa", f"R$ {val_est:,.2f}")
        else: st.warning("Valuation pendente (WACC > G necessário).")
    with colb:
        st.subheader("🎯 Resumo SWOT")
        sw = data.get('swot', {})
        st.write(f"**Força:** {sw.get('f', '-')[:60]}...")
        st.write(f"**Ameaça:** {sw.get('a', '-')[:60]}...")

# --- 2. IDENTIFICAÇÃO ---
elif menu == "2. Identificação da Equipe":
    st.title("👥 Equipe de Consultores")
    st.markdown('<div class="guide-text"><b>Orientação:</b> Identifique individualmente os membros da equipe e o professor responsável.</div>', unsafe_allow_html=True)
    part = data.get('participants', {})
    with st.form("f_equipe"):
        c1, c2 = st.columns(2)
        al1 = c1.text_input("Consultor 1 (Líder)", value=part.get('aluno1', ''))
        al2 = c1.text_input("Consultor 2", value=part.get('aluno2', ''))
        al3 = c1.text_input("Consultor 3", value=part.get('aluno3', ''))
        al4 = c2.text_input("Consultor 4", value=part.get('aluno4', ''))
        al5 = c2.text_input("Consultor 5", value=part.get('aluno5', ''))
        prof = c2.text_input("Professor Orientador", value=part.get('professor', ''))
        if st.form_submit_button("Salvar Equipe"):
            save_data(st.session_state.group, "participants", {"aluno1":al1, "aluno2":al2, "aluno3":al3, "aluno4":al4, "aluno5":al5, "professor":prof})
            st.success("Equipe Salva!")

# --- 3. PERFIL EMPRESA ---
elif menu == "3. Perfil da Empresa":
    st.title("🏢 Caracterização do Cliente")
    st.markdown('<div class="guide-text"><b>Orientação:</b> Forneça dados demográficos para contextualizar a consultoria.</div>', unsafe_allow_html=True)
    info = data.get('company_info', {})
    with st.form("f_empresa"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Razão Social / Nome Fantasia", value=info.get('nome', ''))
        setor = c1.selectbox("Setor", ["Varejo", "Indústria", "Serviços", "Agro", "Tech"], index=0)
        fundacao = c1.text_input("Ano de Fundação", value=info.get('fundacao', ''))
        colab = c2.number_input("Nº Funcionários", value=int(safe_float(info.get('colab', 0))))
        produto = c2.text_input("Produto/Serviço Principal", value=info.get('produto', ''))
        desc = st.text_area("Descrição do Modelo de Negócio", value=info.get('desc', ''))
        if st.form_submit_button("Salvar Perfil"):
            save_data(st.session_state.group, "company_info", {"nome":nome, "setor":setor, "fundacao":fundacao, "colab":colab, "produto":produto, "desc":desc})
            st.success("Perfil Atualizado!")

# --- 4. DIÁRIO DE CAMPO ---
elif menu == "4. Guia de Entrevista (Campo)":
    st.title("📔 Diário de Bordo Estruturado")
    st.markdown('<div class="guide-text"><b>Guia:</b> Utilize as perguntas abaixo como roteiro para a entrevista com o empresário.</div>', unsafe_allow_html=True)
    diary = data.get('diary', {})
    with st.form("f_diary"):
        q1 = st.text_area("1. Histórico e Diferencial: Como a empresa começou e por que o cliente compra dela?", value=diary.get('q1', ''))
        q2 = st.text_area("2. Estrutura de Custos e Juros: Como a inflação e as taxas de juros impactam as margens hoje?", value=diary.get('q2', ''))
        q3 = st.text_area("3. Mercado e Concorrência: Quem são os rivais diretos e qual a maior ameaça externa?", value=diary.get('q3', ''))
        q4 = st.text_area("4. Endividamento: A empresa possui empréstimos? Qual o indexador (Selic, IPCA...)?", value=diary.get('q4', ''))
        if st.form_submit_button("Sincronizar Diagnóstico"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2, "q3":q3, "q4":q4})
            st.success("Diário Salvo!")

# --- 5. MICRO ---
elif menu == "5. Módulo Micro (Estratégia)":
    st.title("🔬 Módulo Microeconômico")
    t1, t2, t3 = st.tabs(["5 Forças de Porter", "HHI (Concentração)", "Matriz SWOT"])
    with t1:
        st.subheader("Análise Setorial")
        p = data.get('porter', {})
        p1 = st.slider("Ameaça de Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        p2 = st.slider("Poder dos Fornecedores", 1, 5, int(safe_float(p.get('p2', 3))))
        p3 = st.slider("Poder dos Clientes", 1, 5, int(safe_float(p.get('p3', 3))))
        p5 = st.slider("Rivalidade", 1, 5, int(safe_float(p.get('p5', 3))))
        if st.button("Salvar Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1, "p2":p2, "p3":p3, "p5":p5})
            st.success("Porter Salvo!")
    with t2:
        st.subheader("HHI Guiado")
        s1 = st.number_input("Share Líder %", 0.0, 100.0, 30.0)
        s2 = st.number_input("Share 2º Concorrente %", 0.0, 100.0, 20.0)
        s3 = st.number_input("Share 3º Concorrente %", 0.0, 100.0, 10.0)
        rest = max(0.0, 100.0 - (s1+s2+s3))
        h_calc = s1**2 + s2**2 + s3**2 + rest**2
        st.metric("HHI Final", int(h_calc))
        st.plotly_chart(px.pie(values=[s1, s2, s3, rest], names=["Líder", "2º", "3º", "Outros"], hole=0.4))
        if st.button("Salvar HHI"):
            save_data(st.session_state.group, "hhi", f"{s1},{s2},{s3},{rest}")
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

# --- 6. MONETÁRIO ---
elif menu == "6. Módulo Macro (Monetário)":
    st.title("🏦 Diagnóstico Monetário e Stress Test")
    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_nome = st.selectbox("Indexador da Dívida", ["Selic", "TJLP", "IGP-M", "IPCA", "Outro"], index=0)
        idx_val = st.number_input(f"Valor do {idx_nome} (%)", value=safe_float(dre_d.get('idx_valor', 10.75)))
        spread = st.number_input("Spread Bancário (+%)", value=safe_float(dre_d.get('spread', 2.0)))
        rec = st.number_input("Receita Bruta", value=safe_float(dre_d.get('receita', 1000000)))
        cus = st.number_input("Custos Operacionais", value=safe_float(dre_d.get('custos', 700000)))
        div = st.number_input("Dívida Total", value=safe_float(dre_d.get('divida', 400000)))
        if st.button("Salvar Macro"):
            save_data(st.session_state.group, "dre", {"idx_nome":idx_nome, "idx_valor":idx_val, "spread":spread, "receita":rec, "custos":cus, "divida":div})
            st.rerun()
    with c2:
        ebitda = rec - cus
        sim = st.slider(f"Simular {idx_nome} (%)", 0.0, 30.0, idx_val)
        st.metric("Lucro Estimado", f"R$ {ebitda - (div * (sim+spread)/100):,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div*(s+spread)/100) for s in range(0,31)], title="Ponto de Ruptura")
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig)

# --- 7. FINANCEIRO ---
elif menu == "6. Módulo Financeiro & Valor": # Ajuste de índice manual para evitar conflito de menu
    menu = "6. Módulo Financeiro & Valor"

if menu == "6. Módulo Financeiro & Valor":
    st.title("💰 Viabilidade, WACC e Valuation")
    tab1, tab2 = st.tabs(["WACC & EVA (Didático)", "Valuation por Perpetuidade"])
    w_d = data.get('wacc', {})
    
    with tab1:
        with st.expander("🎓 Saiba mais: Fórmulas de Valor"):
            st.markdown('<span class="formula-text">WACC = (Equity/Total * Ke) + (Debt/Total * Kd * 0.66)</span>', unsafe_allow_html=True)
            st.markdown('<span class="formula-text">EVA = ROI - WACC</span>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            ke = st.number_input("Custo Cap. Próprio - Ke (%)", value=safe_float(w_d.get('ke', 15.0)))
            kd = st.number_input("Custo da Dívida - Kd (%)", value=safe_float(w_d.get('kd', 12.0)))
            eq = st.slider("Equity Ratio (%)", 0, 100, int(safe_float(w_d.get('eq_ratio', 60)))) / 100
            w_calc = (eq * (ke/100)) + ((1-eq) * (kd/100) * 0.66)
            st.metric("WACC Final", f"{w_calc*100:.2f}%")
        with c2:
            roi = st.number_input("ROI da Empresa (%)", value=safe_float(w_d.get('roi', 18.0)))
            eva = roi - (w_calc * 100)
            st.metric("EVA (Criação de Valor)", f"{eva:.2f}%")
            if st.button("Salvar Financeiro"):
                save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":w_calc*100})

    with tab2:
        g = st.slider("Crescimento Perpétuo - g (%)", 0.0, 10.0, safe_float(w_d.get('g_growth', 3.0)))
        if st.button("Sincronizar g"):
            save_data(st.session_state.group, "wacc", {**w_d, "g_growth": g})
            st.rerun()
        ebitda_v = safe_float(data.get('dre', {}).get('receita')) - safe_float(data.get('dre', {}).get('custos'))
        w_base = safe_float(w_d.get('wacc_final')) / 100
        g_base = g / 100
        if w_base > g_base:
            val = (ebitda_v * (1 + g_base)) / (w_base - g_base)
            st.metric("Enterprise Value", f"R$ {val:,.2f}")
        else: st.error("Erro: WACC deve ser > g.")

# --- 8. RELATÓRIO ---
elif menu == "7. Relatório Final":
    st.title("📄 Relatório Consolidado")
    st.write(f"Empresa: {data.get('company_info', {}).get('nome')} | Grupo: {st.session_state.group}")
    st.divider()
    st.subheader("Histórico do Diário")
    st.info(data.get('diary', {}).get('q1', 'Nenhum registro.'))
    st.button("Imprimir Relatório (Ctrl+P)")
