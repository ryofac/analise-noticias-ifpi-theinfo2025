import csv
from collections import Counter

import pandas as pd
import spacy

INPUT_FILE = "./data/noticias_ifpi.csv"
OUTPUT_FILE = "./data/analise_editais.csv"
nlp = None

MAPA_CAMPI = {
    # Geral
    "ifpi": "IFPI - Geral",
    "instituto federal do piaui": "IFPI - Geral",
    # Teresina
    "teresina central": "IFPI - Campus Teresina Central",
    "campus central": "IFPI - Campus Teresina Central",
    "campus teresina central": "IFPI - Campus Teresina Central",
    "teresina dirceu arcoverde": "IFPI - Campus Teresina Dirceu Arcoverde",
    "dirceu": "IFPI - Campus Teresina Dirceu Arcoverde",
    "campus dirceu": "IFPI - Campus Teresina Dirceu Arcoverde",
    "teresina zona sul": "IFPI - Campus Teresina Zona Sul",
    "zona sul": "IFPI - Campus Teresina Zona Sul",
    "campus teresina zona sul": "IFPI - Campus Teresina Zona Sul",
    # ....
    # Interior
    "angical": "IFPI - Campus Angical",
    "campo maior": "IFPI - Campus Campo Maior",
    "cocal": "IFPI - Campus Cocal",
    "corrente": "IFPI - Campus Corrente",
    "floriano": "IFPI - Campus Floriano",
    "jose de freitas": "IFPI - Campus José de Freitas",
    "josé de freitas": "IFPI - Campus José de Freitas",
    "oeiras": "IFPI - Campus Oeiras",
    "parnaiba": "IFPI - Campus Parnaíba",
    "parnaíba": "IFPI - Campus Parnaíba",
    "paulistana": "IFPI - Campus Paulistana",
    "pedro ii": "IFPI - Campus Pedro II",
    "picos": "IFPI - Campus Picos",
    "pio ix": "IFPI - Campus Pio IX",
    "piripiri": "IFPI - Campus Piripiri",
    "sao joao": "IFPI - Campus São João",
    "são joão": "IFPI - Campus São João",
    "sao raimundo nonato": "IFPI - Campus São Raimundo Nonato",
    "são raimundo nonato": "IFPI - Campus São Raimundo Nonato",
    "urucui": "IFPI - Campus Uruçuí",
    "uruçuí": "IFPI - Campus Uruçuí",
    "valenca": "IFPI - Campus Valença",
    "valença": "IFPI - Campus Valença",
    # Educação a distância
    "diretoria de educação a distância": "IFPI - EaD",
    "ead": "IFPI - EaD",
}

# Palavras-chave para Classificar o Tópico dos Editais (Ordem de prioridade importa!)
MAPA_TOPICOS = {
    "Assistência Estudantil": [
        "bolsa",
        "permanência",
        "auxílio",
        "moradia",
        "apoio estudantil",
    ],
    "Pós-Graduação": ["mestrado", "doutorado", "especialização", "pós-graduação"],
    "Concursos e Seleção de Servidores": [
        "concurso",
        "servidores",
        "tae",
        "professor",
        "cargo efetivo",
    ],
    "Ensino e Cursos": ["vagas", "cursos", "matrículas", "ensino técnico"],
    "Pesquisa e Inovação": [
        "pesquisa",
        "iniciação científica",
        "inovação",
        "extensão tecnológica",
        "residência tecnológica",
    ],
    "Extensão e Cultura": [
        "extensão",
        "cultura",
        "evento",
        "palestra",
        "curso de férias",
        "minicurso",
    ],
}

PALAVRAS_CHAVE_EDITAL = [
    "edital",
    "seleção",
    "processo seletivo",
    "inscrições abertas",
    "chamada pública",
]


