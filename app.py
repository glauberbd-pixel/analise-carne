import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Configuração visual
st.set_page_config(page_title="Gestão de Grelhados", layout="wide")

st.title("🥩 Calculadora de Carnes: Gôndola vs Grelhado")

# Conexão com a planilha (usando o segredo que você vai configurar)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- ENTRADA DE DADOS ---
with st.sidebar:
    st.header("Novo Lançamento")
    with st.form("form_carne", clear_on_submit=True):
        corte = st.text_input("Corte (ex: Picanha)").strip()
        preco_kg = st.number_input("Preço do KG (R$)", min_value=0.0, format="%.2f")
        peso_gondola = st.number_input("Peso Gôndola (g)", min_value=0.0)
        peso_grelhado = st.number_input("Peso Grelhado (g)", min_value=0.0)
        submit = st.form_submit_button("Salvar / Atualizar")

if submit and corte:
    # --- CÁLCULOS MATEMÁTICOS ---
    dif_peso = peso_gondola - peso_grelhado
    perda_perc = (dif_peso / peso_gondola) * 100 if peso_gondola > 0 else 0
    p_g_gondola = preco_kg / 1000
    custo_total = p_g_gondola * peso_gondola
    p_g_grelhado = custo_total / peso_grelhado if peso_grelhado > 0 else 0
    dif_preco_g = p_g_grelhado - p_g_gondola
    aumento_perc = (dif_preco_g / p_g_gondola) * 100 if p_g_gondola > 0 else 0

    # Lendo dados atuais
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

    # --- LÓGICA DE NÃO REPETIR CORTE ---
    if not df_atual.empty and corte in df_atual['Corte'].values:
        # Se o corte existe, encontra a linha e atualiza os dados
        idx = df_atual.index[df_atual['Corte'] == corte].tolist()[0]
        for col, val in nova_linha.items():
            df_atual.at[idx, col] = val
        st.info(f"Dados de '{corte}' atualizados na planilha!")
    else:
        # Se não existe, adiciona uma nova linha
        df_atual = pd.concat([df_atual, pd.DataFrame([nova_linha])], ignore_index=True)
        st.success(f"'{corte}' cadastrado com sucesso!")

    # Envia de volta para o Google Sheets
    conn.update(data=df_atual)

# --- RANKING E EXIBIÇÃO ---
try:
    df_exibir = conn.read(ttl=0)
    if not df_exibir.empty:
        st.subheader("🏆 Ranking: Menor Preço por Grama Grelhado")
        # Ordenar do menor preço para o maior
        ranking = df_exibir.sort_values(by="Preco_G_Grelhado", ascending=True)
        st.dataframe(ranking, use_container_width=True)
except:
    st.info("Aguardando o primeiro lançamento para exibir a tabela.")
