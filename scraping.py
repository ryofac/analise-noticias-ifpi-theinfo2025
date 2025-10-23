import asyncio
import csv
import re
from datetime import datetime
from traceback import format_exc

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup

BASE_URL = "https://www.ifpi.edu.br/ultimas-noticias"
OUTPUT_FILE = "./data/noticias_ifpi.csv"

# Configuração de limites
MAX_PAGES = 10
ITENS_POR_PAGINA = 30

# Limite de conexões simultâneas
MAX_CONEXOES_SIMULTANEAS = 5


async def obter_texto_noticia(session, link, titulo, data):
    """
    Obtém o texto completo da notícia e retorna um dicionário com os dados relacionados.
    """
    try:
        async with session.get(
            link, timeout=aiohttp.ClientTimeout(total=60)
        ) as response:
            response.raise_for_status()
            html = await response.text()

            soup = BeautifulSoup(html, "html.parser")
            conteudo_div = soup.find("div", property="rnews:articleBody")

            texto_completo = "Conteúdo não encontrado ou Erro de Seletor"
            if conteudo_div:
                paragrafos = conteudo_div.find_all("p")
                texto_completo = " ".join(p.get_text(strip=True) for p in paragrafos)

            return {
                "titulo": titulo,
                "texto": texto_completo[:2000],
                "link": link,
                "data": data,
            }

    except Exception as e:
        # Captura erros de requisição ou timeout
        print(f"[ERRO REQ] Erro ao obter conteúdo de {link}: {e}")
        return {"titulo": titulo, "texto": f"ERRO: {e}", "link": link, "data": data}


async def obter_links_pagina(session, url):
    """
    Raspa uma página de listagem de forma assíncrona e extrai os links e metadados.
    """
    links_e_metadados = []
    try:
        async with session.get(
            url, timeout=aiohttp.ClientTimeout(total=15)
        ) as response:
            response.raise_for_status()
            html = await response.text()

            soup = BeautifulSoup(html, "html.parser")
            itens_titulo = soup.find_all("h2", class_="tileHeadline")

            if not itens_titulo:
                return []

            for h2 in itens_titulo:
                link_tag = h2.find("a", class_="summary url")
                titulo = link_tag.get_text(strip=True) if link_tag else "N/A"
                link = (
                    link_tag["href"] if link_tag and "href" in link_tag.attrs else "N/A"
                )

                # Buscando a data (lógica síncrona, mas dentro do loop de processamento da página)
                data = "N/A"
                main_container = h2.find_parent("div", class_="tileContent").parent
                byline_span = main_container.find("span", class_="documentByLine")

                if byline_span:
                    date_icon_span = byline_span.find("i", class_="icon-day")
                    if date_icon_span:
                        full_date_text = date_icon_span.parent.get_text(strip=True)
                        date_match = re.search(r"\d{2}\/\d{2}\/\d{4}", full_date_text)
                        if date_match:
                            data = date_match.group(0)

                links_e_metadados.append({"titulo": titulo, "link": link, "data": data})

            return links_e_metadados

    except Exception as e:
        print(f"[ERRO LISTA] Erro ao acessar a URL {url}: {e}")
        return []


async def raspar_noticias():
    """
    Função principal que orquestra a raspagem.
    """

    # Utilizado para limitar o número de requisições em paralelo
    semaphore = asyncio.Semaphore(MAX_CONEXOES_SIMULTANEAS)

    async with aiohttp.ClientSession() as session:
        listagem_tasks = []
        for start_index in range(0, MAX_PAGES * ITENS_POR_PAGINA, ITENS_POR_PAGINA):
            url = f"{BASE_URL}?b_start:int={start_index}"
            listagem_tasks.append(obter_links_pagina(session, url))

        print(f"Iniciando raspagem de {len(listagem_tasks)} páginas de listagem...")

        # Executa todas as tarefas de listagem em paralelo
        resultados_listagem = await asyncio.gather(*listagem_tasks)

        # Consolida todos os links em uma única lista
        todos_os_links = []
        for res_lista in resultados_listagem:
            todos_os_links.extend(res_lista)

        print(
            f"Total de {len(todos_os_links)} notícias encontradas. Iniciando raspagem de conteúdo..."
        )

        conteudo_tasks = []
        for noticia in todos_os_links:

            async def scrap_task(sem, session, link, titulo, data):
                async with sem:
                    return await obter_texto_noticia(session, link, titulo, data)

            conteudo_tasks.append(
                scrap_task(
                    semaphore,
                    session,
                    noticia["link"],
                    noticia["titulo"],
                    noticia["data"],
                )
            )

        dados_completos = await asyncio.gather(*conteudo_tasks)

        return [d for d in dados_completos if d]


def salvar_csv(dados):
    if not dados:
        print("Nenhum dado para salvar.")
        return

    df = pd.DataFrame(dados)
    df = df[["titulo", "link", "data", "texto"]]
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)

    print(
        f"\n[SUCESSO] Coleta concluída! {len(dados)} notícias salvas em '{OUTPUT_FILE}'."
    )


def realizar_scraping_noticias():
    start_time = datetime.now()
    noticias = asyncio.run(raspar_noticias())
    salvar_csv(noticias)

    end_time = datetime.now()
    print(f"Tempo total de execução: {end_time - start_time}")
