import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from supabase import create_client, Client

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="EcoStrategy Hub - Edição Acadêmica", layout="wide", initial_sidebar_state="expanded")

# --- CSS WHITELABEL & DESIGN ACADÊMICO ---
st.markdown("""
    <style>
    .stAppDeployButton {display:none !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #f0f2f6; border-right: 1px solid #e0e0e0; min-width: 300px !important; }
    h1, h2, h3 { color: #002e5d; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
    .risk-card { padding: 20px; border-radius: 12px; text-align: center; color: white; font-weight: bold; margin-bottom: 10px; border: 1px solid rgba(0,0,0,0.1); box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .insight-box { background-color: #ffffff; padding: 20px; border-left: 6px solid #0052cc; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 25px; }
    .swot-card { padding: 15px; border-radius: 8px; height: 120px; color: white; font-size: 0.85em; overflow-y: auto; margin-bottom: 10px; }
    .stButton>button { background-color: #0052cc; color: white; border-radius: 6px; width: 100%; font-weight: bold; height: 45px; border: none; }
    .formula-text { font-family: 'Courier New', Courier, monospace; background-color: #f4f4f4; padding: 5px; border-radius: 3px; font-size: 0.9em; }
    .guide-text { font-size: 0.95em; color: #444; line-height: 1.6; background: #f9f9f9; padding: 15px; border-radius: 5px; border: 1px solid #ddd; margin-bottom: 15px;}
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO SUPABASE ---
try:
    URL: str = st.secrets["SUPABASE_URL"]
    KEY: str = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(URL, KEY)
except:
    st.error("Erro Crítico: Chaves do Supabase não configuradas.")
    st.stop()

# --- FUNÇÕES DE SEGURANÇA E CÁLCULO ---
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
            for col in ['porter', 'dre', 'wacc', 'swot', 'participants', 'company_info']:
                row[col] = safe_json(row.get(col))
            return row
        return {'group_id': gid, 'porter': {}, 'dre': {}, 'wacc': {}, 'swot': {}, 'hhi': '0', 'diary': '', 'participants': {}, 'company_info': {}}
    except: return {}

# --- LOGIN ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🏛️ EcoStrategy Hub")
    st.subheader("Plataforma Acadêmica de Consultoria")
    col_l1, col_l2 = st.columns([1, 2])
    with col_l1:
        group = st.selectbox("Selecione seu Grupo", ["Grupo 1", "Grupo 2", "Grupo 3"])
        if st.text_input("Senha", type="password") == "eco123" and st.button("Acessar Dashboard"):
            st.session_state.auth, st.session_state.group = True, group
            st.rerun()
    st.stop()

data = load_data(st.session_state.group)

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"📊 {st.session_state.group}")
    st.header("⚙️ Variáveis de Referência")
    selic_ref = st.number_input("Selic de Referência (%)", value=10.75, step=0.25, help="Taxa básica usada para o custo de oportunidade.")
    st.divider()
    menu = st.radio("ETAPAS DA CONSULTORIA", [
        "1. Dashboard Executivo", 
        "2. Equipe e Empresa", 
        "3. Diário de Campo", 
        "4. Módulo Micro (Estratégia)", 
        "5. Módulo Macro (Monetário)", 
        "6. Módulo Financeiro & Valor", 
        "7. Relatório Consolidado"
    ])
    st.divider()
    if st.button("Logout"):
        st.session_state.auth = False
        st.rerun()

# --- 1. DASHBOARD EXECUTIVO ---
if menu == "1. Dashboard Executivo":
    st.title("📈 Painel Geral de Inteligência")
    info = data.get('company_info', {})
    st.markdown(f'<div class="insight-box"><h4>Consultoria Acadêmica: {info.get("nome", "Empresa X")}</h4><p>Diagnóstico em tempo real baseado nos indicadores inseridos pela equipe.</p></div>', unsafe_allow_html=True)
    
    # Cálculos Inteligentes
    dre_d = data.get('dre', {})
    ebitda = safe_float(dre_d.get('receita')) - safe_float(dre_d.get('custos'))
    divida = safe_float(dre_d.get('divida'))
    idx_total = safe_float(dre_d.get('idx_valor')) + safe_float(dre_d.get('spread'))
    break_even = (ebitda / divida * 100) if divida > 0 else 0

    hhi_str = data.get('hhi', '0')
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
        st.markdown(f'<div class="risk-card" style="background:{c}">RISCO CRÉDITO<br>Taxa Atual: {idx_total:.2f}%</div>', unsafe_allow_html=True)
    with col2:
        mc = "#28a745" if hhi_val < 1500 else "#ffc107" if hhi_val < 2500 else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{mc}">RISCO MERCADO<br>HHI: {int(hhi_val)}</div>', unsafe_allow_html=True)
    with col3:
        vc = "#28a745" if roi > w_final else "#dc3545"
        st.markdown(f'<div class="risk-card" style="background:{vc}">CRIAÇÃO VALOR<br>ROI: {roi}%</div>', unsafe_allow_html=True)

    st.divider()
    cola, colb = st.columns(2)
    with cola:
        st.subheader("💎 Valuation do Negócio")
        if (w_final/100) > g_val:
            val_est = (ebitda * (1 + g_val)) / ((w_final/100) - g_val)
            st.metric("Enterprise Value Estimado", f"R$ {val_est:,.2f}")
        else: st.warning("Aguardando cálculos WACC > Growth.")
    with colb:
        st.subheader("🎓 Resumo da Equipe")
        part = data.get('participants', {})
        st.write(f"**Líder:** {part.get('aluno1', '-')}")
        st.write(f"**Professor:** {part.get('professor', '-')}")

# --- 2. IDENTIFICAÇÃO E EMPRESA ---
elif menu == "2. Equipe e Empresa":
    st.title("👥 Identificação Acadêmica e Perfil Corporativo")
    
    t1, t2 = st.tabs(["Equipe de Consultores", "Perfil da Empresa"])
    
    with t1:
        st.markdown('<div class="guide-text"><b>Orientação:</b> Insira o nome completo de todos os membros do grupo e do professor responsável pela disciplina.</div>', unsafe_allow_html=True)
        part = data.get('participants', {})
        with st.form("f_equipe"):
            c1, c2 = st.columns(2)
            al1 = c1.text_input("Consultor 1 (Líder)", value=part.get('aluno1', ''))
            al2 = c1.text_input("Consultor 2", value=part.get('aluno2', ''))
            al3 = c1.text_input("Consultor 3", value=part.get('aluno3', ''))
            al4 = c2.text_input("Consultor 4", value=part.get('aluno4', ''))
            al5 = c2.text_input("Consultor 5", value=part.get('aluno5', ''))
            prof = c2.text_input("Professor Responsável", value=part.get('professor', ''))
            if st.form_submit_button("Salvar Equipe"):
                save_data(st.session_state.group, "participants", {"aluno1":al1, "aluno2":al2, "aluno3":al3, "aluno4":al4, "aluno5":al5, "professor":prof})
                st.success("Equipe Salva!")

    with t2:
        st.markdown('<div class="guide-text"><b>Orientação:</b> Caracterize a empresa em análise para contextualizar os diagnósticos econômicos subsequentes.</div>', unsafe_allow_html=True)
        info = data.get('company_info', {})
        with st.form("f_empresa"):
            c1, c2 = st.columns(2)
            nome = c1.text_input("Nome Fantasia / Razão Social", value=info.get('nome', ''))
            setor = c1.selectbox("Setor de Atuação", ["Varejo", "Indústria", "Serviços", "Agronegócio", "Tecnologia"], index=0)
            fundacao = c1.text_input("Ano de Fundação", value=info.get('fundacao', ''))
            colaboradores = c2.number_input("Número de Colaboradores", value=int(safe_float(info.get('colaboradores', 0))))
            produto = c2.text_input("Principal Produto/Serviço", value=info.get('produto', ''))
            desc = c2.text_area("Breve Descrição do Modelo de Negócio", value=info.get('desc', ''))
            if st.form_submit_button("Salvar Perfil Corporativo"):
                save_data(st.session_state.group, "company_info", {"nome":nome, "setor":setor, "fundacao":fundacao, "colaboradores":colaboradores, "produto":produto, "desc":desc})
                st.success("Perfil Salvo!")

# --- 3. DIÁRIO DE CAMPO ---
elif menu == "3. Diário de Campo":
    st.title("📔 Diário de Campo e Observações")
    st.markdown('<div class="guide-text"><b>Instrução:</b> Registre aqui o histórico de visitas, atas de reuniões e observações qualitativas coletadas "in loco". Este campo é vital para a fundamentação do relatório final.</div>', unsafe_allow_html=True)
    notas = st.text_area("Registro das Atividades", value=data.get('diary', ''), height=450)
    if st.button("Salvar Diário"):
        save_data(st.session_state.group, "diary", notas)
        st.success("Notas de campo sincronizadas!")

# --- 4. MÓDULO MICRO ---
elif menu == "4. Módulo Micro (Porter/HHI/SWOT)":
    st.title("🔬 Análise Microeconômica")
    
    t1, t2, t3 = st.tabs(["5 Forças de Porter", "Concentração (HHI) Guiada", "Matriz SWOT"])
    
    with t1:
        st.markdown('<div class="guide-text"><b>Guia:</b> Avalie de 1 (Muito Baixo) a 5 (Muito Alto) a intensidade de cada força competitiva proposta por Michael Porter.</div>', unsafe_allow_html=True)
        p = data.get('porter', {})
        c1, c2 = st.columns(2)
        p1 = c1.slider("Ameaça de Novos Entrantes", 1, 5, int(p.get('p1', 3)))
        p2 = c1.slider("Poder dos Fornecedores", 1, 5, int(p.get('p2', 3)))
        p3 = c1.slider("Poder dos Clientes", 1, 5, int(p.get('p3', 3)))
        p4 = c2.slider("Ameaça de Substitutos", 1, 5, int(p.get('p4', 3)))
        p5 = c2.slider("Rivalidade entre Concorrentes", 1, 5, int(p.get('p5', 3)))
        if st.button("Salvar Matriz Porter"):
            save_data(st.session_state.group, "porter", {"p1":p1,"p2":p2,"p3":p3,"p4":p4,"p5":p5})
            st.success("Porter Salvo!")

    with t2:
        st.markdown('<div class="guide-text"><b>Guia HHI:</b> Identifique a participação de mercado (%) das principais empresas do setor. Se o somatório for inferior a 100%, o sistema considerará o restante como "Outros Concorrentes".</div>', unsafe_allow_html=True)
        
        col_h1, col_h2 = st.columns([1, 1.5])
        with col_h1:
            st.subheader("Estrutura do Mercado")
            s1 = st.number_input("Share da Empresa Líder (%)", 0.0, 100.0, 30.0)
            s2 = st.number_input("Share do 2º Concorrente (%)", 0.0, 100.0, 20.0)
            s3 = st.number_input("Share do 3º Concorrente (%)", 0.0, 100.0, 10.0)
            s4 = st.number_input("Share do 4º Concorrente (%)", 0.0, 100.0, 5.0)
            restante = max(0.0, 100.0 - (s1+s2+s3+s4))
            st.write(f"Concorrência Atomizada (Outros): {restante}%")
            
            shares_str = f"{s1},{s2},{s3},{s4},{restante}"
            if st.button("Calcular e Salvar HHI"):
                save_data(st.session_state.group, "hhi", shares_str)
                st.success("HHI Sincronizado!")

        with col_h2:
            hhi_calc = sum([x**2 for x in [s1, s2, s3, s4, restante]])
            st.metric("HHI Final", int(hhi_calc))
            st.plotly_chart(px.pie(values=[s1, s2, s3, s4, restante], names=["Líder", "2º", "3º", "4º", "Outros"], hole=0.4))
            
            with st.expander("🎓 Interpretação Acadêmica"):
                if hhi_calc < 1500: st.success("Mercado Altamente Competitivo.")
                elif hhi_calc < 2500: st.warning("Mercado com Concentração Moderada.")
                else: st.error("Mercado Altamente Concentrado (Oligopólio).")

    with t3:
        sw = data.get('swot', {})
        st.markdown('<div class="guide-text"><b>Guia SWOT:</b> Mapeie o cenário estratégico cruzando variáveis internas e externas.</div>', unsafe_allow_html=True)
        with st.form("f_swot"):
            c1, c2 = st.columns(2)
            f = c1.text_area("Forças (Interno)", value=sw.get('f', ''))
            o = c1.text_area("Oportunidades (Externo)", value=sw.get('o', ''))
            fra = c2.text_area("Fraquezas (Interno)", value=sw.get('fra', ''))
            a = c2.text_area("Ameaças (Externo)", value=sw.get('a', ''))
            if st.form_submit_button("Sincronizar SWOT"):
                save_data(st.session_state.group, "swot", {"f":f, "fra":fra, "o":o, "a":a})
                st.rerun()

# --- 5. MONETÁRIO ---
elif menu == "5. Módulo Macro (Monetário)":
    st.title("🏦 Diagnóstico Monetário")
    st.markdown('<div class="guide-text"><b>Guia:</b> Estabeleça a estrutura de endividamento. Defina o indexador (ex: Selic, IPCA) e o spread bancário acordado.</div>', unsafe_allow_html=True)
    
    dre_d = data.get('dre', {})
    c1, c2 = st.columns([1, 1.5])
    with c1:
        idx_nome = st.selectbox("Indexador da Dívida", ["Selic", "TJLP", "IGP-M", "IPCA", "Outro"], index=0)
        idx_val = st.number_input(f"Taxa atual do {idx_nome} (%)", value=safe_float(dre_d.get('idx_valor', 10.75)))
        spread = st.number_input("Spread Bancário (+%)", value=safe_float(dre_d.get('spread', 2.0)))
        rec = st.number_input("Receita Bruta Anual (R$)", value=safe_float(dre_d.get('receita', 1000000)))
        cus = st.number_input("Custos Totais (R$)", value=safe_float(dre_d.get('custos', 700000)))
        div = st.number_input("Dívida Total (R$)", value=safe_float(dre_d.get('divida', 400000)))
        if st.button("Salvar Cenário Macro"):
            save_data(st.session_state.group, "dre", {"idx_nome":idx_nome, "idx_valor":idx_val, "spread":spread, "receita":rec, "custos":cus, "divida":div})
            st.rerun()
    with c2:
        ebitda = rec - cus
        sim = st.slider(f"Simular {idx_nome} (%)", 0.0, 30.0, idx_val)
        lucro_est = ebitda - (div * (sim + spread) / 100)
        st.metric("Lucro Líquido Estimado (Simulação)", f"R$ {lucro_est:,.2f}")
        fig = px.line(x=list(range(0,31)), y=[ebitda - (div * (s + spread) / 100) for s in range(0,31)], title="Ponto de Ruptura do Negócio")
        fig.add_hline(y=0, line_dash="dash", line_color="red", annotation_text="Prejuízo")
        st.plotly_chart(fig)

# --- 6. FINANCEIRO ---
elif menu == "6. Módulo Financeiro & Valor":
    st.title("💰 Custo de Capital e Valuation")
    
    t1, t2 = st.tabs(["WACC & EVA", "Avaliação de Perpetuidade"])
    with t1:
        st.markdown('<div class="guide-text"><b>Guia:</b> Calcule o Custo Médio Ponderado de Capital (WACC). Use o ROI para verificar se a empresa está criando valor econômico real (EVA).</div>', unsafe_allow_html=True)
        w_d = data.get('wacc', {})
        c1, c2 = st.columns(2)
        with c1:
            ke = st.number_input("Ke (Custo Cap. Próprio %)", value=safe_float(w_d.get('ke', 15)))
            kd = st.number_input("Kd (Custo Cap. Terceiros %)", value=safe_float(w_d.get('kd', 12)))
            eq = st.slider("Equity Ratio (%)", 0, 100, int(safe_float(w_d.get('eq_ratio', 60)))) / 100
            w_calc = (eq * (ke/100)) + ((1 - eq) * (kd/100) * 0.66)
            st.metric("WACC Final", f"{w_calc*100:.2f}%")
        with c2:
            roi = st.number_input("ROI da Empresa (%)", value=safe_float(w_d.get('roi', 18)))
            eva = roi - (selic_ref + 5.0)
            st.metric("Criação de Valor (EVA)", f"{eva:.2f}%")
            if st.button("Salvar Dados Financeiros"):
                save_data(st.session_state.group, "wacc", {"ke":ke, "kd":kd, "eq_ratio":eq*100, "roi":roi, "wacc_final":w_calc*100})

    with t2:
        st.subheader("Estimativa de Valor (DCF Perpetuidade)")
        g = st.slider("Taxa de Crescimento Esperada (g) %", 0.0, 10.0, safe_float(w_d.get('g_growth', 3.0)))
        if st.button("Sincronizar Crescimento (g)"):
            save_data(st.session_state.group, "wacc", {**w_d, "g_growth": g})
            st.rerun()
        
        ebit_base = safe_float(data.get('dre', {}).get('receita')) - safe_float(data.get('dre', {}).get('custos'))
        w_base = safe_float(w_d.get('wacc_final')) / 100
        g_base = g / 100
        if w_base > g_base:
            val = (ebit_base * (1 + g_base)) / (w_base - g_base)
            st.metric("Enterprise Value", f"R$ {val:,.2f}")
        else: st.error("O WACC deve ser superior ao Crescimento (g).")

# --- 7. RELATÓRIO ---
elif menu == "7. Relatório Consolidado":
    st.title("📄 Relatório Final de Consultoria")
    st.divider()
    info = data.get('company_info', {})
    part = data.get('participants', {})
    
    st.header(f"Projeto: {info.get('nome', 'N/A')}")
    st.subheader(f"Professor Orientador: {part.get('professor', 'N/A')}")
    st.write(f"**Equipe:** {part.get('aluno1')}, {part.get('aluno2')}, {part.get('aluno3')}, {part.get('aluno4')}, {part.get('aluno5')}")
    
    st.divider()
    st.subheader("Sumário do Diário de Campo")
    st.info(data.get('diary', 'Nenhum registro encontrado.'))
    st.button("Visualizar para Impressão (Ctrl+P)")
