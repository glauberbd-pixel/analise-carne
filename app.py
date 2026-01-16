import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO VISUAL PREMIUM (DARK MODE)
st.set_page_config(page_title="Inteligência de Grelhados", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0c0c0c; color: #e0e0e0; }
    div[data-testid="stMetricValue"] { color: #d4af37 !important; font-size: 28px !important; }
    label { color: #d4af37 !important; font-weight: bold; }
    h1, h2, h3 { color: #d4af37 !important; }
    .stButton>button { width: 100%; border-radius: 5px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥩 Inteligência de Grelhados")

# 2. CONEXÃO COM A PLANILHA
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. BARRA LATERAL: LANÇAMENTO E GESTÃO
with st.sidebar:
    st.header("📋 Lançamento")
    with st.form("form_carne", clear_on_submit=True):
        corte = st.text_input("Nome do Corte").strip()
        preco_kg = st.number_input("Preço KG (R$)", min_value=0.0, format="%.2f")
        peso_gondola = st.number_input("Peso Gôndola (g)", min_value=0.0)
        peso_grelhado = st.number_input("Peso Grelhado (g)", min_value=0.0)
        submit = st.form_submit_button("CALCULAR E SALVAR")
    
    st.markdown("---")
    # Botão para limpar todos os registros da planilha
    if st.button("🗑️ Limpar Planilha"):
        # Cabeçalhos exatos conforme image_3ead46.png
        colunas = ["Corte", "Preco_KG", "Peso_Gondola", "Peso_Grelhado", "# Dif_Peso", 
                   "% Perda_Perc", "Preco_G_Gondola", "Preco_G_Grelhado", "Dif_Preco_G", "% Aumento_Perc"]
        df_reset = pd.DataFrame(columns=colunas)
        conn.update(data=df_reset)
        st.sidebar.success("Planilha zerada com sucesso!")
        st.rerun()

# 4. LÓGICA DE CÁLCULOS E PERSISTÊNCIA
if submit and corte:
    # Cálculo de pesos
    dif_peso = peso_gondola - peso_grelhado
    perda_perc = (dif_peso / peso_gondola) * 100 if peso_gondola > 0 else 0
    
    # Cálculo de preços (Preço por grama)
    p_g_gondola = preco_kg / 1000
    # O preço real do grelhado considera o custo total dividido pelo que restou
    custo_total_carne = p_g_gondola * peso_gondola
    p_g_grelhado = custo_total_carne / peso_grelhado if peso_grelhado > 0 else 0
    
    dif_preco_g = p_g_grelhado - p_g_gondola
    aumento_perc = (dif_preco_g / p_g_gondola) * 100 if p_g_gondola > 0 else 0

    # Lendo dados atuais
    df_atual = conn.read(ttl=0)
    
    # Mapeamento idêntico aos cabeçalhos da image_3ead46.png
    nova_linha = {
        "Corte": corte,
        "Preco_KG": preco_kg,
        "Peso_Gondola": peso_gondola,
        "Peso_Grelhado": peso_grelhado,
        "# Dif_Peso": round(dif_peso, 2),
        "% Perda_Perc": round(perda_perc, 2),
        "Preco_G_Gondola": round(p_g_gondola, 4),
        "Preco_G_Grelhado": round(p_g_grelhado, 4),
        "Dif_Preco_G": round(dif_preco_g, 4),
        "% Aumento_Perc": round(aumento_perc, 2)
    }

    # Atualiza se o corte já existir, senão adiciona novo
    if not df_atual.empty and corte in df_atual['Corte'].values:
        idx = df_atual.index[df_atual['Corte'] == corte].tolist()[0]
        for col, val in nova_linha.items():
            df_atual.at[idx, col] = val
        st.info(f"Dados de '{corte}' atualizados!")
    else:
        df_atual = pd.concat([df_atual, pd.DataFrame([nova_linha])], ignore_index=True)
        st.success(f"'{corte}' adicionado ao ranking!")

    conn.update(data=df_atual)

# 5. EXIBIÇÃO DE RESULTADOS E RANKING
try:
    df_db = conn.read(ttl=0)
    if not df_db.empty:
        # Ordenação por custo-benefício (menor preço grelhado primeiro)
        ranking = df_db.sort_values(by="Preco_G_Grelhado", ascending=True)
        
        # Métricas de destaque
        campeao = ranking.iloc[0]
        c1, c2, c3 = st.columns(3)
        c1.metric("Corte mais Econômico", campeao['Corte'])
        c2.metric("Preço Real (g)", f"R$ {campeao['Preco
