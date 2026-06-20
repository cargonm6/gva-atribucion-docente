import json
import csv
import os

# =====================================================
# CONFIGURACIÓN
# =====================================================

DB_FILE = "fp_db.json"

DEFAULT_SEARCH = (
    "Sistemas y aplicaciones informáticas"
)

# =====================================================
# UTILIDADES
# =====================================================

def normalize(text):

    return (
        text
        .strip()
        .upper()
    )

# =====================================================
# CARGAR BASE DE DATOS
# =====================================================

def load_database():

    with open(
        DB_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)

# =====================================================
# BUSCAR ATRIBUCIÓN
# =====================================================

def search_staff(data, keyword):

    keyword = normalize(keyword)

    results = []

    for title in data["titles"]:

        nivel = title["nivel"]
        familia = title["familia"]
        nombre_titulo = title["titulo"]
        url = title["url"]

        for modulo in title["modulos"]:

            modulo_nombre = modulo["nombre"]

            for staff in modulo["atribuciones"]:

                if keyword in normalize(staff):

                    results.append({

                        "nivel": nivel,
                        "familia": familia,
                        "titulo": nombre_titulo,
                        "modulo": modulo_nombre,
                        "cuerpo": staff,
                        "url": url

                    })

    return results

# =====================================================
# EXPORTAR CSV
# =====================================================

def export_csv(results, keyword):

    filename = (
        keyword
        .replace("/", "-")
        .replace("\\", "-")
        .replace(":", "")
        .replace("*", "")
        .replace("?", "")
        .replace('"', "")
        .replace("<", "")
        .replace(">", "")
        .replace("|", "")
    )

    csv_file = f"{filename}.csv"

    with open(
        csv_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.writer(f)

        writer.writerow([
            "Nivel",
            "Familia",
            "Título",
            "Módulo",
            "Cuerpo",
            "URL"
        ])

        for row in results:

            writer.writerow([

                row["nivel"],
                row["familia"],
                row["titulo"],
                row["modulo"],
                row["cuerpo"],
                row["url"]

            ])

    return csv_file

# =====================================================
# RESUMEN
# =====================================================

def print_summary(results):

    titulos = set()
    modulos = set()

    for row in results:

        titulos.add(row["titulo"])

        modulos.add(
            (
                row["titulo"],
                row["modulo"]
            )
        )

    print("\n")
    print("=" * 60)
    print(f"TÍTULOS: {len(titulos)}")
    print(f"MÓDULOS: {len(modulos)}")
    print(f"REGISTROS: {len(results)}")
    print("=" * 60)

# =====================================================
# MAIN
# =====================================================

def main():

    answer = input(
        f'Especialidad (ENTER="{DEFAULT_SEARCH}") > '
    ).strip()

    if not answer:
        answer = DEFAULT_SEARCH

    print("\nCargando base de datos...")

    data = load_database()

    print(
        f"Buscando: {answer}"
    )

    results = search_staff(
        data,
        answer
    )

    print_summary(results)

    if not results:

        print(
            "\nNo se encontraron resultados."
        )

        return

    csv_file = export_csv(
        results,
        answer
    )

    print(
        f"\nCSV generado:"
    )

    print(
        os.path.abspath(csv_file)
    )

if __name__ == "__main__":
    main()