import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="EcoStrategy Hub", layout="wide")

# --- CONEXÃO MANUAL COM SUPABASE (Bypass Streamlit Errors) ---
@st.cache_resource
def get_engine():
    try:
        # Pega os dados do bloco [db] nos Secrets
        db = st.secrets["db"]
        url = f"postgresql://{db['user']}:{db['password']}@{db['host']}:{db['port']}/{db['database']}?sslmode=require"
        return create_engine(url, pool_pre_ping=True)
    except Exception as e:
        st.error(f"Erro de configuração nos Secrets: {e}")
        return None

engine = get_engine()

def init_db():
    if engine:
        try:
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS eco_data (
                        group_id TEXT PRIMARY KEY, 
                        participants TEXT, 
                        company_info TEXT, 
                        diary TEXT, 
                        porter TEXT, 
                        hhi TEXT, 
                        dre TEXT, 
                        wacc TEXT
                    );
                """))
                conn.commit()
        except Exception as e:
            st.error(f"Erro ao inicializar banco: {e}")

init_db()

# --- FUNÇÕES DE PERSISTÊNCIA ---
def save_data(gid, column, value):
    if engine:
        with engine.connect() as conn:
            # Verifica se grupo existe
            res = conn.execute(text("SELECT 1 FROM eco_data WHERE group_id = :gid"), {"gid": gid}).fetchone()
            if not res:
                conn.execute(text("INSERT INTO eco_data (group_id) VALUES (:gid)"), {"gid": gid})
            
            # Atualiza coluna específica
            query = text(f"UPDATE eco_data SET {column} = :val WHERE group_id = :gid")
            conn.execute(query, {"val": str(value), "gid": gid})
            conn.commit()

def load_data(gid):
    if engine:
        with engine.connect() as conn:
            return conn.execute(text("SELECT * FROM eco_data WHERE group_id = :gid"), {"gid": gid}).fetchone()
    return None

# --- DESIGN (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #f0f2f6; }
    h1, h2, h3 { color: #002e5d; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { background-color: #0052cc; color: white; width: 100%; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
    password = st.text_input("Senha", type="password")
    if st.button("Acessar Dashboard"):
        if password == "eco123":
            st.session_state.auth = True
            st.session_state.group = group
            st.rerun()
    st.stop()

# --- CARREGAR DADOS ---
db_row = load_data(st.session_state.group)

# --- NAVEGAÇÃO ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    menu = st.radio("MENU", ["Início", "Caracterização", "Diário de Bordo", "Análise Micro", "Cenário Macro", "Relatório Final"])

# --- CONTEÚDO DAS ABAS ---
if menu == "Início":
    st.title("Bem-vindo ao EcoStrategy Hub")
    company = db_row[2] if db_row and db_row[2] else "Nenhuma empresa cadastrada"
    st.info(f"📍 **Projeto atual:** {company}")
    st.write("Utilize o menu lateral para registrar visitas e realizar análises econômicas.")

elif menu == "Caracterização":
    st.title("👥 Configuração do Grupo e Empresa")
    with st.form("caract"):
        membros = st.text_area("Integrantes do Grupo", value=db_row[1] if db_row and db_row[1] else "")
        empresa = st.text_input("Nome da Empresa Analisada", value=db_row[2] if db_row and db_row[2] else "")
        if st.form_submit_button("Salvar Configurações"):
            save_data(st.session_state.group, "participants", membros)
            save_data(st.session_state.group, "company_info", empresa)
            st.success("Dados salvos com sucesso!")
            st.rerun()

elif menu == "Diário de Bordo":
    st.title("📔 Diário de Bordo")
    notas = st.text_area("Notas da Visita / Entrevista", value=db_row[3] if db_row and db_row[3] else "", height=300)
    if st.button("Salvar Notas"):
        save_data(st.session_state.group, "diary", notas)
        st.success("Diário atualizado!")

elif menu == "Análise Micro":
    st.title("🔬 Análise Microeconômica")
    st.subheader("Concentração de Mercado (HHI)")
    shares = st.text_input("Insira as Market Shares separadas por vírgula (ex: 40, 30, 20)", 
                           value=db_row[5] if db_row and db_row[5] else "")
    if shares:
        vals = [float(x.strip()) for x in shares.split(",")]
        hhi = sum([x**2 for x in vals])
        st.metric("Índice HHI", f"{int(hhi)}")
        fig = px.pie(values=vals, names=[f"Empresa {i+1}" for i in range(len(vals))], hole=0.4)
        st.plotly_chart(fig)
        if st.button("Salvar Dados HHI"):
            save_data(st.session_state.group, "hhi", shares)

elif menu == "Cenário Macro":
    st.title("🏦 Stress Test Monetário")
    divida = st.number_input("Endividamento da Empresa (R$)", value=100000)
    selic = st.slider("Simular Taxa Selic (%)", 5.0, 20.0, 10.75)
    custo = divida * (selic/100)
    st.warning(f"O custo anual da dívida com Selic a {selic}% é de R$ {custo:,.2f}")
    
    # Gráfico simples
    selics = list(range(5, 21))
    custos = [divida * (s/100) for s in selics]
    fig_macro = px.line(x=selics, y=custos, title="Sensibilidade Juros vs Dívida")
    st.plotly_chart(fig_macro)

elif menu == "Relatório Final":
    st.title("📄 Relatório Consolidado")
    st.markdown(f"**Empresa:** {db_row[2] if db_row else '-'}")
    st.markdown(f"**Alunos:** {db_row[1] if db_row else '-'}")
    st.markdown("---")
    st.subheader("Notas de Campo")
    st.write(db_row[3] if db_row else "-")
    st.button("Imprimir Relatório (Ctrl + P)")
