# Projeto final do Módulo 1
# Autora: Camila Gomes dos Santos
# Tratamento dos dados da camada RAW para SILVER

import pandas as pd
from banco import conectar
from config import TAMANHO_BLOCO
from psycopg2.extras import execute_values

def converter_valor(coluna):
    valores = coluna.str.strip()
    valores = valores.str.replace(",", ".", regex=False)
    convertidos = pd.to_numeric(valores, errors="coerce")

    invalidos = (
        valores.notna()
        & valores.ne("")
        & convertidos.isna()
    )

    if invalidos.any():
        raise ValueError(
            f"Valor numérico inválido na coluna {coluna.name}."
        )

    return convertidos

def converter_data(coluna):
    datas = coluna.str.strip()
    convertidas = pd.to_datetime(
        datas,
        format="%d/%m/%Y",
        errors="coerce"
    )

    invalidas = (
        datas.notna()
        & datas.ne("")
        & convertidas.isna()
    )

    if invalidas.any():
        raise ValueError(
            f"Data inválida na coluna {coluna.name}."
        )

    return convertidas

def limpar_texto(coluna):
    textos = coluna.str.strip()
    return textos.replace("", None)

def transformar_viagens(viagens):
    colunas_texto = [
        "id_viagem", "num_proposta", "situacao", "viagem_urgente",
        "cod_orgao_superior", "nome_orgao_superior",
        "nome_viajante", "cargo", "destinos", "motivo"
    ]

    for coluna in colunas_texto:
        viagens[coluna] = limpar_texto(viagens[coluna])

    viagens["data_inicio"] = converter_data(viagens["data_inicio"])
    viagens["data_fim"] = converter_data(viagens["data_fim"])

    colunas_valores = [
        "valor_diarias", "valor_passagens",
        "valor_devolucao", "valor_outros_gastos"
    ]

    for coluna in colunas_valores:
        viagens[coluna] = converter_valor(viagens[coluna])
        
    obrigatorias = ["id_viagem", "nome_orgao_superior"]

    if viagens[obrigatorias].isna().any().any():
        raise ValueError("Viagem com campo obrigatório ausente.")

    if (viagens["data_fim"] < viagens["data_inicio"]).any():
        raise ValueError("Viagem com data final anterior à inicial.")

    if (viagens["valor_diarias"] < 0).any():
        raise ValueError("Viagem com valor de diárias negativo.")
    
    viagens["duracao_dias"] = (
        viagens["data_fim"] - viagens["data_inicio"]
    ).dt.days + 1

    viagens["valor_total"] = (
        viagens["valor_diarias"]
        + viagens["valor_passagens"]
        + viagens["valor_outros_gastos"]
        - viagens["valor_devolucao"]
    ).round(2)

    return viagens

def inserir_viagens(cursor, viagens):
    colunas = ", ".join(viagens.columns)

    dados = viagens.astype(object).where(pd.notna(viagens), None)
    linhas = list(dados.itertuples(index=False, name=None))

    sql = f"""
        INSERT INTO silver_viagem ({colunas})
        VALUES %s
    """

    execute_values(cursor, sql, linhas)
    
def transformar_pagamentos(pagamentos):
    colunas_texto = [
        "id_viagem", "num_proposta", "nome_orgao_pagador",
        "nome_ug_pagadora", "tipo_pagamento"
    ]

    for coluna in colunas_texto:
        pagamentos[coluna] = limpar_texto(pagamentos[coluna])

    pagamentos["valor"] = converter_valor(pagamentos["valor"])

    if pagamentos[["id_viagem", "tipo_pagamento"]].isna().any().any():
        raise ValueError("Pagamento com campo obrigatório ausente.")

    if (pagamentos["valor"] < 0).any():
        raise ValueError("Pagamento com valor negativo.")

    return pagamentos


