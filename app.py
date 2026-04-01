import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Hub - Edição Master", layout="wide", initial_sidebar_state="expanded")

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
    .swot-card { padding: 15px; border-radius: 8px; height: 130px; color: white; font-size: 0.85em; overflow-y: auto; margin-bottom: 10px; }
    .stButton>button { background-color: #0052cc; color: white; border-radius: 6px; width: 100%; font-weight: bold; height: 45px; border: none; }
    .guide-text { font-size: 0.95em; color: #444; line-height: 1.6; background: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #ddd; margin-bottom: 15px;}
    .interview-q { font-weight: 600; color: #002e5d; margin-top: 15px; display: block; }
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

# --- FUNÇÕES DE SEGURANÇA E CÁLCULO ---
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
            # Inicialização segura de todas as colunas JSON
            row['porter'] = safe_json(row.get('porter'))
            row['dre'] = safe_json(row.get('dre'))
            row['wacc'] = safe_json(row.get('wacc'))
            row['swot'] = safe_json(row.get('swot'))
            row['participants'] = safe_json(row.get('participants'))
            row['company_info'] = safe_json(row.get('company_info'))
            row['diary'] = safe_json(row.get('diary'))
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

# CARREGAR DADOS GLOBAIS
data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    st.header("⚙️ Variáveis Macro")
    selic_ref = st.number_input("Selic de Referência (%)", value=10.75, step=0.25)
    st.divider()
    menu = st.radio("ROTEIRO DA CONSULTORIA", [
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
    st.title("📈 Dashboard Executivo Inteligente")
    info = data.get('company_info', {})
    st.markdown(f'<div class="insight-box"><h4>Consultoria Acadêmica: {info.get("nome", "Aguardando Cadastro")}</h4><p>Diagnóstico automático de riscos, valor e concentração setorial.</p></div>', unsafe_allow_html=True)
    
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
        st.markdown(f'<div class="risk-card" style="background:{c}">RISCO CRÉDITO<br>Taxa Atual: {idx_total:.2f}%</div>', unsafe_allow_html=True)
    with col2:
        mc = "#28a745" if hhi_val < 1500 else "#ffc107" if hhi_val < 2500 else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{mc}">RISCO MERCADO<br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
    with col3:
        vc = "#28a745" if roi > w_final else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{vc}">CRIAÇÃO VALOR<br>ROI: {roi}%</div>', unsafe_allow_html=True)

    st.divider()
    cola, colb = st.columns(2)
    with cola:
        st.subheader("💎 Valuation Estimado")
        if (w_final/100) > g_val:
            val_est = (ebitda * (1 + g_val)) / ((w_final/100) - g_val)
            st.metric("Enterprise Value", f"R$ {val_est:,.2f}")
        else: st.warning("Aguardando cálculos WACC.")
    with colb:
        st.subheader("🎓 Resumo da Equipe")
        part = data.get('participants', {})
        st.write(f"**Líder:** {part.get('aluno1', '-')}")
        st.write(f"**Professor:** {part.get('professor', '-')}")

# --- 2. IDENTIFICAÇÃO EQUIPE ---
elif menu == "2. Identificação da Equipe":
    st.title("👥 Identificação dos Consultores")
    st.markdown('<div class="guide-text">Preencha o nome completo dos consultores e do professor orientador.</div>', unsafe_allow_html=True)
    part = data.get('participants', {})
    with st.form("f_equipe"):
        c1, c2 = st.columns(2)
        al1 = c1.text_input("Consultor 1 (Líder)", value=part.get('aluno1', ''))
        al2 = c1.text_input("Consultor 2", value=part.get('aluno2', ''))
        al3 = c1.text_input("Consultor 3", value=part.get('aluno3', ''))
        al4 = c2.text_input("Consultor 4", value=part.get('aluno4', ''))
        al5 = c2.text_input("Consultor 5", value=part.get('aluno5', ''))
        prof = c2.text_input("Professor Responsável", value=part.get('professor', ''))
        if st.form_submit_button("Salvar Equipe"):
            save_data(st.session_state.group, "participants", {"aluno1":al1, "aluno2":al2, "aluno3":al3, "aluno4":al4, "aluno5":al5, "professor":prof})
            st.success("Equipe Salva!")

# --- 3. PERFIL DA EMPRESA ---
elif menu == "3. Perfil da Empresa":
    st.title("🏢 Caracterização Completa da Empresa")
    st.markdown('<div class="guide-text">Forneça os dados demográficos e operacionais da empresa analisada.</div>', unsafe_allow_html=True)
    info = data.get('company_info', {})
    with st.form("f_empresa"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Razão Social / Nome Fantasia", value=info.get('nome', ''))
        setor = c1.selectbox("Setor de Atuação", ["Varejo", "Indústria", "Serviços", "Agro", "Tech"], index=0)
        fundacao = c1.text_input("Ano de Fundação", value=info.get('fundacao', ''))
        faturamento = c1.selectbox("Porte (Faturamento Anual)", ["Micro (< 360k)", "Pequena (360k - 4.8M)", "Média (4.8M - 300M)", "Grande (> 300M)"])
        colab = c2.number_input("Nº de Colaboradores", value=int(safe_float(info.get('colab', 0))))
        produto = c2.text_input("Principal Produto/Serviço", value=info.get('produto', ''))
        abrangencia = c2.selectbox("Abrangência", ["Local", "Regional", "Nacional", "Multinacional"])
        desc = c2.text_area("Descrição Detalhada do Negócio", value=info.get('desc', ''))
        if st.form_submit_button("Salvar Perfil Corporativo"):
            save_data(st.session_state.group, "company_info", {"nome":nome, "setor":setor, "fundacao":fundacao, "faturamento":faturamento, "colab":colab, "produto":produto, "abrangencia":abrangencia, "desc":desc})
            st.success("Perfil Salvo!")

# --- 4. GUIA DE ENTREVISTA (DIÁRIO ESTRUTURADO) ---
elif menu == "4. Guia de Entrevista (Diário)":
    st.title("📔 Guia de Entrevista e Diagnóstico de Campo")
    st.markdown('<div class="guide-text"><b>Instrução:</b> Utilize as perguntas abaixo como roteiro durante a visita técnica. Registre as respostas e observações.</div>', unsafe_allow_html=True)
    
    diary = data.get('diary', {})
    with st.form("f_diary"):
        st.markdown('<span class="interview-q">1. Histórico e Estratégia: Como a empresa começou e qual o seu principal diferencial competitivo hoje?</span>', unsafe_allow_html=True)
        q1 = st.text_area("Resposta 1", value=diary.get('q1', ''), key="q1", label_visibility="collapsed")
        
        st.markdown('<span class="interview-q">2. Estrutura de Custos: Qual o maior custo operacional da empresa e como a inflação/juros tem afetado as margens?</span>', unsafe_allow_html=True)
        q2 = st.text_area("Resposta 2", value=diary.get('q2', ''), key="q2", label_visibility="collapsed")
        
        st.markdown('<span class="interview-q">3. Mercado e Clientes: Quem são os 3 principais concorrentes e qual a maior dificuldade em atrair clientes?</span>', unsafe_allow_html=True)
        q3 = st.text_area("Resposta 3", value=diary.get('q3', ''), key="q3", label_visibility="collapsed")
        
        st.markdown('<span class="interview-q">4. Endividamento: A empresa possui empréstimos? Qual o indexador (Selic, IPCA, fixo) e como isso impacta o caixa?</span>', unsafe_allow_html=True)
        q4 = st.text_area("Resposta 4", value=diary.get('q4', ''), key="q4", label_visibility="collapsed")
        
        st.markdown('<span class="interview-q">5. Observações Extras: Notas sobre o layout, clima organizacional ou gargalos produtivos.</span>', unsafe_allow_html=True)
        q5 = st.text_area("Resposta 5", value=diary.get('q5', ''), key="q5", label_visibility="collapsed")
        
        if st.form_submit_button("Salvar Guia de Entrevista"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2, "q3":q3, "q4":q4, "q5":q5})
            st.success("Diagnóstico salvo com sucesso!")

# --- 5. MÓDULO MICRO ---
elif menu == "5. Módulo Micro (Estratégia)":
    st.title("🔬 Módulo de Análise Microeconômica")
    t1, t2, t3 = st.tabs(["5 Forças de Porter", "Cálculo HHI (Concentração)", "Matriz SWOT (FOFA)"])
    
    with t1:
        st.markdown('<div class="guide-text">Avalie as forças competitivas de 1 a 5.</div>', unsafe_allow_html=True)
        p = data.get('porter', {})
        c1, c2 = st.columns(2)
        p1 = c1.slider("Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        p2 = c1.slider("Fornecedores", 1, 5, int(safe_float(p.get('p2', 3))))
        p3 = c1.slider("Clientes", 1, 5, int(safe_float(p.get('p3', 3))))
        p4 = c2.slider("Substitutos", 1, 5, int(safe_float(p.get('p4', 3))))
        p5 = c2.slider("Rivalidade", 1, 5, int(safe_float(p.get('p5', 3))))
        if st.button("Sincronizar Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1,"p2":p2,"p3":p3,"p4":p4,"p5":p5})
            st.success("Porter Salvo!")

    with t2:
        st.markdown('<div class="guide-text">Preencha o Market Share das maiores empresas do setor para calcular a concentração.</div>', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 1.5])
        with c1:
            s1 = st.number_input("Share Empresa Líder (%)", 0.0, 100.0, 30.0)
            s2 = st.number_input("Share 2º Concorrente (%)", 0.0, 100.0, 20.0)
            s3 = st.number_input("Share 3º Concorrente (%)", 0.0, 100.0, 10.0)
            restante = max(0.0, 100.0 - (s1+s2+s3))
            st.info(f"Outros concorrentes: {restante}%")
            shares_str = f"{s1},{s2},{s3},{restante}"
            if st.button("Salvar Análise HHI"):
                save_data(st.session_state.group, "hhi", shares_str)
                st.success("HHI Atualizado!")
        with c2:
            h_calc = sum([x**2 for x in [s1, s2, s3, restante]])
            st.metric("HHI Final", int(h_calc))
            st.plotly_chart(px.pie(values=[s1, s2, s3, restante], names=["Líder", "2º", "3º", "Outros"], hole=0.4))

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
    st.title("🏦 Diagnóstico Monetário e Sensibilidade")
    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_nome = st.selectbox("Indexador", ["Selic", "TJLP", "IGP-M", "IPCA", "Outro"], index=0)
        idx_val = st.number_input(f"Valor do {idx_nome} (%)", value=safe_float(dre_d.get('idx_valor', 10.75)))
        spread = st.number_input("Spread Bancário (+%)", value=safe_float(dre_d.get('spread', 2.0)))
        rec = st.number_input("Receita Bruta (R$)", value=safe_float(dre_d.get('receita', 1000000)))
        cus = st.number_input("Custos Totais (R$)", value=safe_float(dre_d.get('custos', 700000)))
        div = st.number_input("Dívida Total (R$)", value=safe_float(dre_d.get('divida', 400000)))
        if st.button("Salvar Dados Macro"):
            save_data(st.session_state.group, "dre", {"idx_nome":idx_nome, "idx_valor":idx_val, "spread":spread, "receita":rec, "custos":cus, "divida":div})
            st.rerun()
    with c2:
        ebitda = rec - cus
        sim = st.slider(f"Simular {idx_nome} (%)", 0.0, 30.0, idx_val)
        lucro_est = ebitda - (div * (sim + spread) / 100)
        st.metric("Lucro Estimado", f"R$ {lucro_est:,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div * (s + spread) / 100) for s in range(0,31)], title="Análise de Ponto de Ruptura")
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig)

# --- 7. FINANCEIRO ---
elif menu == "7. Módulo Financeiro & Valor":
    st.title("💰 Viabilidade, WACC e Valuation")
    w_d = data.get('wacc', {})
    t1, t2 = st.tabs(["WACC & EVA", "Avaliação de Perpetuidade"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            ke = st.number_input("Ke (Próprio %)", value=safe_float(w_d.get('ke', 15)))
            kd = st.number_input("Kd (Terceiros %)", value=safe_float(w_d.get('kd', 12)))
            eq = st.slider("Equity Ratio (%)", 0, 100, int(safe_float(w_d.get('eq_ratio', 60)))) / 100
            w_calc = (eq * (ke/100)) + ((1 - eq) * (kd/100) * 0.66)
            st.metric("WACC Final", f"{w_calc*100:.2f}%")
        with c2:
            roi = st.number_input("ROI da Empresa (%)", value=safe_float(w_d.get('roi', 18)))
            eva = roi - (selic_ref + 5.0)
            st.metric("Criação de Valor (EVA)", f"{eva:.2f}%")
            if st.button("Salvar Dados Financeiros"):
                save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":w_calc*100})
    with t2:
        g = st.slider("Crescimento (g) %", 0.0, 10.0, safe_float(w_d.get('g_growth', 3.0)))
        if st.button("Salvar g"):
            save_data(st.session_state.group, "wacc", {**w_d, "g_growth": g})
            st.rerun()
        ebit_base = safe_float(data.get('dre', {}).get('receita')) - safe_float(data.get('dre', {}).get('custos'))
        w_base = safe_float(w_d.get('wacc_final')) / 100
        g_base = g / 100
        if w_base > g_base:
            val = (ebit_base * (1 + g_base)) / (w_base - g_base)
            st.metric("Enterprise Value (DCF)", f"R$ {val:,.2f}")
        else: st.error("O WACC deve ser maior que g.")

# --- 8. RELATÓRIO ---
elif menu == "8. Relatório Final":
    st.title("📄 Relatório Consolidado de Consultoria")
    st.divider()
    info = data.get('company_info', {})
    part = data.get('participants', {})
    diary = data.get('diary', {})
    
    st.header(f"Projeto: {info.get('nome', 'N/A')}")
    st.write(f"**Equipe:** {part.get('aluno1')}, {part.get('aluno2')}, {part.get('aluno3')}, {part.get('aluno4')}, {part.get('aluno5')}")
    st.write(f"**Orientador:** {part.get('professor', 'N/A')}")
    
    st.divider()
    st.subheader("Diagnóstico Qualitativo (Entrevistas)")
    st.write(f"**Estratégia:** {diary.get('q1', '-')}")
    st.write(f"**Custos/Operação:** {diary.get('q2', '-')}")
    st.write(f"**Mercado:** {diary.get('q3', '-')}")
    st.button("Exportar para PDF (Ctrl+P)")
