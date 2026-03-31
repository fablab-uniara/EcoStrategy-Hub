import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="EcoStrategy Hub", layout="wide")

# --- CONEXÃO VIA API (Mais estável) ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- FUNÇÕES DE DADOS ---
def save_data(gid, column, value):
    # O Upsert insere ou atualiza automaticamente
    supabase.table("eco_data").upsert({"group_id": gid, column: str(value)}).execute()

def load_data(gid):
    response = supabase.table("eco_data").select("*").eq("group_id", gid).execute()
    return response.data[0] if response.data else None

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
data = load_data(st.session_state.group)

# --- NAVEGAÇÃO ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    menu = st.radio("MENU", ["Início", "Caracterização", "Diário de Bordo", "Análises", "Relatório"])

if menu == "Início":
    st.title("Bem-vindo ao EcoStrategy Hub")
    company = data.get('company_info', 'Nenhuma') if data else 'Nenhuma'
    st.info(f"📍 Projeto atual: {company}")

elif menu == "Caracterização":
    st.title("Configuração")
    with st.form("c"):
        membros = st.text_area("Integrantes", value=data.get('participants', '') if data else '')
        empresa = st.text_input("Empresa", value=data.get('company_info', '') if data else '')
        if st.form_submit_button("Salvar"):
            save_data(st.session_state.group, "participants", membros)
            save_data(st.session_state.group, "company_info", empresa)
            st.success("Salvo!")
            st.rerun()

elif menu == "Diário de Bordo":
    st.title("Diário")
    notas = st.text_area("Notas", value=data.get('diary', '') if data else '', height=300)
    if st.button("Salvar Diário"):
        save_data(st.session_state.group, "diary", notas)
        st.success("Atualizado!")

elif menu == "Análises":
    st.title("🔬 Análises Econômicas")
    # Exemplo de Stress Test
    divida = st.number_input("Dívida (R$)", value=100000)
    selic = st.slider("Selic (%)", 5.0, 20.0, 10.75)
    st.metric("Custo da Dívida", f"R$ {divida * (selic/100):,.2f}")

elif menu == "Relatório":
    st.title("📄 Relatório")
    if data:
        st.write(f"**Empresa:** {data.get('company_info')}")
        st.write(f"**Integrantes:** {data.get('participants')}")
        st.write(f"**Notas:** {data.get('diary')}")