def identificar_campus(texto):
    """
    Usa NER para encontrar locais/organizações e mapeá-los para um Campus padronizado.
    Retorna o campus padronizado mais provável.
    """
    doc = nlp(texto)
    entidades_candidatas = Counter()

    for ent in doc.ents:
        # Filtra por Local (LOC) ou Organização (ORG)
        if ent.label_ in ["LOC", "ORG"]:
            # Normaliza a entidade para comparação
            ent_texto_normalizado = ent.text.strip().lower()

            # 1. Tenta mapear diretamente para o Campus
            for chave in MAPA_CAMPI:
                if chave in ent_texto_normalizado:
                    entidades_candidatas[MAPA_CAMPI[chave]] += 1
                    break

    # Retorna o campus mais citado que foi padronizado
    if entidades_candidatas:
        campus_mais_citado = entidades_candidatas.most_common(1)[0][0]
        return campus_mais_citado

    return "Não Mapeado"


def classificar_topico_edital(titulo, texto):
    """
    Classifica o tópico da notícia baseando-se em palavras-chave.
    """
    texto_para_analise = str(str(titulo) + " " + str(texto)).lower()

    # Itera sobre os tópicos em ordem de prioridade
    for topico, palavras_chave in MAPA_TOPICOS.items():
        for chave in palavras_chave:
            if chave in texto_para_analise:
                return topico

    return "Outros/Geral"


def analisar_editais(df):
    """
    Processa o DataFrame, identifica editais, mapeia campi e classifica tópicos.
    """
    # Carrega o modelo SpaCy
    global nlp
    try:
        nlp = spacy.load("pt_core_news_sm")
    except OSError:
        print(
            "ERRO: Modelo SpaCy 'pt_core_news_sm' não carregado. Baixe-o (veja as instruções)."
        )
        return pd.DataFrame()

    df["texto_completo"] = df["titulo"].astype(str) + " " + df["texto"].astype(str)

    # 1. Identificar se é um Edital
    def is_edital(texto_completo):
        texto_lower = texto_completo.lower()
        return any(chave in texto_lower for chave in PALAVRAS_CHAVE_EDITAL)

    df["Is_Edital"] = df["texto_completo"].apply(is_edital)

    # 2. Classificar o Tópico (para Editais e Não-Editais)
    df["Topico_Classificado"] = df.apply(
        lambda row: classificar_topico_edital(row["titulo"], row["texto"]), axis=1
    )

    # 3. Identificar o Campus (Aplica NER e Mapeamento)
    print("Iniciando Identificação de Campi (NER)...")
    df["Campus_Citado"] = df["texto_completo"].apply(identificar_campus)
    print("Identificação de Campi concluída.")

    # 4. Preparar DataFrame de Saída
    df_saida = df[
        ["titulo", "link", "data", "Is_Edital", "Campus_Citado", "Topico_Classificado"]
    ]

    return df_saida


def salvar_dados_analise(df):
    """Salva o DataFrame enriquecido."""
    if df.empty:
        print("Nenhum dado para salvar após a análise.")
        return

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)
    print("\n[SUCESSO] Análise de Editais e Campi concluída!")
    print(f"Resultado salvo em '{OUTPUT_FILE}'.")


def realizar_analise_nlp():
    try:
        df_noticias = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        print(f"ERRO: Arquivo de entrada '{INPUT_FILE}' não encontrado.")
        print(
            "Por favor, execute primeiro o script de raspagem assíncrona ('scraping_async.py')."
        )
    else:
        df_analisado = analisar_editais(df_noticias)
        salvar_dados_analise(df_analisado)

        # Exemplo de Contagem para conferência
        print("\n--- Contagem de Editais por Tópico e Campus ---")
        df_editais = df_analisado[df_analisado["Is_Edital"] == True]
        if not df_editais.empty:
            contagem = (
                df_editais.groupby(["Campus_Citado", "Topico_Classificado"])
                .size()
                .reset_index(name="Total")
            )
            contagem_formatada = contagem.sort_values(by="Total", ascending=False)
            print(contagem_formatada.to_string(index=False))
        else:
            print("Nenhum edital identificado com as palavras-chave.")


if __name__ == "__main__":
    realizar_analise_nlp()
