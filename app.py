import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO VISUAL
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

# 2. CONEXÃO
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. BARRA LATERAL
with st.sidebar:
    st.header("📋 Lançamento")
    with st.form("form_carne", clear_on_submit=True):
        corte = st.text_input("Nome do Corte").strip()
        preco_kg = st.number_input("Preço KG (R$)", min_value=0.0, format="%.2f")
        p_gondola = st.number_input("Peso Gôndola (g)", min_value=0.0)
        p_grelhado = st.number_input("Peso Grelhado (g)", min_value=0.0)
        submit = st.form_submit_button("CALCULAR E SALVAR")
    
    st.markdown("---")
    if st.button("🗑️ Limpar Planilha"):
        colunas = ["Corte", "Preco_KG", "Peso_Gondola", "Peso_Grelhado", "# Dif_Peso", 
                   "% Perda_Perc", "Preco_G_Gondola", "Preco_G_Grelhado", "Dif_Preco_G", "% Aumento_Perc"]
        df_reset = pd.DataFrame(columns=colunas)
        conn.update(data=df_reset)
        st.sidebar.success("Planilha zerada!")
        st.rerun()

# 4. PROCESSAMENTO
if submit and corte:
    dif_peso = p_gondola - p_grelhado
    perda_perc = (dif_peso / p_gondola) * 100 if p_gondola > 0 else 0
    p_g_gondola = preco_kg / 1000
    p_g_grelhado = (p_g_gondola * p_gondola) / p_grelhado if p_grelhado > 0 else 0
    dif_preco_g = p_g_grelhado - p_g_gondola
    aumento_perc = (dif_preco_g / p_g_gondola) * 100 if p_g_gondola > 0 else 0

    df_atual = conn.read(ttl=0)
    nova_linha = {
        "Corte": corte, "Preco_KG": preco_kg, "Peso_Gondola": p_gondola, "Peso_Grelhado": p_grelhado,
        "# Dif_Peso": round(dif_peso, 2), "% Perda_Perc": round(perda_perc, 2),
        "Preco_G_Gondola": round(p_g_gondola, 4), "Preco_G_Grelhado": round(p_g_grelhado, 4),
        "Dif_Preco_G": round(dif_preco_g, 4), "% Aumento_Perc": round(aumento_perc, 2)
    }

    if not df_atual.empty and corte in df_atual['Corte'].values:
        idx = df_atual.index[df_atual['Corte'] == corte].tolist()[0]
        for col, val in nova_linha.items():
            df_atual.at[idx, col] = val
    else:
        df_atual = pd.concat([df_atual, pd.DataFrame([nova_linha])], ignore_index=True)

    conn.update(data=df_atual)
    st.success(f"'{corte}' processado!")

# 5. RANKING (LINHA ONDE ESTAVA O ERRO)
try:
    df_db = conn.read(ttl=0)
    if not df_db.empty:
        ranking = df_db.sort_values(by="Preco_G_Grelhado", ascending=True)
        campeao = ranking.iloc[0]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Melhor Opção", campeao['Corte'])
        c2.metric("Preço/g Pronto", f"R$ {campeao['Preco_G_Grelhado']:.4f}")
        c3.metric("Perda Real", f"{campeao['% Perda_Perc']}%")

        st.subheader("🏆 Ranking de Custo-Benefício")
        st.dataframe(ranking, use_container_width=True)
except:
    st.info("Aguardando lançamentos...")
