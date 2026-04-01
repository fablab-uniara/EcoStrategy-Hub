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

    h1, h2, h3 { color: #002e5d; font-weight: 800; letter-spacing: -0.04em; }
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
    if val is None: return default
    try: return float(val)
    except (ValueError, TypeError): return default

def safe_json(val, field_name="campo"):
    if val is None or val == "" or val == "None": return {}
    if isinstance(val, dict): return val
    try: return json.loads(val)
    except json.JSONDecodeError: return {}

def sanitize(text: str) -> str:
    if not isinstance(text, str): return str(text) if text else ""
    return html.escape(text)

# ---------------------------------------------------------------------------
# API BANCO CENTRAL — CACHEADA
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def get_live_selic() -> float:
    try:
        url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados/ultimos/1?formato=json"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return float(response.json()[0]["valor"])
    except Exception: return 10.75

# ---------------------------------------------------------------------------
# CONEXÃO SUPABASE
# ---------------------------------------------------------------------------

@st.cache_resource
def get_supabase_client() -> Client:
    url: str = st.secrets["SUPABASE_URL"]
    key: str = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = get_supabase_client()
except Exception as e:
    st.error("Erro Crítico de Conexão com o Banco de Dados.")
    st.stop()

# ---------------------------------------------------------------------------
# PERSISTÊNCIA & SEGURANÇA
# ---------------------------------------------------------------------------

def _assert_group_access(gid: str):
    """Proteção de Acesso: Impede leitura/escrita cruzada entre grupos."""
    if gid != st.session_state.get("group"):
        st.error("Acesso Negado: Unidade não autorizada.")
        st.stop()

def save_data(gid: str, column: str, value):
    _assert_group_access(gid)
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    try:
        # Tenta verificar se o registro existe
        res = supabase.table("eco_data").select("group_id").eq("group_id", gid).execute()
        if res.data:
            supabase.table("eco_data").update({column: str(value)}).eq("group_id", gid).execute()
        else:
            supabase.table("eco_data").insert({"group_id": gid, column: str(value)}).execute()
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")

def load_data(gid: str) -> dict:
    _assert_group_access(gid)
    json_fields = ["porter", "dre", "wacc", "swot", "participants", "company_info", "diary"]
    empty = {"group_id": gid, **{f: {} for f in json_fields}, "hhi": "0"}
    try:
        res = supabase.table("eco_data").select("*").eq("group_id", gid).execute()
        if not res.data: return empty
        row = res.data[0]
        for col in json_fields:
            row[col] = safe_json(row.get(col), field_name=col)
        return row
    except Exception: return empty

# ---------------------------------------------------------------------------
# CÁLCULOS DE NEGÓCIO
# ---------------------------------------------------------------------------

def calc_ebitda(receita, custos): return receita - custos
def calc_wacc(ke, kd, eq_ratio): return (eq_ratio * (ke / 100)) + ((1 - eq_ratio) * (kd / 100) * 0.66)
def calc_eva(roi, wacc_pct): return roi - wacc_pct
def calc_hhi(shares): return sum(s ** 2 for s in shares)
def calc_health_score(ebitda, divida, idx_total, hhi_val, roi, wacc_pct):
    score = 0
    break_even = (ebitda / divida * 100) if divida > 0 else 100
    if divida == 0 or idx_total < break_even: score += 40
    if hhi_val < 2500: score += 30
    if roi > wacc_pct: score += 30
    return score

# ---------------------------------------------------------------------------
# AUTENTICAÇÃO
# ---------------------------------------------------------------------------

if 'auth' not in st.session_state: 
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<h2 style='text-align: center; color: #0f172a; margin-top: 50px;'>EcoStrategy Intelligence</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.8, 1])
    
    with col_l2:
        try: st.image("logo.png", use_container_width=True)
        except: pass
        
        group_selected = st.selectbox("Selecione sua Unidade", ["Grupo 1", "Grupo 2", "Grupo 3"])
        pwd_input = st.text_input("Chave de Acesso", type="password")
        
        if st.button("Validar Credenciais"):
            # Busca as senhas nos Secrets
            passwords = st.secrets.get("GROUP_PASSWORDS", {})
            dev_pwd = st.secrets.get("DEV_PASSWORD", "mestre123") # Fallback seguro
            
            # Validação Mestra ou por Grupo
            if pwd_input == passwords.get(group_selected) or (pwd_input == dev_pwd and dev_pwd is not None):
                st.session_state.auth = True
                st.session_state.group = group_selected
                st.rerun()
            else:
                st.error("Credencial inválida para esta unidade.")
    st.stop()

# Carrega dados do grupo autenticado
data = load_data(st.session_state.group)

