import re

import nltk
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from matplotlib import pyplot as plt
from plotly.subplots import make_subplots
from wordcloud import WordCloud

# ----------------------------------------------------
# CONFIGURAÇÃO DE DADOS
# ----------------------------------------------------
EDITAIS_INPUT_FILE = "./data/analise_editais.csv"
NOTICIAS_INPUT_FILE = "./data/noticias_ifpi.csv"


@st.cache_data
def carregar_dados(
    editais_input_file=EDITAIS_INPUT_FILE,
    noticias_input_file=NOTICIAS_INPUT_FILE,
):
    """Carrega os dados e realiza o pré-processamento necessário."""
    try:
        df_editais = pd.read_csv(editais_input_file)
        # Filtra campi não mapeados ou o IFPI Central se não for útil para esta análise
        df_editais = df_editais[df_editais["Campus_Citado"] != "Não Mapeado"]

        df_noticias = pd.read_csv(noticias_input_file)
        return df_editais, df_noticias

    except FileNotFoundError:
        st.error("Erro: Arquivo de dados não encontrado.")
        st.info(
            "Por favor, execute o 'scraping_async.py' e o 'analise_editais.py' antes de iniciar o dashboard."
        )
        return pd.DataFrame()


def criar_grafico_campi(df):
    """Cria um gráfico de barras para os campi mais citados."""

    contagem_campi = df["Campus_Citado"].value_counts().reset_index()
    contagem_campi.columns = ["Campus", "Total de Menções"]

    contagem_campi = contagem_campi.head(10)

    fig = px.bar(
        contagem_campi,
        x="Total de Menções",
        y="Campus",
        orientation="h",
        title="Top 10 Campi mais Citados em Notícias (Excluindo Reitoria)",
        color_discrete_sequence=px.colors.qualitative.Prism,
        text="Total de Menções",
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"}
    )  # Garante que o maior esteja no topo
    fig.update_traces(textposition="outside")

    return fig


def criar_grafico_editais(df):
    """Cria um gráfico agrupado de tópicos de editais por campus."""

    df_editais = df[df["Is_Edital"] == True]

    if df_editais.empty:
        return None

    # Agrupamento: Contagem de editais por Campus e por Tópico Classificado
    contagem_editais = (
        df_editais.groupby(["Campus_Citado", "Topico_Classificado"])
        .size()
        .reset_index(name="Contagem")
    )

    fig = px.bar(
        contagem_editais,
        x="Campus_Citado",
        y="Contagem",
        color="Topico_Classificado",
        title="Distribuição de Editais por Campus e Tópico",
        labels={"Campus_Citado": "Campus", "Topico_Classificado": "Tópico do Edital"},
        barmode="stack",  # Barras empilhadas
        color_discrete_sequence=px.colors.qualitative.Safe,  # Cores seguras
    )
    fig.update_xaxes(tickangle=45)
    fig.update_layout(legend_title_text="Tópico")

    return fig


def gerar_nuvem_de_palavras(df):
    stop_words_pt = set(nltk.corpus.stopwords.words("portuguese"))
    # Adicionando stop words específicas do contexto
    stop_words_pt.update(["ifpi", "instituto", "federal", "pi", "notícia", "noticias"])
    texto_bruto = " ".join(df["texto"].astype(str))
    texto_limpo = re.sub(r"[^a-zA-Z\s]", "", texto_bruto).lower()
    palavras = texto_limpo.split()
    palavras_filtradas = [
        palavra
        for palavra in palavras
        if palavra not in stop_words_pt and len(palavra) > 3
    ]

    wordcloud = WordCloud(
        width=800,
        height=400,
        background_color="white",
        max_words=100,
        colormap="viridis",
        collocations=False,
        normalize_plurals=True,
    ).generate(" ".join(palavras_filtradas))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wordcloud, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("Termos mais encontrados", fontsize=16)
    return fig


def criar_resumo_geral(df_editais, df_noticias):
    wordcloud = gerar_nuvem_de_palavras(df_noticias)
    st.pyplot(wordcloud)
    st.caption("Nuvem de palavras gerada a partir do texto completo das notícias.")

    total_noticias = len(df_editais)
    total_editais = df_editais["Is_Edital"].sum()

    editais_mais_comuns = df_editais[df_editais["Is_Edital"] == True][
        "Topico_Classificado"
    ].mode()

    st.metric("Total de Notícias Raspadas", total_noticias)
    st.metric(
        "Editais Identificados",
        total_editais,
        delta=f"{total_editais / total_noticias:.1%} do total",
    )

    if not editais_mais_comuns.empty:
        st.metric(
            "Tópico de Edital Mais Comum",
            editais_mais_comuns.iloc[0],
            label_visibility="visible",
        )


def main():
    st.title("📊 Análise de Notícias do IFPI")
    st.markdown("---")

    df_editais, df_noticias = carregar_dados(EDITAIS_INPUT_FILE)

    if df_editais.empty:
        return

    criar_resumo_geral(df_editais, df_noticias)

    st.header("1. Engajamento Institucional (Campi Mais Citados)")
    fig_campi = criar_grafico_campi(df_editais)
    st.plotly_chart(fig_campi, use_container_width=True)

    st.markdown("---")

    # --- 3. Análise de Editais ---
    st.header("2. Onde estão os Editais (Classificação por Tópico)")

    fig_editais = criar_grafico_editais(df_editais)

    if fig_editais:
        st.plotly_chart(fig_editais, use_container_width=True)
    else:
        st.warning("Nenhum Edital foi identificado com as palavras-chave configuradas.")

    # --- 4. Tabela Detalhada com Filtro ---
    st.header("3. Tabela Interativa de Editais")

    # Permite filtrar por tópico
    topicos_unicos = df_editais["Topico_Classificado"].unique().tolist()
    topicos_selecionados = st.multiselect(
        "Filtrar Tópicos de Editais:",
        options=topicos_unicos,
        default=[t for t in topicos_unicos if t != "Outros/Geral"],
    )

    # Filtrar o DataFrame apenas para editais e tópicos selecionados
    df_tabela = df_editais[
        (df_editais["Is_Edital"] == True)
        & (df_editais["Topico_Classificado"].isin(topicos_selecionados))
    ]

    st.write(f"Exibindo {len(df_tabela)} editais filtrados:")

    # Seleção de colunas para exibição
    colunas_tabela = ["Campus_Citado", "Topico_Classificado", "data", "titulo", "link"]
    st.dataframe(
        df_tabela[colunas_tabela].sort_values(by="data", ascending=False),
        use_container_width=True,
    )

    st.caption("A coluna 'link' permite acessar a notícia original.")


if __name__ == "__main__":
    main()
