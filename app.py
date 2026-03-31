import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EcoStrategy Hub", layout="wide", initial_sidebar_state="expanded")

# --- ESTILO "CLEAN CONSULTING" (CSS) ---
st.markdown("""
    <style>
    /* Fundo e texto principal */
    .stApp { background-color: #fcfcfc; color: #1e1e1e; }
    
    /* Sidebar com tom cinza suave */
    [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 1px solid #e0e0e0; }
    
    /* Títulos e Metric Cards */
    h1, h2, h3 { color: #002e5d; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-weight: 700; }
    
    /* Estilo dos cards brancos */
    .css-1r6slb0, .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    
    /* Botão Primário Blue */
    .stButton>button {
        background-color: #0052cc;
        color: white;
        border-radius: 4px;
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover { background-color: #003d99; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ATUALIZADO ---
conn = sqlite3.connect('ecostrategy_db.sqlite', check_same_thread=False)
c = conn.cursor()

# Adicionando colunas de caracterização se não existirem
c.execute('''CREATE TABLE IF NOT EXISTS data 
             (group_id TEXT PRIMARY KEY, 
              participants TEXT, 
              company_info TEXT, 
              diary TEXT, 
              porter TEXT, 
              hhi TEXT, 
              dre TEXT, 
              wacc TEXT)''')
conn.commit()

def save_data(gid, column, value):
    c.execute(f"INSERT OR IGNORE INTO data (group_id) VALUES ('{gid}')")
    c.execute(f"UPDATE data SET {column} = ? WHERE group_id = ?", (str(value), gid))
    conn.commit()

def load_data(gid):
    c.execute("SELECT * FROM data WHERE group_id = ?", (gid,))
    return c.fetchone()

# --- LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    st.subheader("Plataforma de Consultoria Econômica")
    with st.container():
        group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
        password = st.text_input("Senha de Acesso", type="password")
        if st.button("Entrar no Dashboard"):
            if password == "eco123":
                st.session_state.auth = True
                st.session_state.group = group
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()

# --- CARREGAR DADOS ---
db_row = load_data(st.session_state.group)
# Mapeamento do banco: 0:gid, 1:participants, 2:company_info, 3:diary, 4:porter, 5:hhi, 6:dre, 7:wacc

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3201/3201558.png", width=80)
    st.title(f"{st.session_state.group}")
    menu = st.radio("NAVEGAÇÃO", [
        "Dashboard Geral",
        "Caracterização do Grupo",
        "Diário de Bordo", 
        "Módulo Micro (Estratégia)", 
        "Módulo Macro (Monetário)", 
        "Módulo Financeiro", 
        "Relatório Final"
    ])

# --- 1. DASHBOARD GERAL ---
if menu == "Dashboard Geral":
    st.title("📊 Visão Geral do Projeto")
    
    # Cabeçalho Dinâmico
    company_name = db_row[2] if db_row and db_row[2] else "Empresa não definida"
    st.info(f"**Empresa em Análise:** {company_name}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Status do Projeto", "60%", "Em análise macro")
    with col2:
        st.metric("Dados Coletados", "12 registros", "+2 hoje")
    with col3:
        st.metric("Risco Setorial", "Moderado", "-5%")

    st.subheader("Cronograma de Entrega")
    st.write("- [x] Coleta de dados (Semana 2)\n- [x] Análise Micro (Semana 5)\n- [ ] Análise Macro (Semana 9)\n- [ ] Viabilidade (Semana 12)")

# --- 2. CARACTERIZAÇÃO DO GRUPO ---
elif menu == "Caracterização do Grupo":
    st.title("👥 Configuração do Projeto")
    
    with st.form("form_caracterizacao"):
        st.subheader("Membros do Grupo")
        membros = st.text_area("Nome dos Integrantes (um por linha)", 
                               value=db_row[1] if db_row and db_row[1] else "")
        
        st.divider()
        st.subheader("Dados da Empresa")
        col_emp1, col_emp2 = st.columns(2)
        with col_emp1:
            nome_empresa = st.text_input("Nome da Empresa Analisada", 
                                         value=db_row[2] if db_row and db_row[2] else "")
            setor = st.selectbox("Setor de Atuação", ["Indústria", "Varejo", "Serviços", "Agronegócio", "Tecnologia"])
        with col_emp2:
            descricao = st.text_area("Breve Descrição do Negócio", help="O que a empresa faz?")
            
        if st.form_submit_button("Salvar Configurações"):
            save_data(st.session_state.group, "participants", membros)
            save_data(st.session_state.group, "company_info", nome_empresa)
            st.success("Configurações salvas!")
            st.rerun()

# --- 3. DIÁRIO DE BORDO ---
elif menu == "Diário de Bordo":
    st.title("📔 Registro de Visitas e Entrevistas")
    with st.container():
        data_visita = st.date_input("Data da Visita")
        entrevistado = st.text_input("Pessoa Entrevistada (Nome/Cargo)")
        notas = st.text_area("Principais Insights e Notas da Entrevista", 
                             value=db_row[3] if db_row and db_row[3] else "", height=250)
        
        if st.button("Salvar Notas"):
            save_data(st.session_state.group, "diary", notas)
            st.success("Notas de campo arquivadas!")

# --- 4. MÓDULO MICRO ---
elif menu == "Módulo Micro (Estratégia)":
    st.title("🔬 Análise Microeconômica")
    
    tab1, tab2 = st.tabs(["Matriz de Porter", "Concentração (HHI)"])
    
    with tab1:
        st.subheader("Forças Competitivas")
        p1 = st.select_slider("Ameaça de Entrantes", options=["Baixa", "Média", "Alta"])
        p2 = st.select_slider("Poder dos Fornecedores", options=["Baixa", "Média", "Alta"])
        p3 = st.select_slider("Poder dos Clientes", options=["Baixa", "Média", "Alta"])
        
    with tab2:
        st.subheader("Calculadora de HHI")
        shares = st.text_input("Market Shares (ex: 30, 20, 50)")
        if shares:
            val = [float(x) for x in shares.split(",")]
            hhi = sum([x**2 for x in val])
            st.metric("Índice HHI", hhi)
            fig = px.pie(values=val, names=[f"Empresa {i+1}" for i in range(len(val))], hole=0.4)
            st.plotly_chart(fig)

# --- 5. MÓDULO MACRO ---
elif menu == "Módulo Macro (Monetário)":
    st.title("🏦 Cenário Monetário")
    
    col_m1, col_m2 = st.columns([1, 2])
    with col_m1:
        st.subheader("Dados do Balanço")
        receita = st.number_input("Receita Anual (R$)", value=1000000)
        divida = st.number_input("Endividamento Total (R$)", value=400000)
        
        st.divider()
        st.subheader("Focus / Bacen")
        selic_atual = st.slider("Simular Selic (%)", 5.0, 15.0, 10.75)
    
    with col_m2:
        custo_juros = divida * (selic_atual / 100)
        st.subheader("Impacto Financeiro da Selic")
        st.warning(f"Com a Selic em {selic_atual}%, a empresa gasta R$ {custo_juros:,.2f} apenas com juros da dívida.")
        
        # Gráfico de Projeção
        selics = [s for s in range(5, 16)]
        impactos = [divida * (s/100) for s in selics]
        fig_macro = px.area(x=selics, y=impactos, title="Custo da Dívida vs Taxa Selic",
                           labels={'x': 'Selic %', 'y': 'Despesa Financeira (R$)'})
        st.plotly_chart(fig_macro)

# --- 6. MÓDULO FINANCEIRO ---
elif menu == "Módulo Financeiro":
    st.title("💰 Viabilidade Econômica")
    roi = st.number_input("ROI da Empresa (%)", value=12.0)
    selic_bench = 10.75
    
    st.write("### ROI vs Custo de Oportunidade")
    fig_comp = go.Figure(go.Bar(
            x=['ROI da Empresa', 'Taxa Selic (Benchmark)'],
            y=[roi, selic_bench],
            text=[f"{roi}%", f"{selic_bench}%"],
            textposition='auto',
            marker_color=['#0052cc', '#d6d6d6']
        ))
    st.plotly_chart(fig_comp)

# --- 7. RELATÓRIO FINAL ---
elif menu == "Relatório Final":
    st.title("📄 Gerador de Relatório")
    st.write("Clique no botão abaixo para consolidar os dados para o PDF.")
    
    if st.button("Visualizar Sumário Executivo"):
        st.container()
        st.markdown(f"""
        # Relatório de Consultoria: {db_row[2] if db_row[2] else 'Empresa X'}
        **Grupo:** {st.session_state.group}  
        **Integrantes:** {db_row[1] if db_row[1] else 'Não informados'}
        
        ---
        ## 1. Diagnóstico de Campo
        {db_row[3] if db_row[3] else 'Sem registros no diário.'}
        
        ## 2. Análise de Viabilidade
        A empresa apresenta uma estrutura de capital sensível à taxa Selic. 
        (Dados gerados automaticamente pelo EcoStrategy Hub)
        """)
        st.button("Imprimir (Ctrl + P)")
