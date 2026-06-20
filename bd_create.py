import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from bs4 import BeautifulSoup

import json
import time
import random
from datetime import datetime

# =====================================================
# CONFIGURACIÓN
# =====================================================

BASE_URL = "https://www.todofp.es"

URLS = [
    "/que-estudiar/grados-d/fp-grado-basico.html",
    "/que-estudiar/grados-d/grado-medio.html",
    "/que-estudiar/grados-d/grado-superior.html",
    "/que-estudiar/grados-e/curso-especializacion.html"
]

OUTPUT_FILE = "fp_db.json"

MAX_RETRIES = 5
REQUEST_TIMEOUT = 15

MIN_DELAY = 0.5
MAX_DELAY = 2.0

# =====================================================
# USER AGENTS
# =====================================================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 Safari/605.1.15",
    "Mozilla/5.0 (Android 14; Mobile) AppleWebKit/537.36 Chrome/122.0"
]

# =====================================================
# SESIÓN HTTP
# =====================================================

session = requests.Session()

retry_strategy = Retry(
    total=MAX_RETRIES,
    connect=MAX_RETRIES,
    read=MAX_RETRIES,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

adapter = HTTPAdapter(
    max_retries=retry_strategy,
    pool_connections=10,
    pool_maxsize=10
)

session.mount("https://", adapter)
session.mount("http://", adapter)

# =====================================================
# CACHÉ
# =====================================================

page_cache = {}

# =====================================================
# UTILIDADES
# =====================================================

def get_page(url):

    if url in page_cache:
        return page_cache[url]

    time.sleep(
        random.uniform(
            MIN_DELAY,
            MAX_DELAY
        )
    )

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "es-ES,es;q=0.9"
    }

    try:

        response = session.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers=headers
        )

        response.raise_for_status()

        page_cache[url] = response

        return response

    except Exception as e:

        print(f"\nERROR DESCARGANDO:")
        print(url)
        print(e)

        return None

# =====================================================
# DATOS DEL TÍTULO
# =====================================================

def extract_title_info(title_url):

    response = get_page(title_url)

    if response is None:
        return None

    try:

        soup = BeautifulSoup(
            response.content,
            "html.parser"
        )

        nivel = ""
        familia = ""
        titulo = ""

        titulo_div = soup.find(
            "div",
            class_="titulo"
        )

        if titulo_div:

            h1 = titulo_div.find("h1")

            if h1:
                titulo = h1.get_text(strip=True)

            p = titulo_div.find("p")

            if p:
                familia = p.get_text(strip=True)

        info_div = soup.find(
            "div",
            class_="info"
        )

        if info_div:

            p = info_div.find("p")

            if p:
                nivel = p.get_text(strip=True)

        return {
            "nivel": nivel,
            "familia": familia,
            "titulo": titulo
        }

    except Exception as e:

        print(f"ERROR PARSEANDO {title_url}")
        print(e)

        return None

# =====================================================
# ATRIBUCIONES DOCENTES
# =====================================================

def extract_modules_and_staff(attrib_url):

    response = get_page(attrib_url)

    if response is None:
        return []

    try:

        soup = BeautifulSoup(
            response.content,
            "html.parser"
        )

        modules = []

        for div in soup.find_all(
            "div",
            class_="elemento"
        ):

            p = div.find(
                "p",
                class_="titulo"
            )

            cte = div.find(
                "div",
                class_="cte"
            )

            if not p or not cte:
                continue

            module_name = p.get_text(
                strip=True
            )

            atribuciones = []

            for line in cte.stripped_strings:

                line = line.strip()

                if line and line not in atribuciones:

                    atribuciones.append(line)

            modules.append({

                "nombre": module_name,

                "atribuciones": atribuciones

            })

        return modules

    except Exception as e:

        print(f"ERROR ATRIBUCIONES {attrib_url}")
        print(e)

        return []

# =====================================================
# LISTADO DE CICLOS
# =====================================================

def extract_titles(list_url):

    response = get_page(
        BASE_URL + list_url
    )

    if response is None:
        return []

    soup = BeautifulSoup(
        response.content,
        "html.parser"
    )

    titles = []

    for tr in soup.find_all("tr"):

        td = tr.find(
            "td",
            headers="titulacion"
        )

        if not td:
            continue

        link = td.find("a")

        if not link:
            continue

        href = link.get("href")

        if not href:
            continue

        titles.append(
            BASE_URL + href
        )

    return titles

# =====================================================
# CONSTRUCCIÓN DOCUMENTO
# =====================================================

def build_document(title_url):

    print(f"\nProcesando:")
    print(title_url)

    title_data = extract_title_info(
        title_url
    )

    if title_data is None:
        return None

    attrib_url = (
        title_url[:-5]
        + "/atribucion-docente.html"
    )

    modules = extract_modules_and_staff(
        attrib_url
    )

    document = {

        "nivel":
            title_data["nivel"],

        "familia":
            title_data["familia"],

        "titulo":
            title_data["titulo"],

        "url":
            title_url,

        "atribucion_url":
            attrib_url,

        "modulos":
            modules
    }

    print(
        f"  -> {len(modules)} módulos"
    )

    return document

# =====================================================
# MAIN
# =====================================================

def main():

    database = {

        "generated_at":
            datetime.now().isoformat(),

        "titles":
            []
    }

    total_titles = 0

    for url in URLS:

        print("\n" + "=" * 60)
        print(url)
        print("=" * 60)

        title_urls = extract_titles(
            url
        )

        print(
            f"{len(title_urls)} títulos encontrados"
        )

        for title_url in title_urls:

            doc = build_document(
                title_url
            )

            if doc:

                database["titles"].append(
                    doc
                )

                total_titles += 1

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            database,
            f,
            ensure_ascii=False,
            indent=2
        )

    print("\n")
    print("=" * 60)
    print("FINALIZADO")
    print("=" * 60)
    print(
        f"Títulos: {total_titles}"
    )
    print(
        f"Archivo: {OUTPUT_FILE}"
    )

if __name__ == "__main__":
    main()