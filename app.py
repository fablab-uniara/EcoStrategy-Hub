import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Hub - Master BI", layout="wide", initial_sidebar_state="expanded")

# --- CSS WHITELABEL & DESIGN MASTER ---
st.markdown("""
    <style>
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 1px solid #e0e0e0; min-width: 320px !important; }
    h1, h2, h3 { color: #002e5d; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
    .risk-card { padding: 15px; border-radius: 12px; text-align: center; color: white; font-weight: bold; border: 1px solid rgba(0,0,0,0.1); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .insight-box { background-color: #ffffff; padding: 20px; border-left: 6px solid #0052cc; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
    .formula-text { font-family: 'Courier New', Courier, monospace; background-color: #f8f9fa; padding: 10px; border-radius: 6px; font-size: 0.85em; color: #d63384; border: 1px solid #dee2e6; display: block; margin: 10px 0;}
    .guide-text { font-size: 0.92em; color: #444; line-height: 1.5; background: #fffbe6; padding: 12px; border-radius: 5px; border: 1px solid #ffe58f; margin-bottom: 15px;}
    .swot-card { padding: 12px; border-radius: 8px; height: 110px; color: white; font-size: 0.82em; overflow-y: auto; margin-bottom: 8px; }
    .stButton>button { background-color: #0052cc; color: white; border-radius: 6px; width: 100%; font-weight: bold; height: 45px; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO BUSCA BANCO CENTRAL (API SGS - SELIC META) ---
def get_live_selic():
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        response = requests.get(url, timeout=5)
        return float(response.json()[0]['valor'])
    except:
        return 10.75

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
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        try: st.image("logo.png", width=150)
        except: pass
        group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
        pwd = st.text_input("Senha", type="password")
        if st.button("Acessar Plataforma"):
            if pwd == "eco123":
                st.session_state.auth, st.session_state.group = True, group
                st.rerun()
    st.stop()

data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    st.title(f"📊 {st.session_state.group}")
    st.divider()
    
    st.header("🌐 Macro Real-Time (BCB)")
    selic_meta = get_live_selic()
    st.info(f"Selic Meta (COPOM): {selic_meta}% a.a.")
    selic_ref = st.number_input("Selic de Trabalho (%)", value=selic_meta, step=0.25)
    
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
    ], label_visibility="collapsed")
    
    st.divider()
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# --- 1. DASHBOARD ---
if menu == "1. Dashboard Executivo":
    st.title("📈 Dashboard Geral de Inteligência")
    info = data.get('company_info', {})
    st.markdown(f'<div class="insight-box"><h4>Cliente: {info.get("nome", "Pendente")}</h4><p>Nota consolidada baseada em Risco de Crédito, Mercado e Criação de Valor.</p></div>', unsafe_allow_html=True)
    
    dre_d = data.get('dre', {})
    ebitda = safe_float(dre_d.get('receita')) - safe_float(dre_d.get('custos'))
    divida = safe_float(dre_d.get('divida'))
    idx_total = safe_float(dre_d.get('idx_valor')) + safe_float(dre_d.get('spread'))
    break_even = (ebitda / divida * 100) if divida > 0 else 0

    hhi_str = str(data.get('hhi', '0'))
    try: hhi_val = sum([float(x)**2 for x in hhi_str.split(",") if x.strip()])
    except: hhi_val = 0

    w_d = data.get('wacc', {})
    roi = safe_float(w_d.get('roi'))
    w_final = safe_float(w_d.get('wacc_final', 15.0))
    
    score = 0
    if divida == 0 or idx_total < (ebitda/divida*100 if divida > 0 else 100): score += 40
    if hhi_val < 2500: score += 30
    if roi > w_final: score += 30

    col_gauge, col_sem = st.columns([1.5, 2])
    with col_gauge:
        fig_health = go.Figure(go.Indicator(
            mode = "gauge+number", value = score, title = {'text': "Financial Health Score"},
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#0052cc"},
                     'steps': [{'range': [0, 50], 'color': "#dc3545"}, {'range': [50, 75], 'color': "#ffc107"}, {'range': [75, 100], 'color': "#28a745"}]}))
        st.plotly_chart(fig_health, use_container_width=True)

    with col_sem:
        c1, c2, c3 = st.columns(3)
        with c1:
            color = "#28a745" if idx_total < break_even else "#dc3545" if break_even > 0 else "#6c757d"
            st.markdown(f'<div class="risk-card" style="background:{color}">CRÉDITO<br>{idx_total:.1f}%</div>', unsafe_allow_html=True)
        with c2:
            m_color = "#28a745" if hhi_val < 1500 else "#ffc107" if hhi_val < 2500 else "#dc3545"
            st.markdown(f'<div class="risk-card" style="background:{m_color}">MERCADO<br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
        with c3:
            v_color = "#28a745" if roi > w_final else "#dc3545"
            st.markdown(f'<div class="risk-card" style="background:{v_color}">VALOR (EVA)<br>ROI: {roi}%</div>', unsafe_allow_html=True)

# --- 2. EQUIPE ---
elif menu == "2. Identificação da Equipe":
    st.title("👥 Consultores e Professor")
    part = data.get('participants', {})
    with st.form("f_equipe"):
        c1, c2 = st.columns(2)
        al1 = c1.text_input("Aluno 1 (Líder)", value=part.get('aluno1', ''))
        al2 = c1.text_input("Aluno 2", value=part.get('aluno2', ''))
        al3 = c1.text_input("Aluno 3", value=part.get('aluno3', ''))
        al4 = c2.text_input("Aluno 4", value=part.get('aluno4', ''))
        al5 = c2.text_input("Aluno 5", value=part.get('aluno5', ''))
        prof = c2.text_input("Professor Responsável", value=part.get('professor', ''))
        if st.form_submit_button("Salvar Identificação"):
            save_data(st.session_state.group, "participants", {"aluno1":al1, "aluno2":al2, "aluno3":al3, "aluno4":al4, "aluno5":al5, "professor":prof})
            st.success("Equipe Sincronizada!")

# --- 3. PERFIL ---
elif menu == "3. Perfil da Empresa":
    st.title("🏢 Caracterização Corporativa")
    info = data.get('company_info', {})
    with st.form("f_empresa"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Razão Social", value=info.get('nome', ''))
        setor = c1.selectbox("Setor", ["Varejo", "Indústria", "Serviços", "Agro", "Tech"], index=0)
        fundacao = c1.text_input("Ano Fundação", value=info.get('fundacao', ''))
        colab = c2.number_input("Nº Funcionários", value=int(safe_float(info.get('colab', 0))))
        prod = c2.text_input("Principal Produto", value=info.get('produto', ''))
        desc = st.text_area("Descrição do Negócio", value=info.get('desc', ''))
        if st.form_submit_button("Salvar Perfil"):
            save_data(st.session_state.group, "company_info", {"nome":nome, "setor":setor, "fundacao":fundacao, "colab":colab, "produto":prod, "desc":desc})
            st.success("Perfil Salvo!")

# --- 4. GUIA ENTREVISTA ---
elif menu == "4. Guia de Entrevista (Campo)":
    st.title("📔 Diagnóstico de Campo")
    diary = data.get('diary', {})
    with st.form("f_diary"):
        q1 = st.text_area("1. Qual o diferencial competitivo?", value=diary.get('q1', ''))
        q2 = st.text_area("2. Como a Selic afeta o caixa?", value=diary.get('q2', ''))
        q3 = st.text_area("3. Quem são os rivais?", value=diary.get('q3', ''))
        q4 = st.text_area("4. Qual o indexador da dívida?", value=diary.get('q4', ''))
        if st.form_submit_button("Salvar Diário"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2, "q3":q3, "q4":q4})
            st.success("Salvo!")

# --- 5. MÓDULO MICRO (PORTER/HHI/SWOT RESTAURADO) ---
elif menu == "5. Módulo Micro (Estratégia)":
    st.title("🔬 Estratégia e Concentração")
    t1, t2, t3 = st.tabs(["5 Forças de Porter", "HHI Guiado", "Matriz SWOT"])
    
    with t1:
        p = data.get('porter', {})
        c1, c2 = st.columns(2)
        p1 = c1.slider("Ameaça de Novos Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        p2 = c1.slider("Poder dos Fornecedores", 1, 5, int(safe_float(p.get('p2', 3))))
        p3 = c1.slider("Poder dos Clientes", 1, 5, int(safe_float(p.get('p3', 3))))
        p4 = c2.slider("Ameaça de Substitutos", 1, 5, int(safe_float(p.get('p4', 3))))
        p5 = c2.slider("Rivalidade entre Rivais", 1, 5, int(safe_float(p.get('p5', 3))))
        if st.button("Salvar Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1,"p2":p2,"p3":p3,"p4":p4,"p5":p5})
            st.success("Porter Salvo!")

    with t2:
        s1 = st.number_input("Share Líder %", 0.0, 100.0, 30.0)
        s2 = st.number_input("Share 2º %", 0.0, 100.0, 20.0)
        s3 = st.number_input("Share 3º %", 0.0, 100.0, 10.0)
        s4 = st.number_input("Share 4º %", 0.0, 100.0, 5.0)
        rest = max(0.0, 100.0 - (s1+s2+s3+s4))
        h_calc = s1**2 + s2**2 + s3**2 + s4**2 + rest**2
        st.metric("HHI Final", int(h_calc))
        st.plotly_chart(px.pie(values=[s1,s2,s3,s4,rest], names=["Líder","2º","3º","4º","Outros"], hole=0.4))
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", f"{s1},{s2},{s3},{s4},{rest}")

    with t3:
        sw = data.get('swot', {})
        with st.form("f_sw"):
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

# --- 6. MACRO ---
elif menu == "6. Módulo Macro (Monetário)":
    st.title("🏦 Cenário Monetário")
    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_nome = st.selectbox("Indexador", ["Selic", "TJLP", "IPCA", "IGP-M"], index=0)
        idx_val = st.number_input(f"Valor {idx_nome} %", value=safe_float(dre_d.get('idx_valor', selic_ref)))
        spread = st.number_input("Spread + %", value=safe_float(dre_d.get('spread', 2.0)))
        rec = st.number_input("Receita Bruta", value=safe_float(dre_d.get('receita', 1000000)))
        cus = st.number_input("Custos", value=safe_float(dre_d.get('custos', 700000)))
        div = st.number_input("Dívida", value=safe_float(dre_d.get('divida', 400000)))
        if st.button("Salvar Cenário"):
            save_data(st.session_state.group, "dre", {"idx_nome":idx_nome, "idx_valor":idx_val, "spread":spread, "receita":rec, "custos":cus, "divida":div})
            st.rerun()
    with c2:
        ebitda = rec - cus
        sim = st.slider(f"Simular {idx_nome} %", 0.0, 30.0, idx_val)
        st.metric("Lucro Estimado", f"R$ {ebitda - (div*(sim+spread)/100):,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div*(s+spread)/100) for s in range(0,31)], title="Análise de Ponto de Ruptura")
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig)

# --- 7. FINANCEIRO (EXPLICAÇÕES INTEGRADAS) ---
elif menu == "7. Módulo Financeiro & Valor":
    st.title("💰 Viabilidade Econômica e Valor")
    
    with st.expander("🎓 Saiba Mais: Fórmulas Financeiras"):
        st.markdown("**1. WACC (Custo de Capital):** <span class='formula-text'>WACC = (Equity/V * Ke) + (Debt/V * Kd * 0.66)</span>", unsafe_allow_html=True)
        st.markdown("**2. EVA (Criação de Valor):** <span class='formula-text'>EVA = ROI - WACC</span>", unsafe_allow_html=True)
        st.markdown("**3. Gordon (Valuation):** <span class='formula-text'>EV = EBITDA(1+g) / (WACC - g)</span>", unsafe_allow_html=True)

    t1, t2 = st.tabs(["WACC & EVA", "Simulador Valuation"])
    w_d = data.get('wacc', {})
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            ke = st.number_input("Ke %", value=safe_float(w_d.get('ke', 15.0)))
            kd = st.number_input("Kd %", value=safe_float(w_d.get('kd', 12.0)))
            eq = st.slider("Equity %", 0, 100, int(safe_float(w_d.get('eq_ratio', 60)))) / 100
            w_calc = (eq * (ke/100)) + ((1-eq) * (kd/100) * 0.66)
            st.metric("WACC Final", f"{w_calc*100:.2f}%")
        with c2:
            roi = st.number_input("ROI Empresa %", value=safe_float(w_d.get('roi', 18.0)))
            eva = roi - (w_calc * 100)
            st.metric("EVA", f"{eva:.2f}%")
            if st.button("Salvar Financeiro"):
                save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":w_calc*100})
    with t2:
        st.info("**O que é 'g'?** Taxa de crescimento na perpetuidade (estimativa do consultor).")
        g = st.slider("Crescimento Perpétuo (g) %", 0.0, 10.0, safe_float(w_d.get('g_growth', 3.0)))
        if st.button("Salvar g"): save_data(st.session_state.group, "wacc", {**w_d, "g_growth": g})
        
        ebit_v = safe_float(data.get('dre', {}).get('receita')) - safe_float(data.get('dre', {}).get('custos'))
        w_base = safe_float(w_d.get('wacc_final')) / 100
        g_v = g / 100
        if w_base > g_v:
            val = (ebit_v * (1 + g_v)) / (w_base - g_v)
            st.metric("Enterprise Value", f"R$ {val:,.2f}")
            st.latex(r"EV = \frac{EBITDA \times (1 + g)}{WACC - g}")
        else: st.error("WACC deve ser > g.")

# --- 8. RELATÓRIO ---
elif menu == "8. Relatório Final":
    st.title("📄 Relatório Consolidado")
    st.write(f"Empresa: {data.get('company_info', {}).get('nome', 'N/A')}")
    st.button("Exportar / Imprimir (Ctrl + P)")
