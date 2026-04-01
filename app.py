import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Intelligence", layout="wide", initial_sidebar_state="expanded")

# --- CSS WHITELABEL & DESIGN CORPORATIVO (REFINADO) ---
st.markdown("""
    <style>
    /* Ocultar elementos técnicos do Streamlit */
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}

    /* Background e Tipografia */
    .stApp { background-color: #f8fafc; font-family: 'Inter', -apple-system, sans-serif; }
    
    /* Customização da Sidebar */
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; min-width: 320px !important; }
    [data-testid="stSidebar"] .stMarkdown h2 { color: #1e293b; font-size: 1.4rem; padding-bottom: 0; }
    
    /* Menu de Navegação (Radio) */
    .stRadio > label { display: none; } /* Esconde o label do radio */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap: 4px; }
    
    /* Estilo dos Headers e Cards */
    h1, h2, h3 { color: #0f172a; font-weight: 700; letter-spacing: -0.03em; }
    .risk-card { padding: 22px; border-radius: 8px; text-align: center; color: white; font-weight: 600; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    .insight-box { background-color: #ffffff; padding: 25px; border-left: 5px solid #0f172a; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 25px; border-top: 1px solid #f1f5f9; border-right: 1px solid #f1f5f9; border-bottom: 1px solid #f1f5f9; }
    
    /* Fórmulas e Botões */
    .formula-text { font-family: 'SF Mono', monospace; background-color: #f1f5f9; padding: 12px; border-radius: 6px; font-size: 0.85em; color: #334155; border: 1px solid #e2e8f0; display: block; margin: 12px 0; }
    .stButton>button { background-color: #0f172a; color: white; border-radius: 6px; width: 100%; font-weight: 600; height: 48px; border: none; transition: 0.2s; }
    .stButton>button:hover { background-color: #334155; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO BANCO CENTRAL (API SGS - SELIC META) ---
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
    st.error("Falha de comunicação com o servidor de dados.")
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
    st.markdown("<h2 style='text-align: center; color: #0f172a;'>EcoStrategy Intelligence</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.6, 1])
    with col_l2:
        try: st.image("logo.png", use_container_width=True)
        except: pass
        group = st.selectbox("Unidade de Consultoria", ["Grupo 1", "Grupo 2", "Grupo 3"])
        pwd = st.text_input("Chave de Acesso", type="password")
        if st.button("Autenticar Unidade"):
            if pwd == "eco123":
                st.session_state.auth, st.session_state.group = True, group
                st.rerun()
    st.stop()

data = load_data(st.session_state.group)

# --- SIDEBAR (DESIGN CORPORATIVO LIMPO) ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    
    st.markdown(f"<h2 style='text-align: center;'>{st.session_state.group}</h2>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("<p style='font-size: 0.8rem; font-weight: 700; color: #64748b; margin-bottom: -10px;'>CENÁRIO MACRO (REAL-TIME)</p>", unsafe_allow_html=True)
    selic_meta = get_live_selic()
    st.caption(f"Selic Meta BCB: {selic_meta}% a.a.")
    selic_ref = st.number_input("Benchmark Trabalho (%)", value=selic_meta, step=0.25)
    
    st.divider()
    st.markdown("<p style='font-size: 0.8rem; font-weight: 700; color: #64748b; margin-bottom: 5px;'>NAVEGAÇÃO DO PROJETO</p>", unsafe_allow_html=True)
    
    # Menu com Símbolos Unicode Minimalistas
    menu = st.radio("MENU", [
        "□ Dashboard Executivo", 
        "○ Governança e Equipe", 
        "◊ Perfil Corporativo",
        "△ Diagnóstico de Campo", 
        "⚙ Inteligência Estratégica", 
        "🌐 Cenário Monetário", 
        "⚖ Viabilidade e Valor", 
        "▤ Relatório Consolidado"
    ])
    
    st.divider()
    if st.button("Encerrar Sessão"):
        st.session_state.auth = False
        st.rerun()

# --- 1. DASHBOARD ---
if menu == "□ Dashboard Executivo":
    st.title("Executive Management Dashboard")
    info = data.get('company_info', {})
    st.markdown(f'<div class="insight-box"><h4>Unidade: {info.get("nome", "Não Cadastrada")}</h4><p>Sumário de indicadores críticos de risco, concentração e valor.</p></div>', unsafe_allow_html=True)
    
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
            gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#0f172a"},
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

# --- 2. EQUIPE ---
elif menu == "○ Governança e Equipe":
    st.title("Estrutura de Governança")
    part = data.get('participants', {})
    with st.form("f_equipe"):
        c1, c2 = st.columns(2)
        al1 = c1.text_input("Consultor Líder", value=part.get('aluno1', ''))
        al2 = c1.text_input("Consultor 2", value=part.get('aluno2', ''))
        al3 = c1.text_input("Consultor 3", value=part.get('aluno3', ''))
        al4 = c2.text_input("Consultor 4", value=part.get('aluno4', ''))
        al5 = c2.text_input("Consultor 5", value=part.get('aluno5', ''))
        prof = c2.text_input("Professor Orientador", value=part.get('professor', ''))
        if st.form_submit_button("Sincronizar Dados"):
            save_data(st.session_state.group, "participants", {"aluno1":al1, "aluno2":al2, "aluno3":al3, "aluno4":al4, "aluno5":al5, "professor":prof})
            st.success("Governança atualizada.")

# --- 3. PERFIL ---
elif menu == "◊ Perfil Corporativo":
    st.title("Caracterização do Cliente")
    info = data.get('company_info', {})
    with st.form("f_empresa"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Razão Social", value=info.get('nome', ''))
        setor = c1.selectbox("Setor", ["Varejo", "Indústria", "Serviços", "Agro", "Tech"], index=0)
        fundacao = c1.text_input("Ano Fundação", value=info.get('fundacao', ''))
        colab = c2.number_input("Nº Funcionários", value=int(safe_float(info.get('colab', 0))))
        prod = c2.text_input("Principal Produto", value=info.get('produto', ''))
        desc = st.text_area("Modelo de Negócio", value=info.get('desc', ''))
        if st.form_submit_button("Salvar Perfil"):
            save_data(st.session_state.group, "company_info", {"nome":nome, "setor":setor, "fundacao":fundacao, "colab":colab, "produto":prod, "desc":desc})
            st.success("Perfil Salvo.")

# --- 4. GUIA ENTREVISTA ---
elif menu == "△ Diagnóstico de Campo":
    st.title("Guia de Entrevista")
    diary = data.get('diary', {})
    with st.form("f_diary"):
        q1 = st.text_area("1. Diferencial Competitivo e Estratégia", value=diary.get('q1', ''))
        q2 = st.text_area("2. Impacto de Variáveis Macro (Juros/Inflação)", value=diary.get('q2', ''))
        q3 = st.text_area("3. Estrutura de Mercado e Concorrência", value=diary.get('q3', ''))
        q4 = st.text_area("4. Gestão Financeira e Endividamento", value=diary.get('q4', ''))
        if st.form_submit_button("Sincronizar Notas"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2, "q3":q3, "q4":q4})
            st.success("Diário Sincronizado.")

# --- 5. MICRO (PORTER/HHI/SWOT) ---
elif menu == "⚙ Inteligência Estratégica":
    st.title("Estratégia e Inteligência Competitiva")
    t1, t2, t3 = st.tabs(["5 Forças de Porter", "Concentração HHI", "Matriz SWOT"])
    
    with t1:
        p = data.get('porter', {})
        p1 = st.slider("Ameaça Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        p2 = st.slider("Poder Fornecedores", 1, 5, int(safe_float(p.get('p2', 3))))
        p3 = st.slider("Poder Clientes", 1, 5, int(safe_float(p.get('p3', 3))))
        p5 = st.slider("Rivalidade Setorial", 1, 5, int(safe_float(p.get('p5', 3))))
        if st.button("Salvar Porter"):
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
            if st.form_submit_button("Salvar SWOT"):
                save_data(st.session_state.group, "swot", {"f":f, "fra":fra, "o":o, "a":a})
                st.rerun()

# --- 6. MACRO ---
elif menu == "🌐 Diagnóstico Monetário":
    st.title("Stress Test e Transmissão de Juros")
    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_nome = st.selectbox("Indexador", ["Selic", "TJLP", "IPCA", "IGP-M"], index=0)
        idx_val = st.number_input(f"Valor {idx_nome} %", value=safe_float(dre_d.get('idx_valor', selic_ref)))
        spread = st.number_input("Spread (+ %)", value=safe_float(dre_d.get('spread', 2.0)))
        rec = st.number_input("Receita Bruta Anual", value=safe_float(dre_d.get('receita', 1000000)))
        cus = st.number_input("Custos Operacionais", value=safe_float(dre_d.get('custos', 700000)))
        div = st.number_input("Dívida Total", value=safe_float(dre_d.get('divida', 400000)))
        if st.button("Salvar Cenário"):
            save_data(st.session_state.group, "dre", {"idx_nome":idx_nome, "idx_valor":idx_val, "spread":spread, "receita":rec, "custos":cus, "divida":div})
            st.rerun()
    with c2:
        ebitda = rec - cus
        sim = st.slider(f"Simular {idx_nome} %", 0.0, 30.0, idx_val)
        st.metric("Lucro Líquido na Simulação", f"R$ {ebitda - (div*(sim+spread)/100):,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div*(s+spread)/100) for s in range(0,31)], title="Análise de Ponto de Ruptura")
        fig.add_hline(y=0, line_dash="dash", line_color="#ef4444")
        st.plotly_chart(fig)

# --- 7. FINANCEIRO ---
elif menu == "⚖ Viabilidade e Valor":
    st.title("Viabilidade e Valuation")
    
    with st.expander("🎓 Saiba Mais: Fórmulas Financeiras"):
        st.markdown("**1. WACC:** Custo Médio Ponderado de Capital.")
        st.markdown("<span class='formula-text'>WACC = (E/V * Ke) + (D/V * Kd * 0.66)</span>", unsafe_allow_html=True)
        st.markdown("**2. Gordon Growth:** Valor presente da perpetuidade.")
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
        else: st.error("Erro: WACC deve ser > g.")

# --- 8. RELATÓRIO ---
elif menu == "▤ Relatório Consolidado":
    st.title("Executive Report Summary")
    st.write(f"Empresa: {data.get('company_info', {}).get('nome', 'N/A')}")
    st.divider()
    st.button("Exportar PDF (Ctrl+P)")
