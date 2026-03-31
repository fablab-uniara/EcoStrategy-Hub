import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EcoStrategy Hub", layout="wide", initial_sidebar_state="expanded")

# --- CONEXÃO SUPABASE ---
URL: str = st.secrets["SUPABASE_URL"]
KEY: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(URL, KEY)

# --- ESTILO Bloomberg/TradingView (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; color: #1e1e1e; }
    [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 1px solid #dee2e6; }
    h1, h2, h3 { color: #002e5d; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 700; }
    .stMetric { background-color: white; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; }
    .stButton>button { background-color: #0052cc; color: white; border-radius: 4px; font-weight: 600; width: 100%; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 4px 4px 0 0; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE PERSISTÊNCIA ---
def save_data(gid, column, value):
    # Converte listas/dicionários para JSON string para salvar no banco
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    supabase.table("eco_data").upsert({"group_id": gid, column: str(value)}).execute()

def load_data(gid):
    res = supabase.table("eco_data").select("*").eq("group_id", gid).execute()
    if res.data:
        row = res.data[0]
        # Tenta converter colunas JSON de volta para objetos Python
        for col in ['porter', 'dre', 'wacc']:
            if row.get(col):
                try: row[col] = json.loads(row[col])
                except: pass
        return row
    return None

# --- LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    st.subheader("Plataforma SaaS de Consultoria Econômica")
    col_l1, col_l2 = st.columns([1, 2])
    with col_l1:
        group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
        password = st.text_input("Senha de Acesso", type="password")
        if st.button("Entrar no Hub"):
            if password == "eco123":
                st.session_state.auth = True
                st.session_state.group = group
                st.rerun()
            else: st.error("Senha inválida.")
    st.stop()

# --- CARREGAR DADOS DO GRUPO ---
data = load_data(st.session_state.group) or {}

# --- NAVEGAÇÃO LATERAL ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    menu = st.radio("NAVEGAÇÃO", [
        "Dashboard", 
        "Caracterização & Diário",
        "Módulo Micro (Estratégia)", 
        "Módulo Macro (Monetário)", 
        "Módulo Financeiro", 
        "Relatório Final"
    ])
    st.divider()
    st.caption("EcoStrategy Hub v1.5 - Online")

# --- 1. DASHBOARD ---
if menu == "Dashboard":
    st.title("📈 Visão Geral do Projeto")
    
    company = data.get('company_info', 'Empresa Não Definida')
    st.info(f"**Projeto:** Consultoria Estratégica - {company}")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Progresso Total", "65%", "+5%")
    col2.metric("Índice HHI", data.get('hhi', 'N/A'))
    col3.metric("Risco de Juros", "Alto", delta="Selic 10.75%", delta_color="inverse")

    st.subheader("Timeline do Semestre")
    progress_val = 65
    st.progress(progress_val/100)
    st.write("Semana 8: Finalizando Análise Monetária e Stress Test.")

# --- 2. CARACTERIZAÇÃO & DIÁRIO ---
elif menu == "Caracterização & Diário":
    st.title("👥 Caracterização e Campo")
    
    tab1, tab2 = st.tabs(["Dados do Projeto", "Diário de Bordo (Visitas)"])
    
    with tab1:
        with st.form("f_caract"):
            membros = st.text_area("Integrantes", value=data.get('participants', ''))
            empresa = st.text_input("Nome da Empresa", value=data.get('company_info', ''))
            setor = st.selectbox("Setor", ["Varejo", "Indústria", "Serviços", "Agro"])
            if st.form_submit_button("Salvar Configurações"):
                save_data(st.session_state.group, "participants", membros)
                save_data(st.session_state.group, "company_info", empresa)
                st.success("Dados salvos!")

    with tab2:
        st.subheader("Registro de Entrevistas")
        notas = st.text_area("Notas da última visita", value=data.get('diary', ''), height=250)
        if st.button("Salvar Diário"):
            save_data(st.session_state.group, "diary", notas)
            st.success("Diário atualizado!")

# --- 3. MÓDULO MICRO ---
elif menu == "Módulo Micro (Estratégia)":
    st.title("🔬 Análise Microeconômica")
    
    tab1, tab2 = st.tabs(["Matriz de Porter Interativa", "Calculadora HHI"])
    
    with tab1:
        st.subheader("5 Forças de Porter")
        colp1, colp2 = st.columns(2)
        with colp1:
            p1 = st.slider("Ameaça de Novos Entrantes", 1, 5, 3)
            p2 = st.slider("Poder dos Fornecedores", 1, 5, 3)
            p3 = st.slider("Poder dos Clientes", 1, 5, 3)
        with colp2:
            p4 = st.slider("Ameaça de Substitutos", 1, 5, 3)
            p5 = st.slider("Rivalidade entre Concorrentes", 1, 5, 3)
        
        if st.button("Salvar Matriz Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1, "p2":p2, "p3":p3, "p4":p4, "p5":p5})
            st.success("Matriz salva!")

    with tab2:
        st.subheader("Concentração de Mercado")
        shares_input = st.text_input("Market Shares separadas por vírgula (ex: 40, 30, 20)", value=data.get('hhi', ''))
        if shares_input:
            shares = [float(x.strip()) for x in shares_input.split(",")]
            hhi = sum([x**2 for x in shares])
            st.metric("HHI Calculado", int(hhi))
            
            fig = px.pie(values=shares, names=[f"Empresa {i+1}" for i in range(len(shares))], hole=0.4, title="Estrutura do Setor")
            st.plotly_chart(fig)
            if st.button("Salvar HHI"):
                save_data(st.session_state.group, "hhi", shares_input)

# --- 4. MÓDULO MACRO ---
elif menu == "Módulo Macro (Monetário)":
    st.title("🏦 Cenário Monetário & Stress Test")
    
    colm1, colm2 = st.columns([1, 1.5])
    
    with colm1:
        st.subheader("DRE Simplificada (R$)")
        receita = st.number_input("Receita Bruta Anual", value=1000000)
        custos = st.number_input("Custos e Despesas (exceto juros)", value=600000)
        divida = st.number_input("Endividamento Total", value=400000)
        ebitda = receita - custos

    with colm2:
        st.subheader("Simulador de Stress Test")
        st.write("Mova os sliders para ver o impacto da Política Monetária no Lucro:")
        selic_sim = st.slider("Taxa Selic (%)", 2.0, 20.0, 10.75)
        
        juros_anual = divida * (selic_sim / 100)
        lucro_liq = ebitda - juros_anual
        
        st.metric("Lucro Líquido Estimado", f"R$ {lucro_liq:,.2f}", delta=f"- R$ {juros_anual:,.2f} Juros")
        
        # Gráfico de Sensibilidade
        selics = list(range(2, 21))
        lucros = [ebitda - (divida * (s/100)) for s in selics]
        fig_macro = px.line(x=selics, y=lucros, title="Impacto da Selic no Lucro", labels={'x':'Selic %', 'y':'Lucro R$'})
        st.plotly_chart(fig_macro)

# --- 5. MÓDULO FINANCEIRO ---
elif menu == "Módulo Financeiro":
    st.title("💰 Viabilidade Econômica (WACC)")
    
    colf1, colf2 = st.columns(2)
    with colf1:
        ke = st.number_input("Custo Cap. Próprio (Ke %)", value=15.0)
        kd = st.number_input("Custo Cap. Terceiros (Kd %)", value=12.0)
        equity_ratio = st.slider("Participação de Capital Próprio (%)", 0, 100, 60) / 100
        
        wacc = (equity_ratio * (ke/100)) + ((1 - equity_ratio) * (kd/100) * 0.66)
        st.subheader(f"WACC: {wacc*100:.2f}%")

    with colf2:
        roi = st.number_input("ROI Atual da Empresa (%)", value=14.0)
        selic_oportunidade = 10.75
        
        fig_roi = go.Figure(go.Bar(
            x=['ROI Empresa', 'Custo de Oportunidade (Selic)'],
            y=[roi, selic_oportunidade],
            marker_color=['#0052cc', '#d1d1d1']
        ))
        st.plotly_chart(fig_roi)

# --- 6. RELATÓRIO FINAL ---
elif menu == "Relatório Final":
    st.title("📄 Gerador de Relatório de Consultoria")
    st.write("Clique abaixo para compilar todos os módulos inseridos.")
    
    if st.button("Gerar Sumário Executivo"):
        st.divider()
        st.header(f"Relatório de Consultoria: {data.get('company_info', 'N/A')}")
        st.markdown(f"**Grupo:** {st.session_state.group} | **Integrantes:** {data.get('participants', 'N/A')}")
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.subheader("1. Diagnóstico Micro")
            st.write(f"Índice HHI Setorial: {data.get('hhi', 'N/A')}")
            st.write("Matriz de Porter: Calculada e Analisada.")
        with col_r2:
            st.subheader("2. Diagnóstico Macro")
            st.write(f"Sensibilidade à Selic: Analisada no Módulo Monetário.")
            st.write(f"WACC Estimado: Concluído.")
            
        st.subheader("3. Notas de Campo")
        st.write(data.get('diary', 'Nenhum registro encontrado.'))
        
        st.success("Relatório pronto! Pressione Ctrl+P para salvar em PDF.")
