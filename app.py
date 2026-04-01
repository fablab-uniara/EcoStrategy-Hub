import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Hub - Professional BI", layout="wide", initial_sidebar_state="expanded")

# --- CSS WHITELABEL & DESIGN ELITE ---
st.markdown("""
    <style>
    /* Whitelabel - Ocultar Streamlit */
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}

    /* Design Profissional */
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 1px solid #e0e0e0; min-width: 320px !important; }
    h1, h2, h3 { color: #002e5d; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
    
    /* Blocos de BI */
    .risk-card { padding: 20px; border-radius: 12px; text-align: center; color: white; font-weight: bold; margin-bottom: 10px; border: 1px solid rgba(0,0,0,0.1); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .insight-box { background-color: #ffffff; padding: 20px; border-left: 6px solid #0052cc; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
    .formula-text { font-family: 'Courier New', Courier, monospace; background-color: #f8f9fa; padding: 12px; border-radius: 6px; font-size: 0.9em; color: #d63384; border: 1px solid #dee2e6; display: block; margin: 10px 0; line-height: 1.5;}
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
# --- LOGIN ---
if 'auth' not in st.session_state: 
    st.session_state.auth = False

if not st.session_state.auth:
    # 1. Centralização da Logo
    col_logo1, col_logo2, col_logo3 = st.columns([1, 1, 1])
    with col_logo2:
        # Altere "logo.png" para o nome do seu arquivo ou link da imagem
        try:
            st.image("logo.png", use_container_width=True)
        except:
            st.info("Logomarca (logo.png) não encontrada. Carregando modo padrão.")

    # 2. Títulos de Acesso
    st.markdown("<h1 style='text-align: center;'>🏛️ EcoStrategy Hub</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Login de Consultoria Acadêmica</h3>", unsafe_allow_html=True)
    
    st.divider()

    # 3. Formulário de Acesso
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1]) # Usando 3 colunas para centralizar o box de login
    with col_l2:
        group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
        password = st.text_input("Senha de Acesso", type="password")
        
        if st.button("Acessar Plataforma"):
            if password == "eco123":
                st.session_state.auth = True
                st.session_state.group = group
                st.rerun()
            else:
                st.error("Senha incorreta. Tente novamente.")
    
    st.stop() # Impede que o restante do app carregue sem login

data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
     # Insira sua logo aqui (ajuste o width conforme necessário)
    st.image("logo.png", use_container_width=True) 
    st.title(f"📊 {st.session_state.group}")
    # ... resto do código
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
    if st.button("Sair (Logout)"):
        st.session_state.auth = False
        st.rerun()

# --- 1. DASHBOARD ---
if menu == "1. Dashboard Executivo":
    st.title("📈 Painel de Inteligência BI")
    info = data.get('company_info', {})
    st.markdown(f'<div class="insight-box"><h4>Cliente: {info.get("nome", "Aguardando Perfil")}</h4><p>Status atual da viabilidade econômica e riscos estruturais.</p></div>', unsafe_allow_html=True)
    
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
        st.subheader("💎 Enterprise Value (Gordon)")
        if (w_final/100) > g_val:
            val_est = (ebitda * (1 + g_val)) / ((w_final/100) - g_val)
            st.metric("Valor do Negócio", f"R$ {val_est:,.2f}")
        else: st.warning("Cálculo de Valuation aguardando preenchimento financeiro.")
    with colb:
        st.subheader("🎯 Insights SWOT")
        sw = data.get('swot', {})
        st.write(f"**Principal Força:** {sw.get('f', '-')[:70]}...")
        st.write(f"**Principal Ameaça:** {sw.get('a', '-')[:70]}...")

# --- 2. IDENTIFICAÇÃO ---
elif menu == "2. Identificação da Equipe":
    st.title("👥 Composição da Equipe")
    st.markdown('<div class="guide-text"><b>Orientação:</b> Insira os nomes dos consultores e do professor.</div>', unsafe_allow_html=True)
    part = data.get('participants', {})
    with st.form("f_eq"):
        c1, c2 = st.columns(2)
        al1 = c1.text_input("Aluno 1 (Líder)", value=part.get('aluno1', ''))
        al2 = c1.text_input("Aluno 2", value=part.get('aluno2', ''))
        al3 = c1.text_input("Aluno 3", value=part.get('aluno3', ''))
        al4 = c2.text_input("Aluno 4", value=part.get('aluno4', ''))
        al5 = c2.text_input("Aluno 5", value=part.get('aluno5', ''))
        prof = c2.text_input("Professor Responsável", value=part.get('professor', ''))
        if st.form_submit_button("Sincronizar Equipe"):
            save_data(st.session_state.group, "participants", {"aluno1":al1, "aluno2":al2, "aluno3":al3, "aluno4":al4, "aluno5":al5, "professor":prof})
            st.success("Salvo!")

# --- 3. PERFIL EMPRESA ---
elif menu == "3. Perfil da Empresa":
    st.title("🏢 Perfil Corporativo")
    info = data.get('company_info', {})
    with st.form("f_emp"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome Fantasia", value=info.get('nome', ''))
        s = c1.selectbox("Setor", ["Varejo", "Indústria", "Serviços", "Agro", "Tech"], index=0)
        f = c1.text_input("Fundação (Ano)", value=info.get('fundacao', ''))
        colab = c2.number_input("Colaboradores", value=int(safe_float(info.get('colab', 0))))
        prod = c2.text_input("Produto Carro-chefe", value=info.get('produto', ''))
        desc = st.text_area("Breve Descrição", value=info.get('desc', ''))
        if st.form_submit_button("Salvar Perfil"):
            save_data(st.session_state.group, "company_info", {"nome":n, "setor":s, "fundacao":f, "colab":colab, "produto":prod, "desc":desc})
            st.success("Perfil Salvo!")

# --- 4. DIÁRIO DE BORDO ---
elif menu == "4. Guia de Entrevista (Campo)":
    st.title("📔 Diagnóstico Qualitativo")
    st.markdown('<div class="guide-text"><b>Instrução:</b> Registre as respostas coletadas na visita técnica.</div>', unsafe_allow_html=True)
    diary = data.get('diary', {})
    with st.form("f_dia"):
        q1 = st.text_area("1. Qual o principal diferencial competitivo?", value=diary.get('q1', ''))
        q2 = st.text_area("2. Como a Selic/Indexador afeta o caixa atual?", value=diary.get('q2', ''))
        q3 = st.text_area("3. Quem são os maiores rivais?", value=diary.get('q3', ''))
        q4 = st.text_area("4. Como é a relação com fornecedores?", value=diary.get('q4', ''))
        if st.form_submit_button("Salvar Entrevista"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2, "q3":q3, "q4":q4})
            st.success("Salvo!")

# --- 5. MICRO ---
elif menu == "5. Módulo Micro (Estratégia)":
    st.title("🔬 Análise Microeconômica")
    
    with st.expander("🎓 Saiba Mais: Matriz de Porter & HHI"):
        st.markdown("**1. 5 Forças de Porter:** Avalia a 'temperatura' da competição. Quanto maior o score (1-5), mais hostil é o setor.")
        st.markdown("**2. HHI (Herfindahl-Hirschman Index):** Mede a concentração de mercado.")
        st.markdown("<span class='formula-text'>HHI = s1² + s2² + s3² + ... + sn²</span>", unsafe_allow_html=True)
        st.markdown("**Interpretando o HHI:** < 1500 (Competitivo), 1500-2500 (Moderado), > 2500 (Oligopólio/Monopolístico).")

    t1, t2, t3 = st.tabs(["5 Forças de Porter", "HHI Guiado", "Matriz SWOT"])
    with t1:
        p = data.get('porter', {})
        c1, c2 = st.columns(2)
        p1 = c1.slider("Ameaça Novos Entrantes", 1, 5, int(safe_float(p.get('p1', 3))))
        p2 = c1.slider("Poder dos Fornecedores", 1, 5, int(safe_float(p.get('p2', 3))))
        p3 = c1.slider("Poder dos Clientes", 1, 5, int(safe_float(p.get('p3', 3))))
        p5 = c2.slider("Rivalidade Setorial", 1, 5, int(safe_float(p.get('p5', 3))))
        if st.button("Salvar Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1, "p2":p2, "p3":p3, "p5":p5})
            st.success("Porter Salvo!")
    with t2:
        st.markdown('<div class="guide-text">Preencha o Market Share (%) das principais empresas. O sistema calcula a atomização (Outros) automaticamente.</div>', unsafe_allow_html=True)
        s1 = st.number_input("Share Líder %", 0.0, 100.0, 30.0)
        s2 = st.number_input("Share 2º %", 0.0, 100.0, 20.0)
        s3 = st.number_input("Share 3º %", 0.0, 100.0, 10.0)
        rest = max(0.0, 100.0 - (s1+s2+s3))
        h_calc = s1**2 + s2**2 + s3**2 + rest**2
        st.metric("HHI Calculado", int(h_calc))
        st.plotly_chart(px.pie(values=[s1, s2, s3, rest], names=["Líder", "2º", "3º", "Outros"], hole=0.4))
        if st.button("Salvar HHI"):
            save_data(st.session_state.group, "hhi", f"{s1},{s2},{s3},{rest}")
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

# --- 6. MONETÁRIO ---
elif menu == "6. Módulo Macro (Monetário)":
    st.title("🏦 Cenário Monetário")
    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_nome = st.selectbox("Indexador", ["Selic", "TJLP", "IGP-M", "IPCA"], index=0)
        idx_val = st.number_input(f"Valor {idx_nome} (%)", value=safe_float(dre_d.get('idx_valor', 10.75)))
        spread = st.number_input("Spread (+ %)", value=safe_float(dre_d.get('spread', 2.0)))
        rec = st.number_input("Receita Bruta (R$)", value=safe_float(dre_d.get('receita', 1000000)))
        cus = st.number_input("Custos (R$)", value=safe_float(dre_d.get('custos', 700000)))
        div = st.number_input("Dívida (R$)", value=safe_float(dre_d.get('divida', 400000)))
        if st.button("Salvar Cenário"):
            save_data(st.session_state.group, "dre", {"idx_nome":idx_nome, "idx_valor":idx_val, "spread":spread, "receita":rec, "custos":cus, "divida":div})
            st.rerun()
    with c2:
        ebitda = rec - cus
        sim = st.slider(f"Simular {idx_nome} %", 0.0, 30.0, idx_val)
        lucro_e = ebitda - (div * (sim+spread)/100)
        st.metric("Lucro na Simulação", f"R$ {lucro_e:,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div*(s+spread)/100) for s in range(0,31)], title="Análise de Sensibilidade")
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig)

# --- 7. FINANCEIRO (CORRIGIDO) ---
elif menu == "7. Módulo Financeiro & Valor":
    st.title("💰 Viabilidade Econômica e Valor")
    
    with st.expander("🎓 Referencial de Análise: WACC, EVA e Valuation"):
        st.markdown("**1. WACC (Weighted Average Cost of Capital):** Custo médio ponderado de capital. Representa o retorno mínimo para compensar sócios e bancos.")
        st.markdown("<span class='formula-text'>WACC = (Equity/V * Ke) + (Debt/V * Kd * (1-T))</span>", unsafe_allow_html=True)
        st.markdown("**2. EVA (Economic Value Added):** Lucro econômico real. Se o ROI é menor que o WACC, o negócio está destruindo capital.")
        st.markdown("<span class='formula-text'>EVA % = ROI % - WACC %</span>", unsafe_allow_html=True)
        st.markdown("**3. Valuation (Gordon Growth):** Valor presente do negócio baseado na perpetuidade.")
        st.markdown("<span class='formula-text'>EV = Fluxo(1+g) / (WACC - g)</span>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["WACC & EVA", "Simulador de Valuation", "Interpretação Financeira"])
    w_d = data.get('wacc', {})
    
    with tab1:
        st.markdown('<div class="guide-text"><b>Guia:</b> Defina Ke (expectativa dos sócios) e Kd (juros do banco). O WACC será usado como taxa de desconto.</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            ke = st.number_input("Ke (Custo Cap. Próprio %)", value=safe_float(w_d.get('ke', 15.0)))
            kd = st.number_input("Kd (Custo Cap. Terceiros %)", value=safe_float(w_d.get('kd', 12.0)))
            eq = st.slider("Participação Equity (%)", 0, 100, int(safe_float(w_d.get('eq_ratio', 60)))) / 100
            w_calc = (eq * (ke/100)) + ((1 - eq) * (kd/100) * 0.66)
            st.metric("WACC Final Calculado", f"{w_calc*100:.2f}%")
        with c2:
            roi = st.number_input("ROI da Empresa (%)", value=safe_float(w_d.get('roi', 18.0)))
            eva = roi - (w_calc * 100)
            st.metric("Criação de Valor (EVA)", f"{eva:.2f}%", delta=f"{eva:.2f}%")
            if st.button("Salvar Resultados Financeiros"):
                save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":w_calc*100})

    with tab2:
        g = st.slider("Crescimento Perpétuo (g) %", 0.0, 10.0, safe_float(w_d.get('g_growth', 3.0)))
        if st.button("Sincronizar Crescimento"):
            save_data(st.session_state.group, "wacc", {**w_d, "g_growth": g})
            st.rerun()
        
        ebit_base = safe_float(data.get('dre', {}).get('receita')) - safe_float(data.get('dre', {}).get('custos'))
        w_base = safe_float(w_d.get('wacc_final')) / 100
        g_base = g / 100
        if w_base > g_base:
            val = (ebit_base * (1 + g_base)) / (w_base - g_base)
            st.metric("Enterprise Value Estimado", f"R$ {val:,.2f}")
        else: st.error("Erro: O WACC deve ser obrigatoriamente maior que o Crescimento (g).")

    with tab3:
        st.subheader("Análise de Viabilidade")
        if eva > 0:
            st.success(f"✅ **Criação de Valor:** A empresa gera um retorno de {roi}% contra um custo de {w_calc*100:.2f}%. Isso atrai investidores.")
        else:
            st.error(f"🚨 **Destruição de Valor:** O ROI ({roi}%) não cobre o custo de capital. Recomenda-se reduzir o endividamento ou aumentar a margem operacional.")

# --- 8. RELATÓRIO ---
elif menu == "8. Relatório Final":
    st.title("📄 Relatório Consolidado")
    st.write(f"Empresa: {data.get('company_info', {}).get('nome', 'N/A')} | Grupo: {st.session_state.group}")
    st.divider()
    st.subheader("Sumário Diário")
    st.info(data.get('diary', {}).get('q1', 'Sem registros.'))
    st.button("Exportar (Ctrl + P)")