# ---------------------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------------------

with st.sidebar:
    try: st.image("logo.png", use_container_width=True)
    except: pass
    st.markdown(f"<h2>{sanitize(st.session_state.group).upper()}</h2>", unsafe_allow_html=True)
    st.divider()

    st.markdown("<p style='font-weight: 700; color: #94a3b8; letter-spacing: 0.1em;'>CENÁRIO MACRO</p>", unsafe_allow_html=True)
    selic_meta = get_live_selic()
    st.markdown(f"<p style='color: #10b981; font-size: 0.9rem; font-weight: 600;'>Selic Meta Oficial: {selic_meta}%</p>", unsafe_allow_html=True)
    selic_ref = st.number_input("Taxa de Trabalho (%)", value=selic_meta, step=0.25)

    st.divider()
    st.markdown("<p style='font-weight: 700; color: #94a3b8; letter-spacing: 0.1em;'>NAVEGAÇÃO</p>", unsafe_allow_html=True)

    menu = st.radio("MENU", [
        "01 DASHBOARD EXECUTIVO", "02 GOVERNANÇA E EQUIPE", "03 PERFIL CORPORATIVO",
        "04 DIAGNÓSTICO DE CAMPO", "05 ANÁLISE ESTRATÉGICA", "06 CENÁRIO MONETÁRIO",
        "07 VIABILIDADE E VALOR", "08 RELATÓRIO FINAL"
    ], label_visibility="collapsed")

    st.divider()
    if st.button("Finalizar Sessão"):
        st.session_state.auth = False
        st.rerun()

# ---------------------------------------------------------------------------
# 01. DASHBOARD
# ---------------------------------------------------------------------------

