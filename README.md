# Análise de viagens a serviço do Governo Federal

**Autora:** Camila Gomes dos Santos

Projeto desenvolvido para a conclusão do módulo 01 de Manipulação de Dados com Python, do curso de Análise de Dados com Python do SCTEC/SENAI.

## Objetivo

Analisar os dados de viagens a serviço do Governo Federal disponibilizados pelo Portal da Transparência, identificando os gastos por órgão, os meios de transporte utilizados e os destinos mais frequentes.

Também busquei observar informações que limitam a análise, como os trechos com meio de transporte registrado como “Inválido”.

## Organização dos dados

O projeto foi organizado em três camadas:

- **RAW:** armazenamento dos dados originais, com os campos em formato de texto.
- **SILVER:** tratamento dos dados, conversão de datas e valores e organização das relações entre as tabelas.
- **GOLD:** criação de uma tabela e uma visão com dados agrupados para apoiar as análises.

As consultas SQL foram utilizadas no notebook para apresentar os resultados em tabelas e gráficos.

## Ferramentas utilizadas

- Python
- Pandas
- Matplotlib
- Psycopg2
- PostgreSQL e pgAdmin
- Jupyter Notebook no VS Code
- Git e GitHub

## Estrutura dos arquivos

- `0_criar_banco.sql`: criação do banco de dados e das tabelas RAW e SILVER.
- `1_extrair.py`: download dos arquivos e carga dos dados nas tabelas RAW.
- `2_transformar.py`: tratamento dos dados e carga nas tabelas SILVER.
- `3_analise.ipynb`: criação da camada GOLD e apresentação das seis análises, com consultas SQL, tabelas, gráficos e interpretações.
- `requirements.txt`: lista das bibliotecas necessárias para executar o projeto.
- `config.py`: configurações utilizadas pelo projeto.
- `banco.py`: funções de conexão e operações no PostgreSQL.
- `.env.example`: exemplo das configurações de conexão, sem a senha pessoal.
- `.gitignore`: definição dos arquivos e pastas que não devem ser enviados ao GitHub.
- `README.md`: apresentação do projeto e instruções de execução.

## Análises realizadas

1. Quais são os cinco órgãos que mais gastaram com viagens?
2. Quais meios de transporte aparecem com mais frequência nos trechos?
3. Qual é o valor médio por tipo de pagamento?
4. Qual é a participação de cada tipo de pagamento nos valores registrados?
5. Quais são as cinco UFs de destino com mais trechos registrados?
6. Quais órgãos têm mais trechos com meio de transporte registrado como “Inválido”?

## Dados utilizados

Foram utilizados dados de janeiro a junho de 2025 do Portal da Transparência, disponibilizados no arquivo ZIP fornecido pela escola.

O arquivo contém quatro conjuntos de dados: viagens, pagamentos, passagens e trechos. O download e a extração são realizados pelo script `1_extrair.py`.

## Como executar

### 1. Preparar o ambiente

É necessário ter Python, PostgreSQL e VS Code com as extensões Python e Jupyter instalados.

No terminal, dentro da pasta do projeto, crie o ambiente virtual:

```powershell
python -m venv .venv
```

Ative o ambiente no Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as bibliotecas:

```powershell
python -m pip install -r requirements.txt
```

### 2. Configurar a conexão

Copie o arquivo `.env.example`, renomeie a cópia para `.env` e preencha as configurações do seu PostgreSQL:

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DATABASE`

O banco utilizado neste projeto se chama `transparencia`. A senha deve ser preenchida somente no arquivo `.env`, que está excluído do versionamento pelo `.gitignore`.

### 3. Criar o banco e as tabelas

Abra o arquivo `0_criar_banco.sql` no pgAdmin.

1. Conectado ao banco `postgres`, selecione e execute somente o comando `CREATE DATABASE transparencia;`.
2. Abra uma nova janela do Query Tool conectada ao banco `transparencia`.
3. Execute somente os comandos `CREATE TABLE` do arquivo para criar as tabelas RAW e SILVER.

Se o banco `transparencia` já existir, pule a primeira etapa.

Os comandos `CREATE TABLE IF NOT EXISTS` criam as tabelas caso ainda não existam. Eles não alteram a estrutura de tabelas existentes.

### 4. Extrair e carregar os dados

Execute:

```powershell
python 1_extrair.py
```

O script baixa o ZIP, extrai os CSVs na pasta `data` e carrega as quatro tabelas RAW em blocos de 50 mil linhas. Uma nova execução substitui os dados anteriores dessas tabelas.

### 5. Transformar os dados

Execute:

```powershell
python 2_transformar.py
```

Essa etapa trata os dados e carrega as tabelas SILVER.

### 6. Executar as análises

Abra o arquivo `3_analise.ipynb` no VS Code e selecione o ambiente `.venv` como kernel.

Execute todas as células na ordem. O notebook cria a tabela e a visão GOLD e apresenta as seis análises com tabelas, gráficos e interpretações.

## Principais resultados

- O Ministério da Justiça e Segurança Pública apresentou o maior gasto total com viagens, com aproximadamente R$ 486,93 milhões.
- Veículo Oficial foi o meio de transporte mais frequente, com 386.424 trechos, seguido de Aéreo, com 232.666.
- DIÁRIAS apresentou o maior número de registros de pagamento, com 366.351 ocorrências. PASSAGEM apresentou o maior valor médio por registro, com R$ 1.856,78.
- DIÁRIAS e PASSAGEM representaram juntas aproximadamente 99,50% da soma dos valores registrados na tabela de pagamentos.
- São Paulo e Distrito Federal foram as UFs de destino com mais trechos, com 82.722 e 79.962 registros, respectivamente.
- Foram encontrados 26.659 trechos com meio de transporte registrado como “Inválido”. O Ministério da Defesa apresentou a maior quantidade nessa categoria, com 9.374 registros.

## Limitações da análise

Os resultados se referem ao conjunto de dados de janeiro a junho de 2025 utilizado no projeto.

A quantidade de trechos não corresponde à quantidade de viagens, pois uma viagem pode ter vários trechos, incluindo o retorno.

Os registros com meio de transporte “Inválido” foram mantidos, pois não há informação suficiente para identificar o transporte utilizado. Na análise por UF de destino, os registros sem essa informação foram excluídos da consulta.

A participação por tipo de pagamento considera a soma dos valores registrados, incluindo restituições. Por isso, esse total não representa o gasto líquido com viagens.

As comparações de gastos e de registros “Inválido” mostram valores absolutos. Esses resultados, sozinhos, não permitem concluir que houve desperdício ou que um órgão tem pior qualidade de preenchimento.

## Possibilidades de melhoria

- Ampliar a análise para outros meses e anos.
- Comparar o gasto médio por viagem entre os órgãos.
- Analisar os gastos considerando a duração das viagens.
- Comparar a proporção de trechos com transporte “Inválido” em relação ao total de cada órgão.
- Investigar os registros sem informação de UF de destino.

## Aprendizados

Neste projeto, pratiquei a extração e o tratamento de dados com Python, a organização das tabelas no PostgreSQL e a criação de consultas SQL para responder às perguntas da análise.

Também pratiquei a construção de gráficos e a interpretação dos resultados, considerando as limitações dos dados, além do versionamento com Git.