def carregar_pagamentos(conexao, cursor_carga):
    colunas = [
        "id_viagem", "num_proposta", "nome_orgao_pagador",
        "nome_ug_pagadora", "tipo_pagamento", "valor"
    ]

    cursor_leitura = conexao.cursor(name="leitura_pagamentos")
    total = 0

    try:
        cursor_leitura.execute("""
            SELECT id_viagem, num_proposta, nome_orgao_pagador,
                   nome_ug_pagadora, tipo_pagamento, valor
            FROM (
                SELECT DISTINCT *
                FROM raw_pagamento
            ) AS pagamentos_unicos
            """)

        while True:
            linhas = cursor_leitura.fetchmany(TAMANHO_BLOCO)

            if not linhas:
                break

            pagamentos = pd.DataFrame(linhas, columns=colunas)
            pagamentos = transformar_pagamentos(pagamentos)

            dados = pagamentos.astype(object).where(
                pd.notna(pagamentos), None
            )
            linhas_tratadas = list(
                dados.itertuples(index=False, name=None)
            )

            execute_values(
                cursor_carga,
                """
                    INSERT INTO silver_pagamento (
                        id_viagem, num_proposta, nome_orgao_pagador,
                        nome_ug_pagadora, tipo_pagamento, valor
                    )
                    VALUES %s
                """,
                linhas_tratadas
            )

            total += len(pagamentos)
            print(f"Pagamentos processados: {total}")

    finally:
        cursor_leitura.close()
        
def transformar_passagens(passagens):
    colunas_texto = [
        "id_viagem", "meio_transporte",
        "pais_origem_ida", "uf_origem_ida", "cidade_origem_ida",
        "pais_destino_ida", "uf_destino_ida", "cidade_destino_ida"
    ]

    for coluna in colunas_texto:
        passagens[coluna] = limpar_texto(passagens[coluna])

    for coluna in ["valor_passagem", "taxa_servico"]:
        passagens[coluna] = converter_valor(passagens[coluna])

    passagens["data_emissao"] = converter_data(
        passagens["data_emissao"]
    )

    if passagens["id_viagem"].isna().any():
        raise ValueError("Passagem sem identificador de viagem.")

    if (passagens[["valor_passagem", "taxa_servico"]] < 0).any().any():
        raise ValueError("Passagem com valor ou taxa negativos.")

    return passagens


def carregar_passagens(conexao, cursor_carga):
    colunas = [
        "id_viagem", "meio_transporte",
        "pais_origem_ida", "uf_origem_ida", "cidade_origem_ida",
        "pais_destino_ida", "uf_destino_ida", "cidade_destino_ida",
        "valor_passagem", "taxa_servico", "data_emissao"
    ]

    cursor_leitura = conexao.cursor(name="leitura_passagens")
    total = 0
    datas_ausentes = 0

    try:
        cursor_leitura.execute("""
            SELECT id_viagem, meio_transporte,
                   pais_origem_ida, uf_origem_ida, cidade_origem_ida,
                   pais_destino_ida, uf_destino_ida, cidade_destino_ida,
                   valor_passagem, taxa_servico, data_emissao
            FROM (
                SELECT DISTINCT *
                FROM raw_passagem
            ) AS passagens_unicas
            """)

        while True:
            linhas = cursor_leitura.fetchmany(TAMANHO_BLOCO)

            if not linhas:
                break

            passagens = pd.DataFrame(linhas, columns=colunas)
            passagens = transformar_passagens(passagens)

            datas_ausentes += passagens["data_emissao"].isna().sum()

            dados = passagens.astype(object).where(
                pd.notna(passagens), None
            )
            linhas_tratadas = list(
                dados.itertuples(index=False, name=None)
            )

            execute_values(
                cursor_carga,
                """
                    INSERT INTO silver_passagem (
                        id_viagem, meio_transporte,
                        pais_origem_ida, uf_origem_ida, cidade_origem_ida,
                        pais_destino_ida, uf_destino_ida, cidade_destino_ida,
                        valor_passagem, taxa_servico, data_emissao
                    )
                    VALUES %s
                """,
                linhas_tratadas
            )

            total += len(passagens)
            print(f"Passagens processadas: {total}")

        print(f"Datas de emissão nulas após conversão: {datas_ausentes}")

    finally:
        cursor_leitura.close()
def transformar_trechos(trechos):
    colunas_texto = [
        "id_viagem", "origem_uf", "origem_cidade",
        "destino_uf", "destino_cidade", "meio_transporte"
    ]

    for coluna in colunas_texto:
        trechos[coluna] = limpar_texto(trechos[coluna])

    for coluna in ["origem_data", "destino_data"]:
        trechos[coluna] = converter_data(trechos[coluna])

    trechos["sequencia_trecho"] = pd.to_numeric(
        trechos["sequencia_trecho"].str.strip(),
        errors="raise"
    ).astype("Int64")

    trechos["numero_diarias"] = converter_valor(
        trechos["numero_diarias"]
    )

    if trechos["id_viagem"].isna().any():
        raise ValueError("Trecho sem identificador de viagem.")

    if (trechos["numero_diarias"] < 0).any():
        raise ValueError("Trecho com número de diárias negativo.")

    return trechos


