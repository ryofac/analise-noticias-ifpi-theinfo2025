# Análise de Notícias do IFPI — Exemplo de Webscraping
Projeto demonstrativo usado como exemplo na Palestra sobre Webscraping no Teresina Info 2025.

Resumo
- Coleção, análise e visualização de notícias do portal IFPI.
- Fluxo: raspagem assíncrona → análise NLP (detecção de editais, NER para campi, classificação por tópico) → dashboard Streamlit.
- Arquivos principais:
  - [`scraping.py`](scraping.py) — coleta notícias do site do IFPI.
  - [`analise_nlp.py`](analise_nlp.py) — enriquece dados com NLP (spaCy + regras).
  - [`app.py`](app.py) — dashboard Streamlit para visualização.
  - [`data_pipeline.py`](data_pipeline.py) — script que executa raspagem + análise em sequência.
  - Dados gerados: [`data/noticias_ifpi.csv`](data/noticias_ifpi.csv) e [`data/analise_editais.csv`](data/analise_editais.csv).

Pré-requisitos
- Python >= 3.13 (ver `pyproject.toml`).
- Dependências listadas em `pyproject.toml` (ex.: aiohttp, beautifulsoup4, pandas, spacy, streamlit, wordcloud, nltk, plotly).

Instalação rápida
```bash
# criar virtualenv (recomendado)
python -m venv .venv
source .venv/bin/activate

# instalar dependências (usar uv ou seu gerenciador)
pip install uv
uv sync --active

```

Passos para usar (modo interativo / completo)
1. Baixar as stopwords do NLTK e o modelo spaCy (necessário para `analise_nlp.py`):
```bash
python -c "import nltk; nltk.download('stopwords')"
python -m spacy download pt_core_news_sm
```

2. Raspagem (gera `data/noticias_ifpi.csv`):
```bash
python scraping.py
# ou executar via data_pipeline.py que chama scraping + análise:
python data_pipeline.py
```

3. Análise NLP (gera `data/analise_editais.csv`):
```bash
python analise_nlp.py
# ou já executado por data_pipeline.py
```

4. Abrir o dashboard Streamlit:
```bash
streamlit run app.py
```
O dashboard lê `data/analise_editais.csv` e `data/noticias_ifpi.csv` e permite:
- Visualizar top campi citados.
- Ver distribuição de editais por campus e tópico.
- Filtrar e navegar pela tabela de notícias/editais.
- Gerar nuvem de palavras a partir das notícias.

Notas e dicas
- Se quiser rodar tudo em sequência, use [`data_pipeline.py`](data_pipeline.py).
- O arquivo `pyproject.toml` contém as dependências do projeto.
- Em ambientes com bloqueios de rede ou sites que bloqueiam scraping, ajuste tempos/headers em [`scraping.py`](scraping.py) e verifique limites de requisição.
- Ajuste o mapeamento de campi e tópicos em [`analise_nlp.py`](analise_nlp.py) conforme necessidade local.

Licença
- Uso educativo / exemplo de demonstração em palestra. Ajuste conforme desejar.

Contato
- Uso destinado à apresentação no Teresina Info 2025.