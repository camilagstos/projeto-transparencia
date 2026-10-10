# Projeto final do Módulo 1
# Autora: Camila Gomes dos Santos

import zipfile

import pandas as pd
import requests
from psycopg2.extras import execute_values

from config import (
    PASTA_DADOS,
    DRIVE_FILE_ID,
    ARQUIVOS,
    CSV_SEPARADOR,
    CSV_ENCODING,
    TAMANHO_BLOCO,
)

from banco import conectar

def preparar_pasta_dados():
    PASTA_DADOS.mkdir(exist_ok=True)
    print(f"Pasta de dados pronta: {PASTA_DADOS}")


def baixar_zip():
    url = f"https://drive.usercontent.google.com/download?id={DRIVE_FILE_ID}&export=download&confirm=t"

    caminho_zip = PASTA_DADOS / "viagens_2025_6meses.zip"

    print("Solicitando o arquivo ao Google Drive...")

    resposta = requests.get(url, stream=True, timeout=60)
    resposta.raise_for_status()
    with open(caminho_zip, "wb") as arquivo:
        for pedaco in resposta.iter_content(chunk_size=1024 * 1024):
            arquivo.write(pedaco)
    if not zipfile.is_zipfile(caminho_zip):
        raise RuntimeError(
            "O arquivo baixado não é um ZIP. "
            "Confira se o arquivo no Drive permite acesso "
            "a qualquer pessoa com o link."
        )

    with zipfile.ZipFile(caminho_zip) as pacote:
        pacote.extractall(PASTA_DADOS)

    print("Download concluído e CSVs extraídos na pasta data.")
    
def carregar_raw(conexao, nome_csv, tabela):
    cursor = conexao.cursor()
    cursor.execute(f"TRUNCATE {tabela}")

    total = 0

    blocos = pd.read_csv(
        PASTA_DADOS / nome_csv,
        sep=CSV_SEPARADOR,
        encoding=CSV_ENCODING,
        dtype=str,
        keep_default_na=False,
        chunksize=TAMANHO_BLOCO,
    )
    for bloco in blocos:
        linhas = bloco.values.tolist()

        execute_values(
            cursor,
            f"INSERT INTO {tabela} VALUES %s",
            linhas
        )

        total += len(linhas)
        print(f"{tabela}: {total} registros inseridos")

    conexao.commit()
    cursor.close()
    print(f"Carga de {tabela} concluída: {total} registros.")
    
conexao = None

try:
    preparar_pasta_dados()
    baixar_zip()

    conexao = conectar()

    for nome, dados in ARQUIVOS.items():
        carregar_raw(
            conexao,
            dados["csv"],
            dados["tabela_raw"]
        )

    print("Carga das quatro tabelas RAW concluída!")

except Exception as erro:
    if conexao is not None:
        conexao.rollback()
    print(f"Erro na extração ou carga: {erro}")

finally:
    if conexao is not None:
        conexao.close()