def carregar_trechos(conexao, cursor_carga):
    colunas = [
        "id_viagem", "sequencia_trecho",
        "origem_data", "origem_uf", "origem_cidade",
        "destino_data", "destino_uf", "destino_cidade",
        "meio_transporte", "numero_diarias"
    ]

    cursor_leitura = conexao.cursor(name="leitura_trechos")
    total = 0
    campos_ausentes = pd.Series(0, index=colunas, dtype="int64")

    try:
        cursor_leitura.execute("""
            SELECT id_viagem, sequencia_trecho,
                   origem_data, origem_uf, origem_cidade,
                   destino_data, destino_uf, destino_cidade,
                   meio_transporte, numero_diarias
            FROM raw_trecho
        """)

        while True:
            linhas = cursor_leitura.fetchmany(TAMANHO_BLOCO)

            if not linhas:
                break

            trechos = pd.DataFrame(linhas, columns=colunas)
            trechos = transformar_trechos(trechos)
            campos_ausentes += trechos.isna().sum()

            dados = trechos.astype(object).where(
                pd.notna(trechos), None
            )
            linhas_tratadas = list(
                dados.itertuples(index=False, name=None)
            )

            execute_values(
                cursor_carga,
                """
                    INSERT INTO silver_trecho (
                        id_viagem, sequencia_trecho,
                        origem_data, origem_uf, origem_cidade,
                        destino_data, destino_uf, destino_cidade,
                        meio_transporte, numero_diarias
                    )
                    VALUES %s
                """,
                linhas_tratadas
            )

            total += len(trechos)
            print(f"Trechos processados: {total}")

        print("\nCampos ausentes nos trechos:")
        print(campos_ausentes)

    finally:
        cursor_leitura.close()

conexao = conectar()

try:
    cursor_carga = conexao.cursor()
    cursor_carga.execute("""
        TRUNCATE TABLE
            silver_pagamento,
            silver_passagem,
            silver_trecho,
            silver_viagem
        RESTART IDENTITY
    """)
    
    consulta = """
        SELECT id_viagem, num_proposta, situacao, viagem_urgente,
               cod_orgao_superior, nome_orgao_superior,
               nome_viajante, cargo, data_inicio, data_fim,
               destinos, motivo, valor_diarias, valor_passagens,
               valor_devolucao, valor_outros_gastos
        FROM raw_viagem
    """

    colunas = [
        "id_viagem", "num_proposta", "situacao", "viagem_urgente",
        "cod_orgao_superior", "nome_orgao_superior",
        "nome_viajante", "cargo", "data_inicio", "data_fim",
        "destinos", "motivo", "valor_diarias", "valor_passagens",
        "valor_devolucao", "valor_outros_gastos"
    ]

    cursor = conexao.cursor(name="leitura_viagens")
    cursor.execute(consulta)

    total = 0
    datas_invertidas = 0
    diarias_negativas = 0
    campos_ausentes = pd.Series(0, index=colunas, dtype="int64")

    while True:
        linhas = cursor.fetchmany(TAMANHO_BLOCO)

        if not linhas:
            break

        viagens = pd.DataFrame(linhas, columns=colunas)
        viagens = transformar_viagens(viagens)
        
        inserir_viagens(cursor_carga, viagens)

        campos_ausentes += viagens[colunas].isna().sum()
        datas_invertidas += (
            viagens["data_fim"] < viagens["data_inicio"]
        ).sum()
        diarias_negativas += (
            viagens["valor_diarias"] < 0
        ).sum()

        total += len(viagens)
        print(f"Viagens processadas: {total}")

    cursor.close()

    carregar_pagamentos(conexao, cursor_carga)
    
    carregar_passagens(conexao, cursor_carga)
    
    carregar_trechos(conexao, cursor_carga)

    cursor_carga.close()
    conexao.commit()
    print("\nCarga das quatro tabelas SILVER concluída!")

    print("\nCampos ausentes por coluna:")
    print(campos_ausentes)

    print("\nViagens com data final anterior à inicial:")
    print(datas_invertidas)

    print("\nValores de diárias negativos:")
    print(diarias_negativas)

except Exception as erro:
    conexao.rollback()
    print(f"Erro na transformação: {erro}")
    raise

finally:
    conexao.close()