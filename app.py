import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Intelligence", layout="wide", initial_sidebar_state="expanded")

# --- CSS WHITELABEL & DESIGN MINIMALISTA (ELITE) ---
st.markdown("""
    <style>
    /* Ocultar elementos técnicos */
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}

    /* Typography & Core Design */
    .stApp { background-color: #f8fafc; font-family: 'Inter', -apple-system, sans-serif; }
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; min-width: 300px !important; }
    
    /* Menu Lateral Customizado */
    [data-testid="stSidebar"] .stMarkdown h2 { color: #f8fafc; font-size: 1.2rem; padding-bottom: 0; text-align: center; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap: 10px; padding-top: 20px; }
    
    /* Estilização do Radio (Links do Menu) */
    [data-testid="stSidebar"] .stRadio label { 
        color: #94a3b8 !important; 
        font-weight: 500 !important; 
        font-size: 0.95rem !important;
        border-radius: 6px;
        padding: 8px 12px !important;
        transition: 0.3s;
    }
    [data-testid="stSidebar"] .stRadio label:hover { color: #ffffff !important; background-color: #1e293b; }
    [data-testid="stSidebar"] .stRadio div[data-testid="stMarkdownContainer"] p { font-size: 1rem; }

    /* Headers e Cards */
    h1, h2, h3 { color: #0f172a; font-weight: 800; letter-spacing: -0.04em; }
    .risk-card { padding: 22px; border-radius: 8px; text-align: center; color: white; font-weight: 600; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    .insight-box { background-color: #ffffff; padding: 25px; border-left: 4px solid #3b82f6; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 25px; border-top: 1px solid #f1f5f9; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; }
    
    /* Fórmulas e Botões */
    .formula-text { font-family: 'SF Mono', 'Roboto Mono', monospace; background-color: #f1f5f9; padding: 12px; border-radius: 4px; font-size: 0.85em; color: #334155; border: 1px solid #e2e8f0; display: block; margin: 12px 0; }
    .guide-text { font-size: 0.9em; color: #475569; line-height: 1.6; background: #eff6ff; padding: 14px; border-radius: 6px; border: 1px solid #dbeafe; margin-bottom: 20px;}
    .stButton>button { background-color: #2563eb; color: white; border-radius: 6px; width: 100%; font-weight: 600; height: 48px; border: none; transition: 0.2s; }
    .stButton>button:hover { background-color: #1d4ed8; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO BANCO CENTRAL (SELIC META 432) ---
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
    st.error("Erro de comunicação com o servidor de dados.")
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
    st.markdown("<h2 style='text-align: center; color: #0f172a; padding-top: 50px;'>ECOSTRATEGY INTELLIGENCE</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.6, 1])
    with col_l2:
        try: st.image("logo.png", use_container_width=True)
        except: pass
        group = st.selectbox("Selecione sua Unidade", ["Grupo 1", "Grupo 2", "Grupo 3"])
        pwd = st.text_input("Credencial de Acesso", type="password")
        if st.button("Acessar Plataforma"):
            if pwd == "eco123":
                st.session_state.auth, st.session_state.group = True, group
                st.rerun()
    st.stop()

data = load_data(st.session_state.group)

# --- SIDEBAR (DESIGN CORPORATIVO DARK/NAVY) ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    
    st.markdown(f"<h2>{st.session_state.group.upper()}</h2>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("<p style='font-size: 0.75rem; font-weight: 700; color: #64748b; letter-spacing: 0.1em; margin-bottom: 5px;'>MACRO BENCHMARK</p>", unsafe_allow_html=True)
    selic_meta = get_live_selic()
    st.markdown(f"<p style='color: #10b981; font-size: 0.85rem; margin-bottom: 15px;'>Selic Meta Oficial: {selic_meta}%</p>", unsafe_allow_html=True)
    selic_ref = st.number_input("Selic de Trabalho (%)", value=selic_meta, step=0.25)
    
    st.divider()
    st.markdown("<p style='font-size: 0.75rem; font-weight: 700; color: #64748b; letter-spacing: 0.1em; margin-bottom: 5px;'>NAVEGAÇÃO</p>", unsafe_allow_html=True)
    
    menu = st.radio("MENU", [
        "01 DASHBOARD EXECUTIVO", 
        "02 GOVERNANÇA E EQUIPE", 
        "03 PERFIL CORPORATIVO",
        "04 DIAGNÓSTICO DE CAMPO", 
        "05 ANÁLISE ESTRATÉGICA", 
        "06 CENÁRIO MONETÁRIO", 
        "07 VIABILIDADE E VALOR", 
        "08 RELATÓRIO FINAL"
    ], label_visibility="collapsed")
    
    st.divider()
    if st.button("Encerrar Sessão"):
        st.session_state.auth = False
        st.rerun()

# --- LÓGICA DAS ETAPAS ---

if menu == "01 DASHBOARD EXECUTIVO":
    st.title("Executive Management Dashboard")
    info = data.get('company_info', {})
    st.markdown(f'<div class="insight-box"><h4>Unidade Analisada: {info.get("nome", "Não Identificada")}</h4><p>Sumário de indicadores críticos de risco, concentração e valor gerado.</p></div>', unsafe_allow_html=True)
    
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
            mode = "gauge+number", value = score, title = {'text': "Health Score Index", 'font': {'size': 18}},
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#2563eb"},
                     'steps': [{'range': [0, 50], 'color': "#ef4444"}, {'range': [50, 75], 'color': "#f59e0b"}, {'range': [75, 100], 'color': "#10b981"}]}))
        st.plotly_chart(fig_health, use_container_width=True)

    with col_sem:
        c1, c2, c3 = st.columns(3)
        with c1:
            color = "#10b981" if idx_total < break_even else "#ef4444" if break_even > 0 else "#94a3b8"
            st.markdown(f'<div class="risk-card" style="background:{color}">CRÉDITO<br>{idx_total:.1f}%</div>', unsafe_allow_html=True)
        with c2:
            m_color = "#10b981" if hhi_val < 1500 else "#f59e0b" if hhi_val < 2500 else "#ef4444"
            st.markdown(f'<div class="risk-card" style="background:{m_color}">MERCADO<br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
        with c3:
            v_color = "#10b981" if roi > w_final else "#ef4444"
            st.markdown(f'<div class="risk-card" style="background:{v_color}">VALOR (EVA)<br>ROI: {roi}%</div>', unsafe_allow_html=True)

elif menu == "02 GOVERNANÇA E EQUIPE":
    st.title("Governança do Projeto")
    st.markdown('<div class="guide-text">Registre os consultores responsáveis e o professor orientador.</div>', unsafe_allow_html=True)
    part = data.get('participants', {})
    with st.form("f_eq"):
        c1, c2 = st.columns(2)
        al1 = c1.text_input("Consultor 1 (Líder)", value=part.get('aluno1', ''))
        al2 = c1.text_input("Consultor 2", value=part.get('aluno2', ''))
        al3 = c1.text_input("Consultor 3", value=part.get('aluno3', ''))
        al4 = c2.text_input("Consultor 4", value=part.get('aluno4', ''))
        al5 = c2.text_input("Consultor 5", value=part.get('aluno5', ''))
        prof = c2.text_input("Professor Orientador", value=part.get('professor', ''))
        if st.form_submit_button("Sincronizar Dados"):
            save_data(st.session_state.group, "participants", {"aluno1":al1, "aluno2":al2, "aluno3":al3, "aluno4":al4, "aluno5":al5, "professor":prof})
            st.success("Dados de equipe atualizados.")

elif menu == "03 PERFIL CORPORATIVO":
    st.title("Perfil do Cliente")
    info = data.get('company_info', {})
    with st.form("f_emp"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Razão Social", value=info.get('nome', ''))
        setor = c1.selectbox("Setor", ["Varejo", "Indústria", "Serviços", "Agro", "Tech"], index=0)
        fundacao = c1.text_input("Ano Fundação", value=info.get('fundacao', ''))
        colab = c2.number_input("Nº Funcionários", value=int(safe_float(info.get('colab', 0))))
        desc = st.text_area("Modelo de Negócio", value=info.get('desc', ''))
        if st.form_submit_button("Salvar Perfil"):
            save_data(st.session_state.group, "company_info", {"nome":nome, "setor":setor, "fundacao":fundacao, "colab":colab, "desc":desc})
            st.success("Perfil Sincronizado.")

elif menu == "04 DIAGNÓSTICO DE CAMPO":
    st.title("Guia de Entrevista Semiestruturada")
    diary = data.get('diary', {})
    with st.form("f_dia"):
        q1 = st.text_area("1. Diferencial Competitivo e Estratégia", value=diary.get('q1', ''))
        q2 = st.text_area("2. Impacto de Juros e Inflação no Caixa", value=diary.get('q2', ''))
        q3 = st.text_area("3. Estrutura de Mercado e Concorrência", value=diary.get('q3', ''))
        q4 = st.text_area("4. Gestão de Endividamento", value=diary.get('q4', ''))
        if st.form_submit_button("Salvar Diagnóstico"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2, "q3":q3, "q4":q4})
            st.success("Notas salvas.")

elif menu == "05 ANÁLISE ESTRATÉGICA":
    st.title("Estratégia e Inteligência Competitiva")
    t1, t2, t3 = st.tabs(["5 Forças de Porter", "Concentração HHI", "Matriz SWOT"])
    with t1:
        p = data.get('porter', {})
        p1 = st.slider("Ameaça de Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        p2 = st.slider("Poder dos Fornecedores", 1, 5, int(safe_float(p.get('p2', 3))))
        p3 = st.slider("Poder dos Clientes", 1, 5, int(safe_float(p.get('p3', 3))))
        p5 = st.slider("Rivalidade Rivais", 1, 5, int(safe_float(p.get('p5', 3))))
        if st.button("Salvar Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1,"p2":p2,"p3":p3,"p5":p5})
            st.success(" Porter Salvo.")
    with t2:
        s1 = st.number_input("Share Líder %", 0.0, 100.0, 30.0)
        s2 = st.number_input("Share 2º %", 0.0, 100.0, 20.0)
        s3 = st.number_input("Share 3º %", 0.0, 100.0, 10.0)
        rest = max(0.0, 100.0 - (s1+s2+s3))
        h_calc = s1**2 + s2**2 + s3**2 + rest**2
        st.metric("HHI Final", int(h_calc))
        st.plotly_chart(px.pie(values=[s1,s2,s3,rest], names=["Líder","2º","3º","Outros"], hole=0.4))
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", f"{s1},{s2},{s3},{rest}")
    with t3:
        sw = data.get('swot', {})
        with st.form("f_sw"):
            f = st.text_area("Forças", value=sw.get('f', ''))
            fra = st.text_area("Fraquezas", value=sw.get('fra', ''))
            o = st.text_area("Oportunidades", value=sw.get('o', ''))
            a = st.text_area("Ameaças", value=sw.get('a', ''))
            if st.form_submit_button("Salvar SWOT"):
                save_data(st.session_state.group, "swot", {"f":f, "fra":fra, "o":o, "a":a})
                st.rerun()

elif menu == "06 CENÁRIO MONETÁRIO":
    st.title("Stress Test e Gestão de Juros")
    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_nome = st.selectbox("Indexador", ["Selic", "TJLP", "IPCA", "IGP-M"], index=0)
        idx_val = st.number_input(f"Taxa {idx_nome} %", value=safe_float(dre_d.get('idx_valor', selic_ref)))
        spread = st.number_input("Spread Bancário %", value=safe_float(dre_d.get('spread', 2.0)))
        rec = st.number_input("Receita Bruta", value=safe_float(dre_d.get('receita', 1000000)))
        cus = st.number_input("Custos Operacionais", value=safe_float(dre_d.get('custos', 700000)))
        div = st.number_input("Dívida Total", value=safe_float(dre_d.get('divida', 400000)))
        if st.button("Salvar Macro"):
            save_data(st.session_state.group, "dre", {"idx_nome":idx_nome, "idx_valor":idx_val, "spread":spread, "receita":rec, "custos":cus, "divida":div})
            st.rerun()
    with c2:
        ebitda = rec - cus
        sim = st.slider(f"Simular {idx_nome} %", 0.0, 30.0, idx_val)
        st.metric("Lucro Líquido na Simulação", f"R$ {ebitda - (div*(sim+spread)/100):,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div*(s+spread)/100) for s in range(0,31)], title="Análise de Ponto de Ruptura")
        fig.add_hline(y=0, line_dash="dash", line_color="#ef4444")
        st.plotly_chart(fig)

elif menu == "07 VIABILIDADE E VALOR":
    st.title("Valuation e Custo de Capital")
    with st.expander("🎓 Metodologia Acadêmica"):
        st.markdown("**WACC:** Custo Médio Ponderado de Capital. <span class='formula-text'>WACC = (E/V * Ke) + (D/V * Kd * 0.66)</span>", unsafe_allow_html=True)
        st.markdown("**Gordon Growth:** Valor da Perpetuidade. <span class='formula-text'>EV = EBITDA(1+g) / (WACC - g)</span>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["WACC & EVA", "Valuation DCF"])
    w_d = data.get('wacc', {})
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            ke = st.number_input("Ke (Retorno Sócios %)", value=safe_float(w_d.get('ke', 15.0)))
            kd = st.number_input("Kd (Custo Bancos %)", value=safe_float(w_d.get('kd', 12.0)))
            eq = st.slider("Equity %", 0, 100, int(safe_float(w_d.get('eq_ratio', 60)))) / 100
            w_calc = (eq * (ke/100)) + ((1-eq) * (kd/100) * 0.66)
            st.metric("WACC Final", f"{w_calc*100:.2f}%")
        with c2:
            roi = st.number_input("ROI Operacional %", value=safe_float(w_d.get('roi', 18.0)))
            eva = roi - (w_calc * 100)
            st.metric("EVA (Spread de Valor)", f"{eva:.2f}%")
            if st.button("Salvar Resultados"):
                save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":w_calc*100})
    with t2:
        g = st.slider("Crescimento Perpétuo (g) %", 0.0, 10.0, safe_float(w_d.get('g_growth', 3.0)))
        if st.button("Sincronizar g"): save_data(st.session_state.group, "wacc", {**w_d, "g_growth": g})
        ebit_v = safe_float(data.get('dre', {}).get('receita')) - safe_float(data.get('dre', {}).get('custos'))
        w_base = safe_float(w_d.get('wacc_final')) / 100
        g_v = g / 100
        if w_base > g_v:
            val = (ebit_v * (1 + g_v)) / (w_base - g_v)
            st.metric("Enterprise Value", f"R$ {val:,.2f}")
        else: st.error("Erro de inconsistência: WACC deve ser > g.")

elif menu == "08 RELATÓRIO FINAL":
    st.title("Executive Report")
    st.write(f"Unidade: {st.session_state.group} | Cliente: {data.get('company_info', {}).get('nome', 'N/A')}")
    st.divider()
    st.button("Exportar Consultoria (Ctrl+P)")
