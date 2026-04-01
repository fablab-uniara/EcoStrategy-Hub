import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Hub - Master BI", layout="wide", initial_sidebar_state="expanded")

# --- CSS WHITELABEL & DESIGN CORPORATIVO (BLOOMBERG STYLE) ---
st.markdown("""
    <style>
    /* Ocultar elementos técnicos */
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}

    /* Typography & Background */
    .stApp { background-color: #f4f7f9; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e0e6ed; min-width: 300px !important; }
    
    /* Headers Sóbrios */
    h1, h2, h3 { color: #1a3353; font-weight: 700; letter-spacing: -0.02em; }
    
    /* Cards de BI Estilo Terminal */
    .risk-card { padding: 22px; border-radius: 8px; text-align: center; color: white; font-weight: 600; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .insight-box { background-color: #ffffff; padding: 25px; border-left: 4px solid #1a3353; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); margin-bottom: 25px; border-top: 1px solid #eee; border-right: 1px solid #eee; border-bottom: 1px solid #eee; }
    
    /* Fórmulas e Guias Acadêmicos */
    .formula-text { font-family: 'SF Mono', 'Roboto Mono', monospace; background-color: #fdfdfd; padding: 12px; border-radius: 4px; font-size: 0.88em; color: #2c3e50; border: 1px solid #eaedf2; display: block; margin: 12px 0; }
    .guide-text { font-size: 0.9em; color: #5a6b82; line-height: 1.6; background: #f0f4f8; padding: 14px; border-radius: 6px; border: 1px solid #d1d9e6; margin-bottom: 20px;}
    
    /* Botões de Ação */
    .stButton>button { background-color: #1a3353; color: white; border-radius: 4px; width: 100%; font-weight: 600; height: 48px; border: none; transition: all 0.2s ease; }
    .stButton>button:hover { background-color: #2c4a70; transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    
    /* Inputs */
    .stNumberInput, .stTextInput { border-radius: 4px; }
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
    st.error("Erro de Conexão com o Servidor de Dados.")
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
    st.title("EcoStrategy Intelligence")
    col_l1, col_l2, col_l3 = st.columns([1, 1.8, 1])
    with col_l2:
        try: st.image("logo.png", width=180)
        except: pass
        group = st.selectbox("Unidade de Consultoria", ["Grupo 1", "Grupo 2", "Grupo 3"])
        pwd = st.text_input("Credencial de Acesso", type="password")
        if st.button("Autenticar Sistema"):
            if pwd == "eco123":
                st.session_state.auth, st.session_state.group = True, group
                st.rerun()
    st.stop()

data = load_data(st.session_state.group)

# --- SIDEBAR (ESTILO CLEAN) ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    
    st.markdown(f"<h2 style='text-align: center;'>{st.session_state.group}</h2>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("**Cenário Macro (SGS-BCB)**")
    selic_meta = get_live_selic()
    st.caption(f"Taxa Selic Meta: {selic_meta}% a.a.")
    selic_ref = st.number_input("Benchmark de Trabalho (%)", value=selic_meta, step=0.25)
    
    st.divider()
    menu = st.radio("SISTEMA DE GESTÃO", [
        "⊞ Dashboard Executivo", 
        "⚇ Equipe e Governança", 
        "🏢 Perfil do Cliente",
        "✎ Diagnóstico de Campo", 
        "⚙ Análise Estratégica", 
        "🌐 Diagnóstico Monetário", 
        "⚖ Viabilidade e Valor", 
        "📋 Relatório Consolidado"
    ])
    
    st.divider()
    if st.button("Finalizar Sessão"):
        st.session_state.auth = False
        st.rerun()

# --- 1. DASHBOARD EXECUTIVO ---
if menu == "⊞ Dashboard Executivo":
    st.title("Executive Dashboard")
    info = data.get('company_info', {})
    st.markdown(f'<div class="insight-box"><h4>Unidade Analisada: {info.get("nome", "Não Identificada")}</h4><p>Sumário executivo de riscos estruturais e métricas de criação de valor econômico.</p></div>', unsafe_allow_html=True)
    
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
            mode = "gauge+number", value = score, title = {'text': "Health Score Index"},
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#1a3353"},
                     'steps': [{'range': [0, 50], 'color': "#e74c3c"}, {'range': [50, 75], 'color': "#f1c40f"}, {'range': [75, 100], 'color': "#27ae60"}]}))
        st.plotly_chart(fig_health, use_container_width=True)

    with col_sem:
        c1, c2, c3 = st.columns(3)
        with c1:
            color = "#27ae60" if idx_total < break_even else "#e74c3c" if break_even > 0 else "#95a5a6"
            st.markdown(f'<div class="risk-card" style="background:{color}">RISCO CRÉDITO<br>{idx_total:.1f}%</div>', unsafe_allow_html=True)
        with c2:
            m_color = "#27ae60" if hhi_val < 1500 else "#f1c40f" if hhi_val < 2500 else "#e74c3c"
            st.markdown(f'<div class="risk-card" style="background:{m_color}">CONCENTRAÇÃO<br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
        with c3:
            v_color = "#27ae60" if roi > w_final else "#e74c3c"
            st.markdown(f'<div class="risk-card" style="background:{v_color}">CRIAÇÃO VALOR<br>ROI: {roi}%</div>', unsafe_allow_html=True)

# --- 2. EQUIPE ---
elif menu == "⚇ Equipe e Governança":
    st.title("Estrutura da Equipe de Consultoria")
    st.markdown('<div class="guide-text">Registre os consultores responsáveis e o orientador do projeto acadêmico.</div>', unsafe_allow_html=True)
    part = data.get('participants', {})
    with st.form("f_equipe"):
        c1, c2 = st.columns(2)
        al1 = c1.text_input("Consultor Líder", value=part.get('aluno1', ''))
        al2 = c1.text_input("Consultor 2", value=part.get('aluno2', ''))
        al3 = c1.text_input("Consultor 3", value=part.get('aluno3', ''))
        al4 = c2.text_input("Consultor 4", value=part.get('aluno4', ''))
        al5 = c2.text_input("Consultor 5", value=part.get('aluno5', ''))
        prof = c2.text_input("Professor Responsável", value=part.get('professor', ''))
        if st.form_submit_button("Sincronizar Governança"):
            save_data(st.session_state.group, "participants", {"aluno1":al1, "aluno2":al2, "aluno3":al3, "aluno4":al4, "aluno5":al5, "professor":prof})
            st.success("Dados de equipe atualizados.")

# --- 3. PERFIL EMPRESA ---
elif menu == "🏢 Perfil do Cliente":
    st.title("Caracterização Corporativa")
    info = data.get('company_info', {})
    with st.form("f_empresa"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Razão Social", value=info.get('nome', ''))
        setor = c1.selectbox("Setor", ["Varejo", "Indústria", "Serviços", "Agro", "Tech"], index=0)
        colab = c2.number_input("Nº Funcionários", value=int(safe_float(info.get('colab', 0))))
        desc = st.text_area("Modelo de Negócio", value=info.get('desc', ''))
        if st.form_submit_button("Salvar Perfil"):
            save_data(st.session_state.group, "company_info", {"nome":nome, "setor":setor, "colab":colab, "desc":desc})
            st.success("Perfil sincronizado.")

# --- 4. GUIA ENTREVISTA ---
elif menu == "✎ Diagnóstico de Campo":
    st.title("Guia de Entrevista Semiestruturada")
    st.markdown('<div class="guide-text">Roteiro para coleta de dados qualitativos durante a visita in loco.</div>', unsafe_allow_html=True)
    diary = data.get('diary', {})
    with st.form("f_diary"):
        q1 = st.text_area("1. Histórico e Estratégia: Qual o diferencial competitivo?", value=diary.get('q1', ''))
        q2 = st.text_area("2. Custos e Juros: Como as variáveis macro afetam o caixa?", value=diary.get('q2', ''))
        q3 = st.text_area("3. Mercado: Quem são os rivais diretos?", value=diary.get('q3', ''))
        q4 = st.text_area("4. Endividamento: Qual o indexador da dívida atual?", value=diary.get('q4', ''))
        if st.form_submit_button("Salvar Diagnóstico"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2, "q3":q3, "q4":q4})
            st.success("Notas de campo salvas.")

# --- 5. MICRO ---
elif menu == "⚙ Análise Estratégica":
    st.title("Estratégia e Inteligência Competitiva")
    t1, t2, t3 = st.tabs(["5 Forças de Porter", "Concentração HHI", "Matriz SWOT"])
    
    with t1:
        p = data.get('porter', {})
        p1 = st.slider("Ameaça de Novos Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        p2 = st.slider("Poder dos Fornecedores", 1, 5, int(safe_float(p.get('p2', 3))))
        p3 = st.slider("Poder dos Clientes", 1, 5, int(safe_float(p.get('p3', 3))))
        p5 = st.slider("Rivalidade entre Concorrentes", 1, 5, int(safe_float(p.get('p5', 3))))
        if st.button("Salvar Matriz Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1,"p2":p2,"p3":p3,"p5":p5})
            st.success("Porter Salvo.")

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
            c1, c2 = st.columns(2)
            f = c1.text_area("Forças", value=sw.get('f', ''))
            fra = c2.text_area("Fraquezas", value=sw.get('fra', ''))
            o = c1.text_area("Oportunidades", value=sw.get('o', ''))
            a = c2.text_area("Ameaças", value=sw.get('a', ''))
            if st.form_submit_button("Sincronizar SWOT"):
                save_data(st.session_state.group, "swot", {"f":f, "fra":fra, "o":o, "a":a})
                st.rerun()
        c1, c2 = st.columns(2)
        c1.markdown(f'<div class="swot-card" style="background:#27ae60"><b>FORÇAS</b><br>{f}</div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="swot-card" style="background:#e74c3c"><b>FRAQUEZAS</b><br>{fra}</div>', unsafe_allow_html=True)

# --- 6. MACRO ---
elif menu == "🌐 Diagnóstico Monetário":
    st.title("Stress Test e Transmissão de Juros")
    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_nome = st.selectbox("Indexador da Dívida", ["Selic", "TJLP", "IPCA", "IGP-M"], index=0)
        idx_val = st.number_input(f"Valor {idx_nome} %", value=safe_float(dre_d.get('idx_valor', selic_ref)))
        spread = st.number_input("Spread Bancário (+ %)", value=safe_float(dre_d.get('spread', 2.0)))
        rec = st.number_input("Receita Bruta Anual", value=safe_float(dre_d.get('receita', 1000000)))
        cus = st.number_input("Custos Operacionais", value=safe_float(dre_d.get('custos', 700000)))
        div = st.number_input("Dívida Total", value=safe_float(dre_d.get('divida', 400000)))
        if st.button("Salvar Cenário"):
            save_data(st.session_state.group, "dre", {"idx_nome":idx_nome, "idx_valor":idx_val, "spread":spread, "receita":rec, "custos":cus, "divida":div})
            st.rerun()
    with c2:
        ebitda = rec - cus
        sim = st.slider(f"Simular {idx_nome} %", 0.0, 30.0, idx_val)
        st.metric("Lucro Estimado", f"R$ {ebitda - (div*(sim+spread)/100):,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div*(s+spread)/100) for s in range(0,31)], title="Ponto de Ruptura")
        fig.add_hline(y=0, line_dash="dash", line_color="#e74c3c")
        st.plotly_chart(fig)

# --- 7. FINANCEIRO ---
elif menu == "⚖ Viabilidade e Valor":
    st.title("Custo de Capital e Valor do Negócio")
    
    with st.expander("🎓 Metodologia Financeira"):
        st.markdown("**1. WACC:** Custo Médio Ponderado de Capital.")
        st.markdown("<span class='formula-text'>WACC = (E/V * Ke) + (D/V * Kd * 0.66)</span>", unsafe_allow_html=True)
        st.markdown("**2. Gordon Growth:** Valor do negócio na perpetuidade.")
        st.markdown("<span class='formula-text'>EV = Fluxo(1+g) / (WACC - g)</span>", unsafe_allow_html=True)

    t1, t2 = st.tabs(["WACC & EVA", "Simulador Valuation"])
    w_d = data.get('wacc', {})
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            ke = st.number_input("Ke (Custo Cap. Próprio %)", value=safe_float(w_d.get('ke', 15.0)))
            kd = st.number_input("Kd (Custo da Dívida %)", value=safe_float(w_d.get('kd', 12.0)))
            eq = st.slider("Participação Equity %", 0, 100, int(safe_float(w_d.get('eq_ratio', 60)))) / 100
            w_calc = (eq * (ke/100)) + ((1-eq) * (kd/100) * 0.66)
            st.metric("WACC Final", f"{w_calc*100:.2f}%")
        with c2:
            roi = st.number_input("ROI Operacional %", value=safe_float(w_d.get('roi', 18.0)))
            eva = roi - (w_calc * 100)
            st.metric("EVA (Criação de Valor)", f"{eva:.2f}%")
            if st.button("Salvar Financeiro"):
                save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":w_calc*100})
    with t2:
        g = st.slider("Taxa Crescimento Perpétuo (g) %", 0.0, 10.0, safe_float(w_d.get('g_growth', 3.0)))
        if st.button("Salvar g"): save_data(st.session_state.group, "wacc", {**w_d, "g_growth": g})
        
        ebit_v = safe_float(data.get('dre', {}).get('receita')) - safe_float(data.get('dre', {}).get('custos'))
        w_base = safe_float(w_d.get('wacc_final')) / 100
        g_v = g / 100
        if w_base > g_v:
            val = (ebit_v * (1 + g_v)) / (w_base - g_v)
            st.metric("Enterprise Value", f"R$ {val:,.2f}")
        else: st.error("Inconsistência: WACC deve ser > g.")

# --- 8. RELATÓRIO ---
elif menu == "📋 Relatório Consolidado":
    st.title("Relatório Técnico de Consultoria")
    st.write(f"Empresa: {data.get('company_info', {}).get('nome', 'N/A')} | Unidade: {st.session_state.group}")
    st.divider()
    st.button("Gerar PDF (Ctrl+P)")
