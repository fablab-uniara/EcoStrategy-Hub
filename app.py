import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
import openai
from datetime import datetime
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Intelligence", layout="wide", initial_sidebar_state="expanded")

# --- CSS MASTER WHITELABEL & DESIGN ACADÊMICO ELITE ---
st.markdown("""
    <style>
    .stAppDeployButton, footer, #MainMenu, header {display:none !important;}
    .stApp { background-color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    .stApp p, .stApp span, .stApp label { color: #1e293b !important; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; border-right: 1px solid #1e293b !important; min-width: 320px !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] label { color: #f1f5f9 !important; }
    h1, h2, h3 { color: #002e5d !important; font-weight: 800; letter-spacing: -0.04em !important; }
    .metodologia-card { background-color: #f0f7ff !important; border-left: 6px solid #0052cc !important; padding: 20px !important; border-radius: 8px !important; margin-bottom: 25px !important; color: #1e40af !important; }
    .metodologia-card h4 { color: #0052cc !important; margin-top: 0 !important; }
    .justificativa-card { background-color: #fffdf0 !important; border: 1px solid #ffe58f !important; padding: 15px !important; border-radius: 8px !important; margin-top: 15px !important; }
    .formula-box { font-family: 'Courier New', monospace !important; background-color: #2d3436 !important; color: #fab1a0 !important; padding: 15px !important; border-radius: 5px !important; font-size: 0.9em !important; margin: 15px 0 !important; display: block; border: 1px solid #636e72 !important; }
    .risk-card { padding: 22px; border-radius: 12px; text-align: center; color: white !important; font-weight: 600; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .swot-card { padding: 15px; border-radius: 8px; height: 130px; color: white !important; font-size: 0.85em; overflow-y: auto; margin-bottom: 10px; }
    .stButton>button { background-color: #0052cc !important; color: white !important; border-radius: 6px; width: 100%; font-weight: 600; height: 45px; border: none; }
    .focus-card { background-color: #1e293b; padding: 10px; border-radius: 8px; border-left: 4px solid #3b82f6; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE API (BCB SGS & FOCUS) ---
@st.cache_data(ttl=3600)
def get_live_selic():
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        return float(requests.get(url, timeout=5).json()[0]['valor'])
    except: return 10.75

@st.cache_data(ttl=3600)
def get_focus_projections():
    try:
        url = "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/aplicacao/recursos/ExpectativasMercadoAnuais?$top=10&$orderby=Data desc&$filter=Indicador eq 'IPCA' or Indicador eq 'PIB Total' or Indicador eq 'Selic'&$format=json"
        res = requests.get(url, timeout=5).json()
        df = pd.DataFrame(res['value'])
        atual = str(datetime.now().year)
        return df[df['DataReferencia'] == atual]
    except: return pd.DataFrame()

# --- CONEXÃO SUPABASE ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("Erro Crítico de Conexão com o Banco de Dados.")
    st.stop()

# --- UTILITÁRIOS DE SEGURANÇA ---
def safe_float(val, default=0.0):
    try: return float(val)
    except: return default

def safe_json(val):
    if val is None or val == "" or val == "None": return {}
    if isinstance(val, dict): return val
    try: return json.loads(val)
    except: return {}

def load_data(gid):
    try:
        res = supabase.table("eco_data").select("*").eq("group_id", gid).execute()
        if res.data:
            row = res.data[0]
            cols = ['porter', 'dre', 'wacc', 'swot', 'participants', 'company_info', 'diary']
            for col in cols: row[col] = safe_json(row.get(col))
            return row
    except: pass
    return {'group_id': gid, 'porter': {}, 'dre': {}, 'wacc': {}, 'swot': {}, 'hhi': '0', 'diary': {}, 'participants': {}, 'company_info': {}, 'feedback': ''}

def save_data(gid, column, value):
    if isinstance(value, (dict, list)): value = json.dumps(value)
    supabase.table("eco_data").upsert({"group_id": gid, column: str(value)}).execute()

def render_academic_header(titulo, objetivo, tarefa):
    st.markdown(f"""<div class="metodologia-card"><h4>🎓 GUIA METODOLÓGICO: {titulo}</h4><p><b>Objetivo:</b> {objetivo}</p><p><b>Ação Requerida:</b> {tarefa}</p></div>""", unsafe_allow_html=True)

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_teacher' not in st.session_state: st.session_state.is_teacher = False

if not st.session_state.auth:
    st.markdown("<h2 style='text-align: center; color: #0f172a; padding-top: 50px;'>ECOSTRATEGY INTELLIGENCE</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.8, 1])
    with col_l2:
        try: st.image("logo.png", use_container_width=True)
        except: pass
        group_sel = st.selectbox("Acesso", ["Grupo 1", "Grupo 2", "Grupo 3", "Acesso Professor"])
        pwd_input = st.text_input("Senha", type="password")
        if st.button("Acessar Dashboard"):
            passwords = st.secrets.get("GROUP_PASSWORDS", {})
            dev_pwd = st.secrets.get("DEV_PASSWORD")
            if pwd_input == passwords.get(group_sel) or pwd_input == dev_pwd:
                st.session_state.auth, st.session_state.group = True, ("Grupo 1" if group_sel == "Acesso Professor" else group_sel)
                st.session_state.is_teacher = (pwd_input == dev_pwd)
                st.rerun()
            else: st.error("Acesso Negado.")
    st.stop()

data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    st.markdown(f"<h2 style='text-align:center;'>{st.session_state.group.upper()}</h2>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("<p style='color:#94a3b8; font-weight:700; font-size:0.75rem;'>EXPECTATIVAS FOCUS (BCB)</p>", unsafe_allow_html=True)
    df_focus = get_focus_projections()
    if not df_focus.empty:
        for idx, row in df_focus.iterrows():
            st.markdown(f"<div class='focus-card'><small style='color:#94a3b8'>{row['Indicador']}</small><br><b style='color:white'>{row['Mediana']}%</b></div>", unsafe_allow_html=True)
    
    st.divider()
    selic_ref = st.number_input("Benchmark Selic (%)", value=get_live_selic(), step=0.25)
    
    menu = st.radio("SISTEMA", [
        "01 DASHBOARD GERAL", "02 EQUIPE E GOVERNANÇA", "03 PERFIL DO CLIENTE", 
        "04 DIÁRIO DE CAMPO", "05 ANÁLISE ESTRATÉGICA", "06 CENÁRIO MONETÁRIO", 
        "07 FINANCEIRO & VALOR", "08 REFERENCIAL TEÓRICO", "09 RELATÓRIO FINAL"
    ] + (["10 PORTAL DO ORIENTADOR"] if st.session_state.is_teacher else []), label_visibility="collapsed")
    
    if st.button("Sair"): st.session_state.auth = False; st.rerun()

# --- 01. DASHBOARD ---
if menu == "01 DASHBOARD GERAL":
    st.title("Executive Intelligence Dashboard")
    render_academic_header("Visão Integrada", "Consolidar indicadores de risco e valor.", "Analise o score de saúde e os pareceres do professor.")
    if data.get('feedback'): st.warning(f"📬 PARECER DO ORIENTADOR: {data.get('feedback')}")
    
    dre_d = data.get('dre', {})
    ebitda = safe_float(dre_d.get('receita')) - safe_float(dre_d.get('custos'))
    divida = safe_float(dre_d.get('divida'))
    idx_total = safe_float(dre_d.get('idx_valor', selic_ref))
    break_even = (ebitda / divida * 100) if divida > 0 else 0
    hhi_str = str(data.get('hhi', '0'))
    try: hhi_val = sum([float(x)**2 for x in hhi_str.split(",") if x.strip()])
    except: hhi_val = 0
    w_d = data.get('wacc', {})
    roi = safe_float(w_d.get('roi'))
    w_final = safe_float(w_d.get('wacc_final', 15.0))
    
    score = 0
    if divida == 0 or idx_total < break_even: score += 40
    if hhi_val < 2500: score += 30
    if roi > (selic_ref + 5): score += 30

    col_g, col_s = st.columns([1.5, 2])
    with col_g:
        st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=score, title={'text':"Health Score Index"},
            gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#2563eb"}, 'steps':[{'range':[0,50],'color':"#dc3545"},{'range':[50,80],'color':"#ffc107"},{'range':[80,100],'color':"#28a745"}]})), use_container_width=True)
    with col_s:
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="risk-card" style="background:{"#10b981" if selic_ref < break_even else "#ef4444"}">CRÉDITO<br>{idx_total:.1f}%</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="risk-card" style="background:{"#10b981" if hhi_val < 1500 else "#f59e0b"}">MERCADO<br>HHI:{int(hhi_val)}</div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="risk-card" style="background:{"#10b981" if roi > w_final else "#ef4444"}">VALOR<br>ROI:{roi}%</div>', unsafe_allow_html=True)

# --- 02. EQUIPE ---
elif menu == "02 EQUIPE E GOVERNANÇA":
    st.title("Composição da Equipe Técnica")
    render_academic_header("Governança", "Identificar os responsáveis e o orientador.", "Preencha os nomes de todos os alunos e do professor responsável.")
    part = data.get('participants', {})
    with st.form("f_eq"):
        c1, c2 = st.columns(2)
        al1 = c1.text_input("Aluno 1 (Líder)", value=part.get('al1', ''))
        al2 = c1.text_input("Aluno 2", value=part.get('al2', ''))
        al3 = c1.text_input("Aluno 3", value=part.get('al3', ''))
        al4 = c2.text_input("Aluno 4", value=part.get('al4', ''))
        al5 = c2.text_input("Aluno 5", value=part.get('al5', ''))
        prof = c2.text_input("Professor Responsável", value=part.get('prof', ''))
        if st.form_submit_button("Sincronizar"):
            save_data(st.session_state.group, "participants", {"al1":al1,"al2":al2,"al3":al3,"al4":al4,"al5":al5,"prof":prof})
            st.success("Salvo!")

# --- 03. PERFIL DO CLIENTE ---
elif menu == "03 PERFIL DO CLIENTE":
    st.title("Caracterização Corporativa")
    render_academic_header("Negócio", "Contextualizar a operação da empresa.", "Insira os dados demográficos e operacionais completos.")
    info = data.get('company_info', {})
    with st.form("f_info"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Razão Social / Nome Fantasia", value=info.get('nome', ''))
        s = c1.selectbox("Setor Econômico", ["Varejo", "Indústria", "Serviços", "Agro", "Tech"], index=0)
        f = c1.text_input("Ano de Fundação", value=info.get('fundacao', ''))
        fat = c1.selectbox("Porte (Faturamento)", ["Micro (< 360k)", "Pequena (360k - 4.8M)", "Média", "Grande"])
        colab = c2.number_input("Nº de Colaboradores", value=int(safe_float(info.get('colab', 0))))
        prod = c2.text_input("Principal Produto", value=info.get('prod', ''))
        abr = c2.selectbox("Abrangência", ["Local", "Regional", "Nacional", "Multinacional"])
        d = c2.text_area("Descrição do Modelo de Negócio", value=info.get('desc', ''))
        if st.form_submit_button("Salvar Perfil"):
            save_data(st.session_state.group, "company_info", {"nome":n, "setor":s, "fundacao":f, "fat":fat, "colab":colab, "prod":prod, "abr":abr, "desc":d})
            st.success("Salvo!")

# --- 04. DIÁRIO ---
elif menu == "04 DIAGNÓSTICO DE CAMPO":
    st.title("Guia de Entrevista e Diagnóstico")
    render_academic_header("Qualitativo", "Coletar evidências reais.", "Utilize estas questões estruturadas durante a visita técnica.")
    dia = data.get('diary', {})
    with st.form("f_dia"):
        q1 = st.text_area("1. Histórico e Estratégia: Como começou e qual o diferencial competitivo?", value=dia.get('q1', ''))
        q2 = st.text_area("2. Custos e Operação: Qual o maior gargalo produtivo hoje?", value=dia.get('q2', ''))
        q3 = st.text_area("3. Mercado e Rivais: Quem são os rivais e qual a barreira de entrada?", value=dia.get('q3', ''))
        q4 = st.text_area("4. Gestão Financeira: Qual o peso dos juros e inflação no caixa?", value=dia.get('q4', ''))
        if st.form_submit_button("Sincronizar Notas"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2, "q3":q3, "q4":q4})
            st.success("Salvo!")

# --- 05. ESTRATÉGIA ---
elif menu == "05 ANÁLISE ESTRATÉGICA":
    st.title("Módulo de Inteligência Competitiva")
    render_academic_header("Estratégia", "Avaliar hostilidade setorial e competitividade.", "Preencha Porter, HHI e SWOT fundamentando cada escolha.")
    
    t1, t2, t3 = st.tabs(["Michael Porter (5 Forças)", "Concentração (HHI)", "Matriz SWOT"])
    with t1:
        p = data.get('porter', {})
        c1, c2 = st.columns(2)
        p1 = c1.slider("Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        p2 = c1.slider("Fornecedores", 1, 5, int(safe_float(p.get('p2', 3))))
        p3 = c1.slider("Clientes", 1, 5, int(safe_float(p.get('p3', 3))))
        p4 = c2.slider("Substitutos", 1, 5, int(safe_float(p.get('p4', 3))))
        p5 = c2.slider("Rivalidade", 1, 5, int(safe_float(p.get('p5', 3))))
        p_just = st.text_area("Justificativa Acadêmica das Notas (Porter):", value=p.get('just', ''))
        if st.button("Salvar Porter"): save_data(st.session_state.group, "porter", {"p1":p1,"p2":p2,"p3":p3,"p4":p4,"p5":p5,"just":p_just})
    with t2:
        st.markdown("<div class='formula-box'>HHI = Σ (Share)²</div>", unsafe_allow_html=True)
        colh1, colh2 = st.columns(2)
        with colh1:
            s1 = st.number_input("Share Empresa Líder %", 0.0, 100.0, 30.0)
            s2 = st.number_input("Share 2º Concorrente %", 0.0, 100.0, 20.0)
            s3 = st.number_input("Share 3º Concorrente %", 0.0, 100.0, 10.0)
            s4 = st.number_input("Share 4º Concorrente %", 0.0, 100.0, 5.0)
            rest = max(0.0, 100.0 - (s1+s2+s3+s4))
            st.info(f"Concorrência Atomizada (Outros): {rest:.1f}%")
        with colh2:
            h_calc = s1**2 + s2**2 + s3**2 + s4**2 + rest**2
            st.metric("HHI Final", int(h_calc))
            st.plotly_chart(px.pie(values=[s1,s2,s3,s4,rest], names=["Líder","2º","3º","4º","Outros"], hole=0.4))
        if st.button("Salvar HHI"): save_data(st.session_state.group, "hhi", f"{s1},{s2},{s3},{s4},{rest}")
    with t3:
        sw = data.get('swot', {})
        with st.form("f_sw"):
            f = st.text_area("Forças (Internas)", value=sw.get('f', ''))
            fra = st.text_area("Fraquezas (Internas)", value=sw.get('fra', ''))
            o = st.text_area("Oportunidades (Externas)", value=sw.get('o', ''))
            a = st.text_area("Ameaças (Externas)", value=sw.get('a', ''))
            if st.form_submit_button("Salvar SWOT"): save_data(st.session_state.group, "swot", {"f":f, "fra":fra, "o":o, "a":a})
        c1, c2 = st.columns(2); c1.markdown(f'<div class="swot-card" style="background:#28a745"><b>FORÇAS</b><br>{f}</div>', unsafe_allow_html=True); c2.markdown(f'<div class="swot-card" style="background:#dc3545"><b>FRAQUEZAS</b><br>{fra}</div>', unsafe_allow_html=True)

# --- 06. MONETÁRIO ---
elif menu == "06 CENÁRIO MONETÁRIO":
    st.title("Diagnóstico Monetário e Stress Test")
    render_academic_header("Macroeconomia", "Analisar transmissão da Selic no balanço.", "Configure os indexadores e verifique o ponto de ruptura.")
    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_nome = st.selectbox("Indexador da Dívida", ["Selic", "TJLP", "IPCA", "IGP-M"], index=0)
        idx_val = st.number_input(f"Valor do {idx_nome} (%)", value=safe_float(dre_d.get('idx_valor', selic_ref)))
        spread = st.number_input("Spread Bancário (+%)", value=safe_float(dre_d.get('spread', 2.0)))
        rec = st.number_input("Receita Bruta", value=safe_float(dre_d.get('receita', 1000000)))
        cus = st.number_input("Custos Totais", value=safe_float(dre_d.get('custos', 700000)))
        div = st.number_input("Dívida Total", value=safe_float(dre_d.get('divida', 400000)))
        if st.button("Salvar Cenário"): save_data(st.session_state.group, "dre", {"idx_nome":idx_nome, "idx_valor":idx_val, "spread":spread, "receita":rec, "custos":cus, "divida":div})
    with c2:
        ebitda = rec - cus
        sim = st.slider(f"Simular {idx_nome} %", 0.0, 30.0, idx_val)
        st.metric("Lucro Líquido Simulado", f"R$ {ebitda - (div*(sim+spread)/100):,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div*(s+spread)/100) for s in range(0,31)], title="Análise de Ruptura (Fluxo de Caixa)")
        fig.add_hline(y=0, line_dash="dash", line_color="red"); st.plotly_chart(fig)

# --- 07. FINANCEIRO ---
elif menu == "07 FINANCEIRO & VALOR":
    st.title("💰 Engenharia Financeira e Valuation")
    render_academic_header("Valor", "Determinar custo de capital e valor intrínseco.", "Calcule o WACC e o Valuation baseado no PIB projetado pelo Focus.")
    w_d = data.get('wacc', {})
    t1, t2 = st.tabs(["WACC & EVA", "Simulador Gordon (Valuation)"])
    with t1:
        st.markdown("<div class='formula-box'>WACC = (E/V * Ke) + (D/V * Kd * 0.66)</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            ke = st.number_input("Ke % (Sócios)", value=safe_float(w_d.get('ke', 15.0)))
            kd = st.number_input("Kd % (Bancos)", value=safe_float(w_d.get('kd', 12.0)))
            eq = st.slider("Equity Ratio %", 0, 100, int(safe_float(w_d.get('eq_ratio', 60)))) / 100
            w_res = (eq*ke/100) + ((1-eq)*kd/100*0.66); st.metric("WACC Final", f"{w_res*100:.2f}%")
        with c2:
            roi = st.number_input("ROI Operacional %", value=safe_float(w_d.get('roi', 18.0)))
            eva = roi - (w_res*100); st.metric("EVA (Criação de Valor)", f"{eva:.2f}%")
        if st.button("Salvar Financeiro"): save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":w_res*100})
    with t2:
        pib_f = float(df_focus[df_focus['Indicador'] == 'PIB Total'].iloc[0]['Mediana']) if not df_focus.empty else 2.0
        st.info(f"💡 Referencial Focus: O mercado projeta crescimento do PIB de {pib_f}%.")
        g = st.slider("Crescimento Perpétuo (g) %", 0.0, 10.0, safe_float(w_d.get('g', pib_f)))
        g_just = st.text_area("Justificativa da Taxa g:", value=w_d.get('g_just', ''))
        ebit_v = safe_float(data.get('dre', {}).get('receita')) - safe_float(data.get('dre', {}).get('custos'))
        if w_res > g/100:
            ev = (ebit_v*(1+g/100)) / (w_res - g/100); st.metric("Enterprise Value", f"R$ {ev:,.2f}")
            if st.button("Salvar Valuation"): save_data(st.session_state.group, "wacc", {**w_d, "g":g, "g_just":g_just})
        else: st.error("Erro: WACC deve ser > g.")

# --- 08. REFERENCIAL ---
elif menu == "08 REFERENCIAL TEÓRICO":
    st.title("📚 Fundamentação Metodológica")
    st.markdown("- **Porter, Michael.** Estratégia Competitiva.\n- **Assaf Neto, Alexandre.** Finanças Corporativas.\n- **Damodaran, Aswath.** Valuation.\n- **Bacen.** Relatório Focus.")

# --- 09. RELATÓRIO ---
elif menu == "09 RELATÓRIO FINAL":
    st.title("Relatório de Consultoria")
    st.write(f"Empresa: {data.get('company_info', {}).get('nome', 'N/A')} | Grupo: {st.session_state.group}")
    st.divider(); st.button("Exportar (Ctrl + P)")

# --- 10. PROFESSOR ---
elif menu == "10 PORTAL DO ORIENTADOR" and st.session_state.is_teacher:
    st.title("🎓 Portal do Professor")
    target = st.selectbox("Selecione o Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
    dados = load_data(target)
    st.write(f"**Justificativa Porter:** {dados.get('porter', {}).get('just')}")
    txt = st.text_area("Parecer Final:", value=dados.get('feedback', ''), height=300)
    if st.button("🚀 Liberar Feedback"): save_data(target, "feedback", txt); st.success("Enviado!")
