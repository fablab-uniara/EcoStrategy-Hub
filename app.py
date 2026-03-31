import streamlit as st
from sqlalchemy import text

st.set_page_config(page_title="EcoStrategy Hub", layout="wide")

# Conexão automática usando os campos do Secret (Dicionário)
# O Streamlit vai ler host, port, user, password individualmente agora
conn = st.connection("postgresql", type="sql")

def init_db():
    try:
        with conn.session as s:
            s.execute(text("""
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
            s.commit()
            # st.success("Conectado ao Supabase com sucesso!") # Opcional: remover após testar
    except Exception as e:
        st.error(f"Erro de Conexão: O banco de dados recusou o acesso. Verifique a senha nos Secrets. Detalhes: {e}")

init_db()
init_db()
# Função de carregar dados protegida
def load_data(gid):
    if conn is None: return None
    try:
        with conn.session as s:
            return s.execute(text("SELECT * FROM eco_data WHERE group_id = :gid"), {"gid": gid}).fetchone()
    except:
        return None

# Funções de Banco de Dados
def save_data(gid, column, value):
    with conn.session as s:
        # Verifica se o grupo já existe
        res = s.execute(text("SELECT 1 FROM eco_data WHERE group_id = :gid"), {"gid": gid}).fetchone()
        if not res:
            s.execute(text("INSERT INTO eco_data (group_id) VALUES (:gid)"), {"gid": gid})
        
        # Atualiza o dado (protegido contra injeção de SQL)
        query = text(f"UPDATE eco_data SET {column} = :val WHERE group_id = :gid")
        s.execute(query, {"val": str(value), "gid": gid})
        s.commit()

def load_data(gid):
    with conn.session as s:
        return s.execute(text("SELECT * FROM eco_data WHERE group_id = :gid"), {"gid": gid}).fetchone()

# --- ESTILO CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; color: #1e1e1e; }
    [data-testid="stSidebar"] { background-color: #f0f2f6; }
    h1, h2, h3 { color: #002e5d; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { background-color: #0052cc; color: white; border-radius: 4px; }
    </style>
    """, unsafe_allow_html=True)

# --- LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
    password = st.text_input("Senha", type="password")
    if st.button("Acessar"):
        if password == "eco123":
            st.session_state.auth = True
            st.session_state.group = group
            st.rerun()
    st.stop()

# --- CARREGAR DADOS DO GRUPO ---
db_row = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    menu = st.radio("Navegação", ["Dashboard", "Caracterização", "Diário de Bordo", "Macro & Micro", "Relatório"])

# --- CONTEÚDO ---
if menu == "Dashboard":
    st.title("Visão Geral")
    st.write(f"Bem-vindo ao hub de consultoria do **{st.session_state.group}**.")
    company = db_row[2] if db_row and db_row[2] else "Empresa não definida"
    st.info(f"Projeto atual: {company}")

elif menu == "Caracterização":
    st.title("Configurações do Projeto")
    with st.form("config"):
        membros = st.text_area("Integrantes", value=db_row[1] if db_row and db_row[1] else "")
        empresa = st.text_input("Nome da Empresa", value=db_row[2] if db_row and db_row[2] else "")
        if st.form_submit_button("Salvar Tudo"):
            save_data(st.session_state.group, "participants", membros)
            save_data(st.session_state.group, "company_info", empresa)
            st.success("Dados salvos no Supabase!")
            st.rerun()

elif menu == "Diário de Bordo":
    st.title("Notas de Visita")
    notas = st.text_area("Descreva a visita técnica", value=db_row[3] if db_row and db_row[3] else "", height=300)
    if st.button("Salvar Diário"):
        save_data(st.session_state.group, "diary", notas)
        st.success("Diário atualizado!")

elif menu == "Macro & Micro":
    st.title("Análise Econômica")
    st.write("Aqui você pode inserir dados de HHI, Selic e WACC.")
    # Implementação simplificada para teste de banco
    hhi_val = st.text_input("HHI", value=db_row[5] if db_row and db_row[5] else "")
    if st.button("Salvar Análise"):
        save_data(st.session_state.group, "hhi", hhi_val)
        st.success("Análise salva!")

elif menu == "Relatório":
    st.title("Relatório Final")
    st.markdown(f"**Empresa:** {db_row[2]}")
    st.markdown(f"**Integrantes:** {db_row[1]}")
    st.markdown(f"**Diagnóstico:** {db_row[3]}")
    st.button("Imprimir (Ctrl+P)")
