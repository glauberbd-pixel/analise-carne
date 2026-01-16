import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Estilo Dark Mode Premium
st.set_page_config(page_title="Gestão de Grelhados", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0c0c0c; color: #e0e0e0; }
    div[data-testid="stMetricValue"] { color: #d4af37 !important; font-size: 28px !important; }
    label { color: #d4af37 !important; font-weight: bold; }
    h1, h2, h3 { color: #d4af37 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🥩 Inteligência de Grelhados")

# Conexão com a planilha
conn = st.connection("gsheets", type=GSheetsConnection)

# --- FORMULÁRIO DE ENTRADA ---
with st.sidebar:
    st.header("📋 Lançamento")
    with st.form("form_carne", clear_on_submit=True):
        corte = st.text_input("Nome do Corte").strip()
        preco_kg = st.number_input("Preço KG (R$)", min_value=0.0, format="%.2f")
        peso_gondola = st.number_input("Peso Gôndola (g)", min_value=0.0)
        peso_grelhado = st.number_input("Peso Grelhado (g)", min_value=0.0)
        submit = st.form_submit_button("CALCULAR E SALVAR")

if submit and corte:
    # --- CÁLCULOS MATEMÁTICOS ---
    dif_peso = peso_gondola - peso_grelhado
    perda_perc = (dif_peso / peso_gondola) * 100 if peso_gondola > 0 else 0
    p_g_gondola = preco_kg / 1000
    
    # Custo real por grama após o preparo
    p_g_grelhado = (p_g_gondola * peso_gondola) / peso_grelhado if peso_grelhado > 0 else 0
    dif_preco_g = p_g_grelhado - p_g_gondola
    aumento_perc = (dif_preco_g / p_g_gondola) * 100 if p_g_gondola > 0 else 0

    # Lendo dados para evitar duplicidade
    df_atual = conn.read(ttl=0)
    
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

    if not df_atual.empty and corte in df_atual['Corte'].values:
        idx = df_atual.index[df_atual['Corte'] == corte].tolist()[0]
        for col, val in nova_linha.items():
            df_atual.at[idx, col] = val
        st.info(f"Dados de '{corte}' atualizados!")
    else:
        df_atual = pd.concat([df_atual, pd.DataFrame([nova_linha])], ignore_index=True)
        st.success(f"'{corte}' adicionado com sucesso!")

    conn.update(data=df_atual)

# --- RANKING DE CUSTO-BENEFÍCIO ---
try:
    df_db = conn.read(ttl=0)
    if not df_db.empty:
        st.subheader("🏆 Ranking: Menor Preço por Grama Grelhado")
        # Ordenar do mais barato para o mais caro (grelhado)
        ranking = df_db.sort_values(by="Preco_G_Grelhado", ascending=True)
        st.dataframe(ranking, use_container_width=True)
        
        # Destaque do campeão
        melhor = ranking.iloc[0]
        st.success(f"💡 Dica: **{melhor['Corte']}** é seu melhor custo-benefício atual.")
except:
    st.info("Aguardando o primeiro lançamento para gerar o ranking.")
