import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# CONFIGURAÇÃO VISUAL PREMIUM
st.set_page_config(page_title="Gestão de Grelhados | Premium", layout="wide")

# CSS para Dark Mode e Detalhes Dourados (Padrão Holding)
st.markdown("""
    <style>
    .main { background-color: #0c0c0c; color: #e0e0e0; }
    div[data-testid="stMetricValue"] { color: #d4af37 !important; font-size: 28px !important; }
    label { color: #d4af37 !important; font-weight: bold; font-size: 16px; }
    .stButton>button { background-color: #d4af37; color: black; font-weight: bold; border-radius: 5px; width: 100%; }
    .stDataFrame { background-color: #1a1a1a; border-radius: 10px; }
    h1, h2, h3 { color: #d4af37 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥩 Inteligência de Grelhados")
st.markdown("---")

# Conexão com a planilha "Analise carne"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ENTRADA DE DADOS NA LATERAL ---
with st.sidebar:
    st.header("📋 Lançamento")
    with st.form("form_carne", clear_on_submit=True):
        corte = st.text_input("Nome do Corte (ex: Picanha)").strip()
        preco_kg = st.number_input("Preço do KG (R$)", min_value=0.0, format="%.2f")
        peso_gondola = st.number_input("Peso Gôndola (g)", min_value=0.0)
        peso_grelhado = st.number_input("Peso Grelhado (g)", min_value=0.0)
        submit = st.form_submit_button("CALCULAR E SALVAR")

if submit and corte:
    # --- CÁLCULOS MATEMÁTICOS ---
    dif_peso = peso_gondola - peso_grelhado
    perda_perc = (dif_peso / peso_gondola) if peso_gondola > 0 else 0
    p_g_gondola = preco_kg / 1000
    custo_total = p_g_gondola * peso_gondola
    p_g_grelhado = custo_total / peso_grelhado if peso_grelhado > 0 else 0
    dif_preco_g = p_g_grelhado - p_g_gondola
    aumento_perc = (dif_preco_g / p_g_gondola) if p_g_gondola > 0 else 0

    # Lendo dados atuais
    df_atual = conn.read(ttl=0)
    
    nova_linha = {
        "Corte": corte,
        "Preco_KG": preco_kg,
        "Peso_Gondola": peso_gondola,
        "Peso_Grelhado": peso_grelhado,
        "# Dif_Peso": round(dif_peso, 2),
        "% Perda_Perc": round(perda_perc * 100, 2),
        "Preco_G_Gondola": round(p_g_gondola, 4),
        "Preco_G_Grelhado": round(p_g_grelhado, 4),
        "Dif_Preco_G": round(dif_preco_g, 4),
        "% Aumento_Perc": round(aumento_perc * 100, 2)
    }

    # Lógica para evitar duplicidade de corte
    if not df_atual.empty and corte in df_atual['Corte'].values:
        idx = df_atual.index[df_atual['Corte'] == corte].tolist()[0]
        for col, val in nova_linha.items():
            df_atual.at[idx, col] = val
        st.info(f"Dados de '{corte}' atualizados com sucesso!")
    else:
        df_atual = pd.concat([df_atual, pd.DataFrame([nova_linha])], ignore_index=True)
        st.success(f"'{corte}' adicionado ao ranking!")

    # Envia para o Google Sheets
    conn.update(data=df_atual)

# --- RANKING E INDICADORES ---
try:
    df_db = conn.read(ttl=0)
    if not df_db.empty:
        # Ordenar pelo menor preço por grama grelhado (Melhor Custo-Benefício)
        ranking = df_db.sort_values(by="Preco_G_Grelhado", ascending=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Melhor Escolha", ranking.iloc[0]['Corte'])
        with col2:
            st.metric("Menor Preço/g Grelhado", f"R$ {ranking.iloc[0]['Preco_G_Grelhado']:.4f}")
        with col3:
            st.metric("Menor Perda", f"{ranking.sort_values(by='% Perda_Perc').iloc[0]['% Perda_Perc']}%")

        st.subheader("🏆 Ranking Geral de Custo-Benefício")
        st.dataframe(ranking, use_container_width=True)
except:
    st.info("Aguardando o primeiro lançamento para gerar o ranking.")
