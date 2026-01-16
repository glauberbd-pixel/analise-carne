import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Estilo Dark Mode (Igual ao seu app da Holding)
st.set_page_config(page_title="Inteligência de Grelhados", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0c0c0c; color: #e0e0e0; }
    div[data-testid="stMetricValue"] { color: #d4af37 !important; }
    label { color: #d4af37 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥩 Inteligência de Grelhados")

# Conexão
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ENTRADA DE DADOS ---
with st.sidebar:
    st.header("Novo Cálculo")
    with st.form("meat_form", clear_on_submit=True):
        corte = st.text_input("Corte (ex: Picanha)").strip()
        p_kg = st.number_input("Preço KG (R$)", min_value=0.0)
        p_gondola = st.number_input("Peso Gôndola (g)", min_value=0.0)
        p_grelhado = st.number_input("Peso Grelhado (g)", min_value=0.0)
        submit = st.form_submit_button("SALVAR E CALCULAR")

if submit and corte:
    # Lógica Matemática
    dif_peso = p_gondola - p_grelhado
    perda_perc = (dif_peso / p_gondola) * 100 if p_gondola > 0 else 0
    p_g_gondola = p_kg / 1000
    p_g_grelhado = (p_g_gondola * p_gondola) / p_grelhado if p_grelhado > 0 else 0
    dif_preco_g = p_g_grelhado - p_g_gondola
    aumento_perc = (dif_preco_g / p_g_gondola) * 100 if p_g_gondola > 0 else 0

    # Lendo planilha atual
    df_atual = conn.read(ttl=0)
    
    nova_linha = {
        "Corte": corte,
        "Preco_KG": p_kg,
        "Peso_Gondola": p_gondola,
        "Peso_Grelhado": p_grelhado,
        "# Dif_Peso": round(dif_peso, 2),
        "% Perda_Perc": round(perda_perc, 2),
        "Preco_G_Gondola": round(p_g_gondola, 4),
        "Preco_G_Grelhado": round(p_g_grelhado, 4),
        "Dif_Preco_G": round(dif_preco_g, 4),
        "% Aumento_Perc": round(aumento_perc, 2)
    }

    # Evita duplicados e salva
    if not df_atual.empty and corte in df_atual['Corte'].values:
        idx = df_atual.index[df_atual['Corte'] == corte].tolist()[0]
        for col, val in nova_linha.items():
            df_atual.at[idx, col] = val
        st.info(f"'{corte}' atualizado!")
    else:
        df_atual = pd.concat([df_atual, pd.DataFrame([nova_linha])], ignore_index=True)
        st.success(f"'{corte}' adicionado!")

    conn.update(data=df_atual)

# --- RANKING ---
try:
    df_rank = conn.read(ttl=0)
    if not df_rank.empty:
        st.subheader("🏆 Ranking: Melhor Custo-Benefício (Grelhado)")
        ranking = df_rank.sort_values(by="Preco_G_Grelhado", ascending=True)
        st.dataframe(ranking, use_container_width=True)
except:
    st.info("Aguardando dados...")
