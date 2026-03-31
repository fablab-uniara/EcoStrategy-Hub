import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EcoStrategy Hub", layout="wide", initial_sidebar_state="expanded")

# --- ESTILO BLOOMBERG (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #0b0e11; color: #e1e1e1; }
    .stApp { background-color: #0b0e11; }
    [data-testid="stSidebar"] { background-color: #15191d; border-right: 1px solid #30363d; }
    h1, h2, h3 { color: #0096ff; font-family: 'Helvetica Neue', sans-serif; }
    .stButton>button { width: 100%; background-color: #0096ff; color: white; border-radius: 5px; }
    .card { background-color: #1c2128; padding: 20px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- BANCO DE DADOS ---
conn = sqlite3.connect('ecostrategy_db.sqlite', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS data (group_id TEXT PRIMARY KEY, diary TEXT, porter TEXT, hhi TEXT, dre TEXT, wacc TEXT)''')
conn.commit()

def save_data(gid, column, value):
    c.execute(f"INSERT OR IGNORE INTO data (group_id) VALUES ('{gid}')")
    c.execute(f"UPDATE data SET {column} = ? WHERE group_id = ?", (str(value), gid))
    conn.commit()

def load_data(gid):
    c.execute("SELECT * FROM data WHERE group_id = ?", (gid,))
    return c.fetchone()

# --- AUTENTICAÇÃO SIMPLES ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub - Login")
    group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
    password = st.text_input("Senha", type="password")
    if st.button("Acessar"):
        if password == "eco123": # Senha simples para exemplo
            st.session_state.auth = True
            st.session_state.group = group
            st.rerun()
    st.stop()

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    menu = st.radio("Navegação", [
        "Dashboard", 
        "Diário de Bordo", 
        "Módulo de Estratégia (Micro)", 
        "Módulo Monetário (Macro)", 
        "Módulo Financeiro", 
        "Repositório & Relatório"
    ])
    st.info("Status: Online - Sincronizado")

# Carregar dados iniciais
db_data = load_data(st.session_state.group)

# --- DASHBOARD ---
if menu == "Dashboard":
    st.title("📈 Dashboard de Progresso")
    
    # Simulação de progresso baseado em preenchimento (exemplo lógico)
    progress = 65 # Isso pode ser calculado dinamicamente
    st.write(f"Conclusão do Projeto: {progress}%")
    st.progress(progress / 100)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Visitas Realizadas", "4", "+1")
    col2.metric("HHI Calculado", "0.24", "Moderado")
    col3.metric("WACC Estimado", "12.5%", "-0.2%")

# --- DIÁRIO DE BORDO ---
elif menu == "Diário de Bordo":
    st.title("📔 Diário de Bordo (CRM)")
    with st.container():
        date = st.date_input("Data da Visita")
        notes = st.text_area("Notas da Entrevista / Observações", height=200)
        upload = st.file_uploader("Fotos da Visita", type=['png', 'jpg'])
        if st.button("Salvar Registro"):
            save_data(st.session_state.group, "diary", notes)
            st.success("Dados salvos com sucesso!")

# --- MÓDULO MICRO ---
elif menu == "Módulo de Estratégia (Micro)":
    st.title("🔬 Análise Microeconômica")
    
    st.subheader("Matriz de Porter")
    p1 = st.slider("Ameaça de Novos Entrantes", 1, 5, 3)
    p2 = st.slider("Poder de Negociação de Fornecedores", 1, 5, 3)
    p3 = st.slider("Poder de Negociação de Clientes", 1, 5, 3)
    p4 = st.slider("Ameaça de Substitutos", 1, 5, 3)
    p5 = st.slider("Rivalidade entre Concorrentes", 1, 5, 3)
    
    st.divider()
    
    st.subheader("Calculadora de HHI (Concentração)")
    shares_input = st.text_input("Insira Market Shares separadas por vírgula (ex: 40, 30, 20, 10)")
    if shares_input:
        shares = [float(x) for x in shares_input.split(",")]
        hhi = sum([x**2 for x in shares])
        st.write(f"**HHI: {hhi}**")
        
        fig = px.pie(values=shares, names=[f"Empresa {i+1}" for i in range(len(shares))], 
                     title="Market Share do Setor", color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig)

# --- MÓDULO MACRO ---
elif menu == "Módulo Monetário (Macro)":
    st.title("🏦 Cenário Monetário & Stress Test")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("DRE Simplificada (R$)")
        rev = st.number_input("Receita Bruta", value=1000000)
        costs = st.number_input("Custos Totais", value=600000)
        debt = st.number_input("Dívida Total da Empresa", value=500000)
    
    with col2:
        st.subheader("Relatório Focus (Input)")
        selic_meta = st.number_input("Meta Selic (%)", value=10.5)
        ipca_meta = st.number_input("Meta Inflação (%)", value=4.5)

    st.divider()
    st.subheader("⚡ Stress Test: Impacto dos Juros")
    selic_slider = st.slider("Simular Selic (%)", 5.0, 20.0, 10.5)
    
    # Lógica: Lucro = (Rec - Custos) - (Divida * Selic)
    ebitda = rev - costs
    impacto_juros = debt * (selic_slider / 100)
    lucro_liq = ebitda - impacto_juros
    
    st.metric("Lucro Líquido Estimado", f"R$ {lucro_liq:,.2f}", delta=f"{-impacto_juros:,.2f} Juros")
    
    # Gráfico de sensibilidade
    selics = [s for s in range(5, 21)]
    lucros = [ebitda - (debt * (s/100)) for s in selics]
    fig = px.line(x=selics, y=lucros, title="Sensibilidade Lucro vs Selic", labels={'x': 'Selic (%)', 'y': 'Lucro Líquido'})
    st.plotly_chart(fig)

# --- MÓDULO FINANCEIRO ---
elif menu == "Módulo Financeiro":
    st.title("💰 Viabilidade e Custo de Capital")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cálculo do WACC")
        re = st.number_input("Custo de Capital Próprio (Ke %)", value=15.0)
        rd = st.number_input("Custo da Dívida (Kd %)", value=12.0)
        ev = st.slider("Equity / Total Capital", 0.0, 1.0, 0.6)
        wacc = (ev * (re/100)) + ((1-ev) * (rd/100) * 0.66) # 0.66 considerando IR
        st.write(f"### WACC: {wacc*100:.2f}%")
    
    with col2:
        st.subheader("ROI vs Selic")
        roi = st.number_input("ROI da Empresa (%)", value=14.0)
        selic_atual = 10.75 # Exemplo
        
        fig = go.Figure(go.Bar(
            x=['ROI Empresa', 'Custo Oportunidade (Selic)'],
            y=[roi, selic_atual],
            marker_color=['#0096ff', '#ff4b4b']
        ))
        st.plotly_chart(fig)

# --- RELATÓRIO ---
elif menu == "Repositório & Relatório":
    st.title("📁 Gerador de Relatório Final")
    
    st.info("O botão abaixo compila todos os dados inseridos nas abas anteriores em um sumário executivo.")
    
    if st.button("Gerar Relatório Estruturado"):
        st.markdown("---")
        st.header(f"Relatório de Consultoria - {st.session_state.group}")
        st.subheader("1. Diagnóstico de Campo")
        st.write(db_data[1] if db_data else "Sem dados registrados.")
        
        st.subheader("2. Análise de Mercado (Micro)")
        st.write("Matriz de Porter e HHI calculados no sistema.")
        
        st.subheader("3. Vulnerabilidade Macro")
        st.write("Análise de sensibilidade Selic concluída.")
        
        st.success("Relatório pronto para impressão (Ctrl+P)")