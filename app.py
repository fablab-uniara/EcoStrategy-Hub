import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import logging
import html
import requests
from supabase import create_client, Client

# --- LOGGING ---
logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Intelligence", layout="wide", initial_sidebar_state="expanded")

# --- CSS WHITELABEL & DESIGN DE ALTO CONTRASTE ---
st.markdown("""
    <style>
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    header {visibility: hidden !important;}

    .stApp { background-color: #f8fafc; font-family: 'Inter', -apple-system, sans-serif; }

    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; min-width: 310px !important; }
    [data-testid="stSidebar"] h2 { color: #ffffff !important; font-size: 1.3rem; font-weight: 800; text-align: center; margin-bottom: 10px; }
    [data-testid="stSidebar"] p { color: #cbd5e1 !important; font-size: 0.85rem; }
    [data-testid="stSidebar"] .stMarkdown { color: #f1f5f9 !important; }

    .stRadio > label { display: none; }
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap: 8px; padding-top: 15px; }
    [data-testid="stSidebar"] .stRadio label {
        color: #f1f5f9 !important;
        font-weight: 500 !important;
        font-size: 0.92rem !important;
        background-color: transparent;
        border-radius: 6px;
        padding: 10px 15px !important;
        transition: 0.2s all;
        cursor: pointer;
    }
    [data-testid="stSidebar"] .stRadio label:hover { background-color: #1e293b !important; color: #ffffff !important; }
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] { color: #f1f5f9 !important; }

    h1, h2, h3 { color: #0f172a; font-weight: 800; letter-spacing: -0.04em; }
    .risk-card { padding: 22px; border-radius: 8px; text-align: center; color: white; font-weight: 600; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .insight-box { background-color: #ffffff; padding: 25px; border-left: 5px solid #3b82f6; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 25px; border: 1px solid #f1f5f9; }

    .formula-text { font-family: 'SF Mono', monospace; background-color: #f1f5f9; padding: 12px; border-radius: 6px; font-size: 0.85em; color: #334155; border: 1px solid #e2e8f0; display: block; margin: 12px 0; }
    .guide-text { font-size: 0.9em; color: #475569; line-height: 1.6; background: #eff6ff; padding: 14px; border-radius: 6px; border: 1px solid #dbeafe; margin-bottom: 20px;}

    .stButton>button { background-color: #2563eb; color: white; border-radius: 6px; width: 100%; font-weight: 600; height: 48px; border: none; transition: 0.2s; }
    .stButton>button:hover { background-color: #1d4ed8; }
    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# UTILITÁRIOS
# ---------------------------------------------------------------------------

def safe_float(val, default=0.0):
    """Converte um valor para float de forma segura."""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_json(val, field_name="campo"):
    """Desserializa JSON com log de erros explícito."""
    if val is None or val == "" or val == "None":
        return {}
    if isinstance(val, dict):
        return val
    try:
        return json.loads(val)
    except json.JSONDecodeError as e:
        logging.warning("Falha ao parsear JSON no campo '%s': %s", field_name, e)
        return {}


def sanitize(text: str) -> str:
    """Escapa HTML de input do usuário para evitar XSS."""
    if not isinstance(text, str):
        return str(text) if text else ""
    return html.escape(text)


# ---------------------------------------------------------------------------
# API BANCO CENTRAL — CACHEADA
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def get_live_selic() -> float:
    """Busca a meta SELIC via API do BCB. Cache de 1 hora."""
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return float(response.json()[0]["valor"])
    except Exception as e:
        logging.warning("Falha ao obter SELIC da API BCB: %s", e)
        return 10.75


# ---------------------------------------------------------------------------
# CONEXÃO SUPABASE
# ---------------------------------------------------------------------------

@st.cache_resource
def get_supabase_client() -> Client:
    """Inicializa o cliente Supabase uma única vez."""
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


try:
    supabase = get_supabase_client()
except Exception as e:
    logging.error("Erro ao conectar ao Supabase: %s", e)
    st.error("Erro: Falha na conexão com o servidor de dados. Verifique as credenciais em st.secrets.")
    st.stop()


# ---------------------------------------------------------------------------
# PERSISTÊNCIA — com controle de acesso
# ---------------------------------------------------------------------------

def _assert_group_access(gid: str):
    """Garante que só o grupo autenticado acessa seus próprios dados."""
    if gid != st.session_state.get("group"):
        logging.warning("Tentativa de acesso não autorizado ao grupo '%s'", gid)
        st.error("Acesso negado.")
        st.stop()


def save_data(gid: str, column: str, value):
    """Salva apenas a coluna alterada (evita race condition de upsert total)."""
    _assert_group_access(gid)
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    try:
        # Tenta update primeiro; se não existir a linha, faz insert
        res = supabase.table("eco_data").select("group_id").eq("group_id", gid).execute()
        if res.data:
            supabase.table("eco_data").update({column: str(value)}).eq("group_id", gid).execute()
        else:
            supabase.table("eco_data").insert({"group_id": gid, column: str(value)}).execute()
    except Exception as e:
        logging.error("Erro ao salvar dados (grupo=%s, coluna=%s): %s", gid, column, e)
        st.error("Erro ao salvar. Tente novamente.")


def load_data(gid: str) -> dict:
    """Carrega dados do grupo autenticado."""
    _assert_group_access(gid)
    json_fields = ["porter", "dre", "wacc", "swot", "participants", "company_info", "diary"]
    empty = {
        "group_id": gid,
        **{f: {} for f in json_fields},
        "hhi": "0",
    }
    try:
        res = supabase.table("eco_data").select("*").eq("group_id", gid).execute()
        if not res.data:
            return empty
        row = res.data[0]
        for col in json_fields:
            row[col] = safe_json(row.get(col), field_name=col)
        return row
    except Exception as e:
        logging.error("Erro ao carregar dados (grupo=%s): %s", gid, e)
        st.warning("Não foi possível carregar os dados salvos. Usando valores padrão.")
        return empty


# ---------------------------------------------------------------------------
# CÁLCULOS DE NEGÓCIO (separados da UI)
# ---------------------------------------------------------------------------

def calc_ebitda(receita: float, custos: float) -> float:
    return receita - custos


def calc_wacc(ke: float, kd: float, eq_ratio: float) -> float:
    """Retorna WACC como decimal (ex: 0.142 para 14.2%)."""
    return (eq_ratio * (ke / 100)) + ((1 - eq_ratio) * (kd / 100) * 0.66)


def calc_eva(roi: float, wacc_pct: float) -> float:
    """EVA = ROI - WACC (ambos em %)."""
    return roi - wacc_pct


def calc_hhi(shares: list[float]) -> float:
    return sum(s ** 2 for s in shares)


def calc_enterprise_value(ebitda: float, wacc: float, g: float) -> float | None:
    """Gordon Growth Model. Retorna None se WACC <= g."""
    if wacc <= g:
        return None
    return (ebitda * (1 + g)) / (wacc - g)


def calc_health_score(ebitda: float, divida: float, idx_total: float,
                      hhi_val: float, roi: float, wacc_pct: float) -> int:
    score = 0
    break_even = (ebitda / divida * 100) if divida > 0 else 100
    if divida == 0 or idx_total < break_even:
        score += 40
    if hhi_val < 2500:
        score += 30
    if roi > wacc_pct:
        score += 30
    return score


# ---------------------------------------------------------------------------
# COMPLETUDE DOS MÓDULOS
# ---------------------------------------------------------------------------

REQUIRED_MODULES = {
    "dre": "06 Cenário Monetário",
    "wacc": "07 Viabilidade e Valor",
    "hhi": "05 Análise Estratégica (HHI)",
}


def check_completeness(data: dict) -> list[str]:
    """Retorna lista de módulos ainda não preenchidos."""
    missing = []
    for key, label in REQUIRED_MODULES.items():
        val = data.get(key)
        if not val or val == "0" or val == {}:
            missing.append(label)
    return missing


# ---------------------------------------------------------------------------
# AUTENTICAÇÃO
# ---------------------------------------------------------------------------

def _verify_password(group: str, password: str) -> bool:
    """Verifica senha por grupo via st.secrets (sem plaintext no código)."""
    try:
        passwords: dict = st.secrets["GROUP_PASSWORDS"]
        expected = passwords.get(group, "")
        # Comparação simples de string — para produção use bcrypt
        return password == expected and password != ""
    except KeyError:
        # Fallback de desenvolvimento: senha única via secret
        fallback = st.secrets.get("DEV_PASSWORD", "")
        return fallback != "" and password == fallback


if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h2 style='text-align: center; color: #0f172a; padding-top: 50px;'>ECOSTRATEGY INTELLIGENCE</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.6, 1])
    with col_l2:
        try:
            st.image("logo.png", use_container_width=True)
        except Exception:
            pass
        group = st.selectbox("Selecione sua Unidade", ["Grupo 1", "Grupo 2", "Grupo 3"])
        pwd = st.text_input("Credencial de Acesso", type="password")
        if st.button("Acessar Plataforma"):
            if _verify_password(group, pwd):
                st.session_state.auth = True
                st.session_state.group = group
                st.rerun()
            else:
                st.error("Credencial inválida.")
    st.stop()

# --- Carrega dados do grupo autenticado ---
data = load_data(st.session_state.group)

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------

with st.sidebar:
    try:
        st.image("logo.png", use_container_width=True)
    except Exception:
        pass

    st.markdown(f"<h2>{sanitize(st.session_state.group).upper()}</h2>", unsafe_allow_html=True)
    st.divider()

    st.markdown("<p style='font-weight: 700; color: #94a3b8; letter-spacing: 0.1em;'>CENÁRIO MACRO</p>", unsafe_allow_html=True)
    selic_meta = get_live_selic()
    st.markdown(f"<p style='color: #10b981; font-size: 0.9rem; font-weight: 600;'>Selic Meta Oficial: {selic_meta}%</p>", unsafe_allow_html=True)
    selic_ref = st.number_input("Taxa de Trabalho (%)", value=selic_meta, step=0.25)

    st.divider()
    st.markdown("<p style='font-weight: 700; color: #94a3b8; letter-spacing: 0.1em;'>NAVEGAÇÃO</p>", unsafe_allow_html=True)

    menu = st.radio("MENU", [
        "01 DASHBOARD EXECUTIVO",
        "02 GOVERNANÇA E EQUIPE",
        "03 PERFIL CORPORATIVO",
        "04 DIAGNÓSTICO DE CAMPO",
        "05 ANÁLISE ESTRATÉGICA",
        "06 CENÁRIO MONETÁRIO",
        "07 VIABILIDADE E VALOR",
        "08 RELATÓRIO FINAL"
    ], label_visibility="collapsed")

    st.divider()
    if st.button("Finalizar Sessão"):
        st.session_state.auth = False
        st.session_state.group = None
        st.rerun()


# ---------------------------------------------------------------------------
# 1. DASHBOARD EXECUTIVO
# ---------------------------------------------------------------------------

if menu == "01 DASHBOARD EXECUTIVO":
    st.title("Executive Management Dashboard")
    info = data.get("company_info", {})
    nome_empresa = sanitize(info.get("nome", "Não Identificada"))
    st.markdown(
        f'<div class="insight-box"><h4>Unidade Analisada: {nome_empresa}</h4>'
        f'<p>Sumário de indicadores de risco e criação de valor econômico.</p></div>',
        unsafe_allow_html=True
    )

    # Aviso de completude
    missing = check_completeness(data)
    if missing:
        st.warning(
            "⚠️ Os seguintes módulos ainda não foram preenchidos — o Health Score pode estar incompleto: "
            + ", ".join(f"**{m}**" for m in missing)
        )

    dre_d = data.get("dre", {})
    receita = safe_float(dre_d.get("receita"))
    custos = safe_float(dre_d.get("custos"))
    ebitda = calc_ebitda(receita, custos)
    divida = safe_float(dre_d.get("divida"))
    idx_total = safe_float(dre_d.get("idx_valor")) + safe_float(dre_d.get("spread"))

    hhi_str = str(data.get("hhi", "0"))
    try:
        hhi_val = calc_hhi([float(x) for x in hhi_str.split(",") if x.strip()])
    except ValueError:
        hhi_val = 0.0

    w_d = data.get("wacc", {})
    roi = safe_float(w_d.get("roi"))
    w_final = safe_float(w_d.get("wacc_final", 15.0))

    score = calc_health_score(ebitda, divida, idx_total, hhi_val, roi, w_final)

    col_gauge, col_sem = st.columns([1.5, 2])
    with col_gauge:
        fig_health = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "Health Score Index", "font": {"size": 18}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#2563eb"},
                "steps": [
                    {"range": [0, 50], "color": "#ef4444"},
                    {"range": [50, 75], "color": "#f59e0b"},
                    {"range": [75, 100], "color": "#10b981"},
                ],
            },
        ))
        st.plotly_chart(fig_health, use_container_width=True)

    with col_sem:
        c1, c2, c3 = st.columns(3)
        break_even = (ebitda / divida * 100) if divida > 0 else 0
        with c1:
            color = "#10b981" if idx_total < break_even else ("#ef4444" if break_even > 0 else "#94a3b8")
            st.markdown(f'<div class="risk-card" style="background:{color}">CRÉDITO<br>{idx_total:.1f}%</div>', unsafe_allow_html=True)
        with c2:
            m_color = "#10b981" if hhi_val < 1500 else ("#f59e0b" if hhi_val < 2500 else "#ef4444")
            st.markdown(f'<div class="risk-card" style="background:{m_color}">MERCADO<br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
        with c3:
            v_color = "#10b981" if roi > w_final else "#ef4444"
            st.markdown(f'<div class="risk-card" style="background:{v_color}">VALOR (EVA)<br>ROI: {roi}%</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# 2. GOVERNANÇA E EQUIPE
# ---------------------------------------------------------------------------

elif menu == "02 GOVERNANÇA E EQUIPE":
    st.title("Governança e Equipe")
    st.markdown('<div class="guide-text">Registre os membros da equipe de consultoria e o professor orientador.</div>', unsafe_allow_html=True)
    part = data.get("participants", {})
    with st.form("f_eq"):
        c1, c2 = st.columns(2)
        al1 = c1.text_input("Consultor 1 (Líder)", value=part.get("aluno1", ""))
        al2 = c1.text_input("Consultor 2", value=part.get("aluno2", ""))
        al3 = c1.text_input("Consultor 3", value=part.get("aluno3", ""))
        al4 = c2.text_input("Consultor 4", value=part.get("aluno4", ""))
        al5 = c2.text_input("Consultor 5", value=part.get("aluno5", ""))
        prof = c2.text_input("Professor Orientador", value=part.get("professor", ""))
        if st.form_submit_button("Sincronizar Governança"):
            with st.spinner("Sincronizando..."):
                save_data(
                    st.session_state.group,
                    "participants",
                    {"aluno1": al1, "aluno2": al2, "aluno3": al3,
                     "aluno4": al4, "aluno5": al5, "professor": prof},
                )
            st.toast("Dados salvos com sucesso!", icon="✅")


# ---------------------------------------------------------------------------
# 3. PERFIL CORPORATIVO
# ---------------------------------------------------------------------------

elif menu == "03 PERFIL CORPORATIVO":
    st.title("Perfil Corporativo do Cliente")
    info = data.get("company_info", {})
    setores = ["Varejo", "Indústria", "Serviços", "Agro", "Tech"]
    setor_atual = info.get("setor", "Varejo")
    setor_idx = setores.index(setor_atual) if setor_atual in setores else 0
    with st.form("f_emp"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Razão Social", value=info.get("nome", ""))
        setor = c1.selectbox("Setor", setores, index=setor_idx)
        fund = c1.text_input("Ano Fundação", value=info.get("fundacao", ""))
        colab = c2.number_input("Funcionários", value=int(safe_float(info.get("colab", 0))), min_value=0)
        prod = c2.text_input("Produto Carro-chefe", value=info.get("produto", ""))
        desc = st.text_area("Modelo de Negócio", value=info.get("desc", ""))
        if st.form_submit_button("Salvar Perfil"):
            with st.spinner("Sincronizando..."):
                save_data(
                    st.session_state.group,
                    "company_info",
                    {"nome": nome, "setor": setor, "fundacao": fund,
                     "colab": colab, "produto": prod, "desc": desc},
                )
            st.toast("Perfil sincronizado!", icon="✅")


# ---------------------------------------------------------------------------
# 4. DIAGNÓSTICO DE CAMPO
# ---------------------------------------------------------------------------

elif menu == "04 DIAGNÓSTICO DE CAMPO":
    st.title("Diagnóstico Qualitativo de Campo")
    st.markdown('<div class="guide-text">Roteiro de entrevista estruturado para coleta de dados "in loco".</div>', unsafe_allow_html=True)
    diary = data.get("diary", {})
    with st.form("f_dia"):
        q1 = st.text_area("1. Histórico e Diferencial Competitivo", value=diary.get("q1", ""))
        q2 = st.text_area("2. Impacto de Variáveis Macro (Juros/Inflação)", value=diary.get("q2", ""))
        q3 = st.text_area("3. Estrutura de Mercado e Concorrência", value=diary.get("q3", ""))
        q4 = st.text_area("4. Gestão de Endividamento e Indexadores", value=diary.get("q4", ""))
        if st.form_submit_button("Sincronizar Notas"):
            with st.spinner("Sincronizando..."):
                save_data(st.session_state.group, "diary", {"q1": q1, "q2": q2, "q3": q3, "q4": q4})
            st.toast("Diário atualizado!", icon="✅")


# ---------------------------------------------------------------------------
# 5. ANÁLISE ESTRATÉGICA
# ---------------------------------------------------------------------------

elif menu == "05 ANÁLISE ESTRATÉGICA":
    st.title("Inteligência Estratégica")
    t1, t2, t3 = st.tabs(["5 Forças de Porter", "Concentração HHI", "Matriz SWOT"])

    with t1:
        p = data.get("porter", {})
        c1, c2 = st.columns(2)
        p1 = c1.slider("Novos Entrantes", 1, 5, int(safe_float(p.get("p1", 3))))
        p2 = c1.slider("Poder Fornecedores", 1, 5, int(safe_float(p.get("p2", 3))))
        p3 = c1.slider("Poder Clientes", 1, 5, int(safe_float(p.get("p3", 3))))
        p5 = c2.slider("Rivalidade Rivais", 1, 5, int(safe_float(p.get("p5", 3))))
        if st.button("Salvar Porter"):
            with st.spinner("Salvando..."):
                save_data(st.session_state.group, "porter", {"p1": p1, "p2": p2, "p3": p3, "p5": p5})
            st.toast("Porter salvo!", icon="✅")

    with t2:
        s1 = st.number_input("Share Líder %", 0.0, 100.0, 30.0)
        s2 = st.number_input("Share 2º %", 0.0, 100.0, 20.0)
        s3 = st.number_input("Share 3º %", 0.0, 100.0, 10.0)
        rest = max(0.0, 100.0 - (s1 + s2 + s3))
        h_calc = calc_hhi([s1, s2, s3, rest])
        st.metric("HHI Final", int(h_calc))
        if h_calc < 1500:
            st.success("Mercado desconcentrado (HHI < 1.500)")
        elif h_calc < 2500:
            st.warning("Mercado moderadamente concentrado (1.500 ≤ HHI < 2.500)")
        else:
            st.error("Mercado altamente concentrado (HHI ≥ 2.500)")
        st.plotly_chart(
            px.pie(values=[s1, s2, s3, rest], names=["Líder", "2º", "3º", "Outros"], hole=0.4),
            use_container_width=True,
        )
        if st.button("Salvar HHI"):
            with st.spinner("Salvando..."):
                save_data(st.session_state.group, "hhi", f"{s1},{s2},{s3},{rest}")
            st.toast("HHI salvo!", icon="✅")

    with t3:
        sw = data.get("swot", {})
        with st.form("f_sw"):
            c1, c2 = st.columns(2)
            f = c1.text_area("Forças", value=sw.get("f", ""))
            fra = c2.text_area("Fraquezas", value=sw.get("fra", ""))
            o = c1.text_area("Oportunidades", value=sw.get("o", ""))
            a = c2.text_area("Ameaças", value=sw.get("a", ""))
            if st.form_submit_button("Salvar SWOT"):
                with st.spinner("Salvando..."):
                    save_data(st.session_state.group, "swot", {"f": f, "fra": fra, "o": o, "a": a})
                st.toast("SWOT salvo!", icon="✅")
                st.rerun()


# ---------------------------------------------------------------------------
# 6. CENÁRIO MONETÁRIO
# ---------------------------------------------------------------------------

elif menu == "06 CENÁRIO MONETÁRIO":
    st.title("Stress Test Monetário")
    dre_d = data.get("dre", {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_nome = st.selectbox("Indexador", ["Selic", "TJLP", "IPCA", "IGP-M"], index=0)
        # MELHORIA: usa selic_ref da sidebar como valor padrão, conectando macro → micro
        idx_val = st.number_input(
            f"Valor {idx_nome} %",
            value=safe_float(dre_d.get("idx_valor", selic_ref)),
        )
        spread = st.number_input("Spread Bancário %", value=safe_float(dre_d.get("spread", 2.0)))
        rec = st.number_input("Receita Bruta", value=safe_float(dre_d.get("receita", 1_000_000)), min_value=0.0)
        cus = st.number_input("Custos Operacionais", value=safe_float(dre_d.get("custos", 700_000)), min_value=0.0)
        div = st.number_input("Dívida Total", value=safe_float(dre_d.get("divida", 400_000)), min_value=0.0)
        if st.button("Salvar Cenário"):
            with st.spinner("Salvando..."):
                save_data(
                    st.session_state.group,
                    "dre",
                    {"idx_nome": idx_nome, "idx_valor": idx_val, "spread": spread,
                     "receita": rec, "custos": cus, "divida": div},
                )
            st.toast("Cenário salvo!", icon="✅")
            st.rerun()

    with c2:
        ebitda = calc_ebitda(rec, cus)
        sim = st.slider(f"Simular {idx_nome} %", 0.0, 30.0, idx_val)
        lucro_sim = ebitda - (div * (sim + spread) / 100)
        st.metric("Lucro Líquido na Simulação", f"R$ {lucro_sim:,.2f}")
        fig = px.line(
            x=list(range(0, 31)),
            y=[ebitda - (div * (s + spread) / 100) for s in range(0, 31)],
            title="Ponto de Ruptura",
            labels={"x": f"{idx_nome} (%)", "y": "Lucro (R$)"},
        )
        fig.add_hline(y=0, line_dash="dash", line_color="#ef4444")
        st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# 7. VIABILIDADE E VALOR
# ---------------------------------------------------------------------------

elif menu == "07 VIABILIDADE E VALOR":
    st.title("Custo de Capital e Valor do Negócio")

    with st.expander("🎓 Metodologia Acadêmica"):
        st.markdown("**WACC:** Custo Médio Ponderado de Capital.", unsafe_allow_html=False)
        st.code("WACC = (E/V × Ke) + (D/V × Kd × (1 - IR))", language="text")
        st.markdown("**Gordon Growth:** Valor da Perpetuidade.")
        st.code("EV = EBITDA × (1+g) / (WACC - g)", language="text")

    t1, t2 = st.tabs(["WACC & EVA", "Valuation DCF"])
    w_d = data.get("wacc", {})

    with t1:
        c1, c2 = st.columns(2)
        with c1:
            # MELHORIA: Kd padrão vinculado à selic_ref da sidebar
            ke = st.number_input("Ke (Retorno Sócios %)", value=safe_float(w_d.get("ke", 15.0)), min_value=0.0)
            kd = st.number_input(
                "Kd (Custo Bancos %)",
                value=safe_float(w_d.get("kd", selic_ref)),
                min_value=0.0,
                help=f"Sugestão: Selic de trabalho ({selic_ref}%) + spread bancário do módulo 06.",
            )
            eq_pct = st.slider("Equity Ratio %", 0, 100, int(safe_float(w_d.get("eq_ratio", 60))))
            eq = eq_pct / 100
            w_calc = calc_wacc(ke, kd, eq)
            st.metric("WACC Final", f"{w_calc * 100:.2f}%")
        with c2:
            roi = st.number_input("ROI Operacional %", value=safe_float(w_d.get("roi", 18.0)), min_value=0.0)
            eva = calc_eva(roi, w_calc * 100)
            delta_color = "normal" if eva >= 0 else "inverse"
            st.metric("EVA (Criação de Valor)", f"{eva:.2f}%", delta=f"{eva:.2f}%", delta_color=delta_color)
            if st.button("Salvar Financeiro"):
                with st.spinner("Salvando..."):
                    save_data(
                        st.session_state.group,
                        "wacc",
                        {"ke": ke, "kd": kd, "eq_ratio": eq_pct, "roi": roi, "wacc_final": w_calc * 100},
                    )
                st.toast("Dados financeiros salvos!", icon="✅")

    with t2:
        g = st.slider(
            "Taxa Crescimento Perpetuidade (g) %",
            0.0, 10.0,
            safe_float(w_d.get("g_growth", 3.0)),
        )
        if st.button("Sincronizar g"):
            with st.spinner("Salvando..."):
                save_data(st.session_state.group, "wacc", {**w_d, "g_growth": g})
            st.toast("Taxa g sincronizada!", icon="✅")

        ebit_v = calc_ebitda(
            safe_float(data.get("dre", {}).get("receita")),
            safe_float(data.get("dre", {}).get("custos")),
        )
        w_base = safe_float(w_d.get("wacc_final")) / 100
        g_v = g / 100

        ev = calc_enterprise_value(ebit_v, w_base, g_v)
        if ev is not None:
            st.metric("Enterprise Value", f"R$ {ev:,.2f}")
        else:
            st.error("Erro: WACC deve ser maior que g para aplicar o modelo de Gordon.")


# ---------------------------------------------------------------------------
# 8. RELATÓRIO FINAL
# ---------------------------------------------------------------------------

elif menu == "08 RELATÓRIO FINAL":
    st.title("Executive Summary Report")
    info = data.get("company_info", {})
    grupo = sanitize(st.session_state.group)
    cliente = sanitize(info.get("nome", "N/A"))
    st.write(f"Unidade: {grupo} | Cliente: {cliente}")
    st.divider()

    # Resumo dos módulos preenchidos
    missing = check_completeness(data)
    if missing:
        st.warning("Módulos incompletos: " + ", ".join(missing))
    else:
        st.success("Todos os módulos obrigatórios foram preenchidos.")

    st.subheader("Resumo Executivo")
    dre_d = data.get("dre", {})
    w_d = data.get("wacc", {})
    receita = safe_float(dre_d.get("receita"))
    custos = safe_float(dre_d.get("custos"))
    ebitda = calc_ebitda(receita, custos)
    roi = safe_float(w_d.get("roi"))
    wacc_final = safe_float(w_d.get("wacc_final"))
    eva = calc_eva(roi, wacc_final)

    col1, col2, col3 = st.columns(3)
    col1.metric("EBITDA", f"R$ {ebitda:,.2f}")
    col2.metric("WACC", f"{wacc_final:.2f}%")
    col3.metric("EVA", f"{eva:.2f}%")

    sw = data.get("swot", {})
    if any(sw.values()):
        st.subheader("Matriz SWOT")
        sc1, sc2 = st.columns(2)
        sc1.markdown(f"**Forças**\n\n{sw.get('f', '—')}")
        sc2.markdown(f"**Fraquezas**\n\n{sw.get('fra', '—')}")
        sc1.markdown(f"**Oportunidades**\n\n{sw.get('o', '—')}")
        sc2.markdown(f"**Ameaças**\n\n{sw.get('a', '—')}")

    st.divider()
    st.info("💡 Para exportar este relatório como PDF, use **Ctrl+P** no seu navegador e selecione 'Salvar como PDF'.")
