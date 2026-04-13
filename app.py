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

# --- CSS MASTER DIDÁTICO ---
st.markdown("""
    <style>
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    .stApp { background-color: #f8fafc !important; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #0f172a !important; min-width: 320px !important; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] h2 { color: #f1f5f9 !important; }
    h1, h2, h3 { color: #002e5d !important; font-weight: 800; }
    
    /* Cards do Focus na Sidebar */
    .focus-box { 
        background-color: #1e293b; 
        padding: 12px; 
        border-radius: 8px; 
        border-left: 4px solid #3b82f6; 
        margin-bottom: 10px;
    }
    .focus-title { color: #94a3b8; font-size: 0.75rem; font-weight: bold; text-transform: uppercase; }
    .focus-value { color: #ffffff; font-size: 1.1rem; font-weight: 700; }
    
    .insight-box { background-color: #ffffff; padding: 20px; border-left: 6px solid #0052cc; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
    .formula-text { font-family: 'Courier New', Courier, monospace; background-color: #f8f9fa; padding: 10px; border-radius: 5px; font-size: 0.85em; color: #d63384; border: 1px solid #ddd; display: block; margin: 10px 0;}
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
        proximo = str(datetime.now().year + 1)
        return df[df['DataReferencia'].isin([atual, proximo])]
    except: return pd.DataFrame()

# --- CONEXÃO SUPABASE ---
try:
    supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
except:
    st.error("Erro de conexão com o banco de dados.")
    st.stop()

# --- FUNÇÕES DE SEGURANÇA E DADOS ---
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
            for col in ['porter', 'dre', 'wacc', 'swot', 'participants', 'company_info', 'diary']:
                row[col] = safe_json(row.get(col))
            return row
    except: pass
    return {'group_id': gid, 'porter': {}, 'dre': {}, 'wacc': {}, 'swot': {}, 'hhi': '0', 'diary': {}, 'participants': {}, 'company_info': {}, 'feedback': ''}

def save_data(gid, column, value):
    if isinstance(value, (dict, list)): value = json.dumps(value)
    supabase.table("eco_data").upsert({"group_id": gid, column: str(value)}).execute()

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if 'is_teacher' not in st.session_state: st.session_state.is_teacher = False

if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    col_l1, col_l2, col_l3 = st.columns([1, 1.6, 1])
    with col_l2:
        try: st.image("logo.png", use_container_width=True)
        except: pass
        group_sel = st.selectbox("Selecione seu Perfil", ["Grupo 1", "Grupo 2", "Grupo 3", "Acesso Professor"])
        pwd_input = st.text_input("Chave de Acesso", type="password")
        if st.button("Entrar no Hub"):
            passwords = st.secrets.get("GROUP_PASSWORDS", {})
            dev_pwd = st.secrets.get("DEV_PASSWORD")
            if pwd_input == passwords.get(group_sel) or pwd_input == dev_pwd:
                st.session_state.auth, st.session_state.group = True, ("Grupo 1" if group_sel == "Acesso Professor" else group_sel)
                st.session_state.is_teacher = (pwd_input == dev_pwd)
                st.rerun()
            else: st.error("Acesso Negado.")
    st.stop()

data = load_data(st.session_state.group)

# --- SIDEBAR (COM RELATÓRIO FOCUS DIDÁTICO) ---
with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    st.markdown(f"<h2>{st.session_state.group.upper()}</h2>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("<p style='color:#94a3b8; font-weight:700; font-size:0.8rem;'>EXPECTATIVAS MERCADO (FOCUS/BCB)</p>", unsafe_allow_html=True)
    df_focus = get_focus_projections()
    if not df_focus.empty:
        for idx, row in df_focus.iterrows():
            st.markdown(f"""
            <div class='focus-box'>
                <div class='focus-title'>{row['Indicador']} ({row['DataReferencia']})</div>
                <div class='focus-value'>{row['Mediana']}%</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    selic_meta = get_live_selic()
    st.info(f"Selic Atual: {selic_meta}%")
    selic_ref = st.number_input("Selic de Trabalho (%)", value=selic_meta, step=0.25)
    
    menu = st.radio("NAVEGAÇÃO", ["01 DASHBOARD", "02 EQUIPE", "03 PERFIL EMPRESA", "04 DIÁRIO DE CAMPO", "05 ESTRATÉGIA", "06 MONETÁRIO", "07 FINANCEIRO & VALOR", "08 RELATÓRIO FINAL"] + (["09 PORTAL DO ORIENTADOR"] if st.session_state.is_teacher else []))
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# --- 1. DASHBOARD ---
if menu == "01 DASHBOARD":
    st.title("📈 Painel Geral de Inteligência")
    # Mostrar feedback se existir
    fb = data.get('feedback', '')
    if fb: st.warning(f"📬 NOTA DO PROFESSOR: {fb}")
    
    info = data.get('company_info', {})
    st.markdown(f'<div class="insight-box"><h4>Cliente: {info.get("nome", "Pendente")}</h4><p>Nota consolidada baseada em Risco de Crédito, Mercado e Criação de Valor.</p></div>', unsafe_allow_html=True)
    
    # Cálculos Inteligentes
    dre_d = data.get('dre', {})
    ebitda = safe_float(dre_d.get('receita')) - safe_float(dre_d.get('custos'))
    divida = safe_float(dre_d.get('divida'))
    idx_total = safe_float(dre_d.get('idx_valor', selic_ref)) + safe_float(dre_d.get('spread', 2.0))
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
    if roi > (selic_ref + 5): score += 30

    col_g, col_s = st.columns([1.5, 2])
    with col_g:
        fig = go.Figure(go.Indicator(mode="gauge+number", value=score, title={'text':"Health Score"},
            gauge={'axis':{'range':[0,100]}, 'bar':{'color':"#2563eb"},
            'steps':[{'range':[0,50],'color':"#dc3545"},{'range':[50,75],'color':"#ffc107"},{'range':[75,100],'color':"#28a745"}]}))
        st.plotly_chart(fig, use_container_width=True)
    with col_s:
        c1, c2, c3 = st.columns(3)
        with c1:
            color = "#28a745" if selic_ref < break_even else "#dc3545" if break_even > 0 else "#6c757d"
            st.markdown(f'<div class="risk-card" style="background:{color}">CRÉDITO<br>{idx_total:.1f}%</div>', unsafe_allow_html=True)
        with c2:
            m_color = "#28a745" if hhi_val < 1500 else "#ffc107" if hhi_val < 2500 else "#dc3545"
            st.markdown(f'<div class="risk-card" style="background:{m_color}">MERCADO<br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
        with c3:
            v_color = "#28a745" if roi > (selic_ref+5) else "#dc3545"
            st.markdown(f'<div class="risk-card" style="background:{v_color}">VALOR (EVA)<br>ROI: {roi}%</div>', unsafe_allow_html=True)

# --- 6. MONETÁRIO (DIDÁTICO) ---
elif menu == "06 MONETÁRIO":
    st.title("🏦 Diagnóstico Monetário e Confronto com o Mercado")
    
    st.subheader("1. Projeções Oficiais do Mercado (Focus)")
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selic_24 = df_focus[df_focus['Indicador'] == 'Selic'].iloc[0]['Mediana'] if not df_focus.empty else 10.5
        st.info(f"O Mercado (Focus) projeta que a Selic feche o ano em **{selic_24}%**.")
    with col_f2:
        ipca_24 = df_focus[df_focus['Indicador'] == 'IPCA'].iloc[0]['Mediana'] if not df_focus.empty else 4.5
        st.info(f"A inflação (IPCA) esperada é de **{ipca_24}%**.")
        
    st.divider()
    st.subheader("2. Estrutura de Dívida da Empresa")
    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        rec = st.number_input("Receita Bruta Anual", value=safe_float(dre_d.get('receita', 1000000)))
        div = st.number_input("Dívida Total", value=safe_float(dre_d.get('divida', 400000)))
        idx_valor = st.number_input("Taxa de Juros da Empresa (%)", value=safe_float(dre_d.get('idx_valor', selic_ref)))
        if st.button("Salvar Dados Monetários"):
            save_data(st.session_state.group, "dre", {"receita":rec, "divida":div, "idx_valor":idx_valor})
            st.success("Dados Salvos!")
    with c2:
        ebitda = rec * 0.3 # Estimado para visualização
        sim = st.slider("Simular Selic (%)", 0.0, 25.0, selic_ref)
        lucro_e = ebitda - (div * sim/100)
        st.metric("Lucro Operacional Líquido Estimado", f"R$ {lucro_e:,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div*s/100) for s in range(0,31)], title="Análise de Ponto de Ruptura (EBITDA vs Juros)")
        fig.add_hline(y=0, line_dash="dash", line_color="red")
        st.plotly_chart(fig)

# --- 7. FINANCEIRO & VALOR (DIDÁTICO) ---
elif menu == "07 FINANCEIRO & VALOR":
    st.title("💰 Custo de Capital e Valor do Negócio")
    w_d = data.get('wacc', {})
    
    t1, t2 = st.tabs(["WACC & EVA", "Simulador Valuation (DCF)"])
    with t1:
        st.subheader("Cálculo do Custo Médio Ponderado de Capital")
        ke = st.number_input("Ke % (Retorno esperado pelos Sócios)", value=safe_float(w_d.get('ke', 15)))
        kd = st.number_input("Kd % (Juros cobrados pelos Bancos)", value=safe_float(w_d.get('kd', 12)))
        wacc = (ke * 0.6) + (kd * 0.4 * 0.66)
        st.metric("WACC Final", f"{wacc:.2f}%")
        
        roi = st.number_input("ROI Operacional da Empresa (%)", value=safe_float(w_d.get('roi', 18)))
        eva = roi - wacc
        st.metric("Economic Value Added (EVA)", f"{eva:.2f}%")
        if st.button("Salvar Financeiro"):
            save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "roi":roi, "wacc_final":wacc})

    with t2:
        st.subheader("Simulador de Valor de Mercado (Perpetuidade)")
        
        # BUSCA PIB DO FOCUS PARA ORIENTAR O ALUNO
        pib_proj = 2.0
        if not df_focus.empty:
            try: pib_proj = float(df_focus[df_focus['Indicador'] == 'PIB Total'].iloc[0]['Mediana'])
            except: pib_proj = 2.0
        
        st.markdown(f"""
        <div style='background-color:#eff6ff; padding:15px; border-radius:10px; border:1px solid #bfdbfe; color:#1e40af;'>
        <b>🎓 Guia do Consultor:</b> Para o cálculo do valor da empresa, você deve definir a taxa de crescimento futuro (g). 
        Estatisticamente, empresas maduras crescem próximas ao PIB do país. <br>
        O Relatório Focus projeta um crescimento do PIB de <b>{pib_proj}%</b> para este ano.
        </div>
        """, unsafe_allow_html=True)
        
        g = st.slider("Taxa de Crescimento Perpétuo (g) %", 0.0, 10.0, pib_proj)
        
        ebitda_v = safe_float(data.get('dre', {}).get('receita', 1000000)) * 0.3
        w_v = wacc / 100
        g_v = g / 100
        if w_v > g_v:
            val = (ebitda_v * (1 + g_v)) / (w_v - g_v)
            st.metric("Enterprise Value (Valor da Empresa)", f"R$ {val:,.2f}")
            st.latex(r"Enterprise \ Value = \frac{EBITDA \times (1 + g)}{WACC - g}")
        else: st.error("Inconsistência Acadêmica: O WACC deve ser maior que o crescimento (g).")

# (MANTENHA OS OUTROS MENUS 02, 03, 04, 05, 08 E 09 CONFORME O CÓDIGO ANTERIOR)