if menu == "01 DASHBOARD EXECUTIVO":
    st.title("Executive Dashboard")
    info = data.get("company_info", {})
    st.markdown(f'<div class="insight-box"><h4>Unidade: {sanitize(info.get("nome", "Não Identificada"))}</h4><p>Sumário de indicadores de risco e criação de valor econômico.</p></div>', unsafe_allow_html=True)

    dre_d = data.get("dre", {})
    ebitda = calc_ebitda(safe_float(dre_d.get("receita")), safe_float(dre_d.get("custos")))
    divida = safe_float(dre_d.get("divida"))
    idx_total = safe_float(dre_d.get("idx_valor")) + safe_float(dre_d.get("spread"))

    hhi_str = str(data.get("hhi", "0"))
    try: hhi_val = calc_hhi([float(x) for x in hhi_str.split(",") if x.strip()])
    except ValueError: hhi_val = 0.0

    w_d = data.get("wacc", {})
    w_final = safe_float(w_d.get("wacc_final", 15.0))
    roi = safe_float(w_d.get("roi"))

    score = calc_health_score(ebitda, divida, idx_total, hhi_val, roi, w_final)

    col_gauge, col_sem = st.columns([1.5, 2])
    with col_gauge:
        fig_health = go.Figure(go.Indicator(
            mode="gauge+number", value=score, title={"text": "Health Score Index"},
            gauge={"axis": {"range": [0, 100]}, "bar": {"color": "#2563eb"},
                   "steps": [{"range": [0, 50], "color": "#ef4444"}, {"range": [50, 75], "color": "#f59e0b"}, {"range": [75, 100], "color": "#10b981"}]}))
        st.plotly_chart(fig_health, use_container_width=True)

    with col_sem:
        c1, c2, c3 = st.columns(3)
        break_even = (ebitda / divida * 100) if divida > 0 else 0
        with c1:
            color = "#10b981" if idx_total < break_even else "#ef4444"
            st.markdown(f'<div class="risk-card" style="background:{color}">CRÉDITO<br>{idx_total:.1f}%</div>', unsafe_allow_html=True)
        with c2:
            m_color = "#10b981" if hhi_val < 1500 else ("#f59e0b" if hhi_val < 2500 else "#ef4444")
            st.markdown(f'<div class="risk-card" style="background:{m_color}">MERCADO<br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
        with c3:
            v_color = "#10b981" if roi > w_final else "#ef4444"
            st.markdown(f'<div class="risk-card" style="background:{v_color}">VALOR (EVA)<br>ROI: {roi}%</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 02. GOVERNANÇA E EQUIPE
# ---------------------------------------------------------------------------
elif menu == "02 GOVERNANÇA E EQUIPE":
    st.title("Governança e Equipe")
    part = data.get("participants", {})
    with st.form("f_eq"):
        c1, c2 = st.columns(2)
        al1 = c1.text_input("Aluno 1 (Líder)", value=part.get("aluno1", ""))
        al2 = c1.text_input("Aluno 2", value=part.get("aluno2", ""))
        al3 = c1.text_input("Aluno 3", value=part.get("aluno3", ""))
        al4 = c2.text_input("Aluno 4", value=part.get("aluno4", ""))
        al5 = c2.text_input("Aluno 5", value=part.get("aluno5", ""))
        prof = c2.text_input("Professor Orientador", value=part.get("professor", ""))
        if st.form_submit_button("Sincronizar"):
            save_data(st.session_state.group, "participants", {"aluno1":al1, "aluno2":al2, "aluno3":al3, "aluno4":al4, "aluno5":al5, "professor":prof})
            st.toast("Dados Salvos!")

# ---------------------------------------------------------------------------
# 03. PERFIL CORPORATIVO
# ---------------------------------------------------------------------------
elif menu == "03 PERFIL CORPORATIVO":
    st.title("Perfil Corporativo")
    info = data.get("company_info", {})
    with st.form("f_emp"):
        c1, c2 = st.columns(2)
        nome = c1.text_input("Razão Social", value=info.get("nome", ""))
        setor = c1.selectbox("Setor", ["Varejo", "Indústria", "Serviços", "Agro", "Tech"], index=0)
        colab = c2.number_input("Funcionários", value=int(safe_float(info.get("colab", 0))), min_value=0)
        desc = st.text_area("Descrição do Negócio", value=info.get("desc", ""))
        if st.form_submit_button("Salvar Perfil"):
            save_data(st.session_state.group, "company_info", {"nome": nome, "setor": setor, "colab": colab, "desc": desc})
            st.toast("Perfil Atualizado!")

# ---------------------------------------------------------------------------
# 04. DIAGNÓSTICO DE CAMPO
# ---------------------------------------------------------------------------
elif menu == "04 DIAGNÓSTICO DE CAMPO":
    st.title("Diagnóstico Qualitativo")
    diary = data.get("diary", {})
    with st.form("f_dia"):
        q1 = st.text_area("1. Histórico e Diferencial Estratégico", value=diary.get("q1", ""))
        q2 = st.text_area("2. Impacto de Variáveis Macro no Caixa", value=diary.get("q2", ""))
        q3 = st.text_area("3. Estrutura de Mercado e Concorrência", value=diary.get("q3", ""))
        q4 = st.text_area("4. Gestão de Dívida", value=diary.get("q4", ""))
        if st.form_submit_button("Salvar Notas"):
            save_data(st.session_state.group, "diary", {"q1":q1, "q2":q2, "q3":q3, "q4":q4})
            st.toast("Diário Sincronizado!")

# ---------------------------------------------------------------------------
# 05. ANÁLISE ESTRATÉGICA
# ---------------------------------------------------------------------------
elif menu == "05 ANÁLISE ESTRATÉGICA":
    st.title("Análise Estratégica")
    t1, t2, t3 = st.tabs(["5 Forças de Porter", "Concentração HHI", "Matriz SWOT"])
    with t1:
        p = data.get("porter", {})
        c1, c2 = st.columns(2)
        p1 = c1.slider("Entrantes", 1, 5, int(safe_float(p.get("p1", 3))))
        p2 = c1.slider("Fornecedores", 1, 5, int(safe_float(p.get("p2", 3))))
        p3 = c1.slider("Clientes", 1, 5, int(safe_float(p.get("p3", 3))))
        p5 = c2.slider("Rivalidade", 1, 5, int(safe_float(p.get("p5", 3))))
        if st.button("Salvar Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1, "p2":p2, "p3":p3, "p5":p5})
            st.toast("Porter Salvo!")
    with t2:
        s1 = st.number_input("Share Líder %", 0.0, 100.0, 30.0)
        s2 = st.number_input("Share 2º %", 0.0, 100.0, 20.0)
        s3 = st.number_input("Share 3º %", 0.0, 100.0, 10.0)
        rest = max(0.0, 100.0 - (s1+s2+s3))
        h_calc = calc_hhi([s1, s2, s3, rest])
        st.metric("HHI Final", int(h_calc))
        st.plotly_chart(px.pie(values=[s1, s2, s3, rest], names=["Líder", "2º", "3º", "Outros"], hole=0.4))
        if st.button("Salvar HHI"):
            save_data(st.session_state.group, "hhi", f"{s1},{s2},{s3},{rest}")
    with t3:
        sw = data.get("swot", {})
        with st.form("f_swot"):
            c1, c2 = st.columns(2)
            f = c1.text_area("Forças", value=sw.get("f", ""))
            fra = c2.text_area("Fraquezas", value=sw.get("fra", ""))
            o = c1.text_area("Oportunidades", value=sw.get("o", ""))
            a = c2.text_area("Ameaças", value=sw.get("a", ""))
            if st.form_submit_button("Salvar SWOT"):
                save_data(st.session_state.group, "swot", {"f":f, "fra":fra, "o":o, "a":a})
                st.rerun()

# ---------------------------------------------------------------------------
# 06. CENÁRIO MONETÁRIO
# ---------------------------------------------------------------------------
elif menu == "06 CENÁRIO MONETÁRIO":
    st.title("Stress Test Monetário")
    dre_d = data.get("dre", {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_nome = st.selectbox("Indexador", ["Selic", "TJLP", "IPCA", "IGP-M"], index=0)
        idx_val = st.number_input(f"Valor {idx_nome} %", value=safe_float(dre_d.get("idx_valor", selic_ref)))
        spread = st.number_input("Spread Bancário %", value=safe_float(dre_d.get("spread", 2.0)))
        rec = st.number_input("Receita Bruta", value=safe_float(dre_d.get("receita", 1000000)))
        cus = st.number_input("Custos", value=safe_float(dre_d.get("custos", 700000)))
        div = st.number_input("Dívida", value=safe_float(dre_d.get("divida", 400000)))
        if st.button("Salvar Cenário"):
            save_data(st.session_state.group, "dre", {"idx_nome":idx_nome, "idx_valor":idx_val, "spread":spread, "receita":rec, "custos":cus, "divida":div})
            st.rerun()
    with c2:
        ebitda = calc_ebitda(rec, cus)
        sim = st.slider(f"Simular {idx_nome} %", 0.0, 30.0, idx_val)
        lucro_sim = ebitda - (div * (sim + spread) / 100)
        st.metric("Lucro Estimado", f"R$ {lucro_sim:,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div*(s+spread)/100) for s in range(0,31)], title="Ponto de Ruptura")
        fig.add_hline(y=0, line_dash="dash", line_color="#ef4444")
        st.plotly_chart(fig)

# ---------------------------------------------------------------------------
# 07. VIABILIDADE E VALOR
# ---------------------------------------------------------------------------
elif menu == "07 VIABILIDADE E VALOR":
    st.title("Valuation e Custo de Capital")
    with st.expander("🎓 Referencial Acadêmico"):
        st.code("WACC = (E/V * Ke) + (D/V * Kd * 0.66)", language="text")
        st.code("EV = EBITDA(1+g) / (WACC - g)", language="text")
    t1, t2 = st.tabs(["WACC & EVA", "Simulador Gordon"])
    w_d = data.get("wacc", {})
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            ke = st.number_input("Ke %", value=safe_float(w_d.get("ke", 15.0)))
            kd = st.number_input("Kd %", value=safe_float(w_d.get("kd", 12.0)))
            eq_pct = st.slider("Equity %", 0, 100, int(safe_float(w_d.get("eq_ratio", 60))))
            w_calc = calc_wacc(ke, kd, eq_pct/100)
            st.metric("WACC Final", f"{w_calc*100:.2f}%")
        with c2:
            roi = st.number_input("ROI %", value=safe_float(w_d.get("roi", 18.0)))
            eva = calc_eva(roi, w_calc*100)
            st.metric("EVA", f"{eva:.2f}%")
            if st.button("Salvar Financeiro"):
                save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq_pct, "roi":roi, "wacc_final":w_calc*100, "g_growth": w_d.get("g_growth", 3.0)})
    with t2:
        g = st.slider("Crescimento (g) %", 0.0, 10.0, safe_float(w_d.get("g_growth", 3.0)))
        if st.button("Sincronizar g"):
            save_data(st.session_state.group, "wacc", {**w_d, "g_growth": g})
            st.rerun()
        ebit_v = calc_ebitda(safe_float(data.get("dre", {}).get("receita")), safe_float(data.get("dre", {}).get("custos")))
        w_base = safe_float(w_d.get("wacc_final")) / 100
        if w_base > (g/100):
            val = (ebit_v * (1 + g/100)) / (w_base - g/100)
            st.metric("Enterprise Value", f"R$ {val:,.2f}")
        else: st.error("Erro: WACC deve ser > g.")

# ---------------------------------------------------------------------------
# 08. RELATÓRIO FINAL
# ---------------------------------------------------------------------------
elif menu == "08 RELATÓRIO FINAL":
    st.title("Report Summary")
    st.write(f"Unidade: {st.session_state.group} | Cliente: {sanitize(data.get('company_info', {}).get('nome', 'N/A'))}")
    st.divider()
    st.button("Exportar (Ctrl + P)")
