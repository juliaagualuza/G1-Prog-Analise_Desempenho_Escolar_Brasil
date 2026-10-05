"""Funções compartilhadas: leitura, tratamento e engenharia de atributos.
Usado pelo notebook, pelo script do banco de dados e pelo dashboard (app.py)."""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent
CSV_PATH = RAIZ / "dados" / "simulacao_desempenho_escolar_brasil.csv"
DB_PATH = RAIZ / "database" / "desempenho_escolar.db"

# Coordenadas aproximadas dos municípios (usadas no mapa interativo)
COORDENADAS = {
    "Manaus": (-3.119, -60.022), "Belém": (-1.456, -48.490), "Santarém": (-2.443, -54.708),
    "Porto Velho": (-8.761, -63.904), "Palmas": (-10.184, -48.333), "Salvador": (-12.971, -38.511),
    "Feira de Santana": (-12.267, -38.967), "Recife": (-8.054, -34.881),
    "Jaboatão dos Guararapes": (-8.113, -35.015), "Fortaleza": (-3.732, -38.527),
    "Juazeiro do Norte": (-7.213, -39.315), "São Luís": (-2.530, -44.303),
    "João Pessoa": (-7.115, -34.863), "Brasília": (-15.794, -47.882), "Goiânia": (-16.686, -49.265),
    "Aparecida de Goiânia": (-16.823, -49.247), "Cuiabá": (-15.601, -56.098),
    "Campo Grande": (-20.469, -54.620), "São Paulo": (-23.550, -46.633), "Campinas": (-22.906, -47.061),
    "Ribeirão Preto": (-21.177, -47.810), "Rio de Janeiro": (-22.907, -43.173),
    "Niterói": (-22.883, -43.103), "Nova Iguaçu": (-22.759, -43.451), "Petrópolis": (-22.505, -43.179),
    "Belo Horizonte": (-19.917, -43.935), "Uberlândia": (-18.918, -48.277),
    "Juiz de Fora": (-21.762, -43.350), "Vitória": (-20.315, -40.312), "Vila Velha": (-20.329, -40.292),
    "Serra": (-20.121, -40.307), "Curitiba": (-25.428, -49.273), "Londrina": (-23.310, -51.162),
    "Florianópolis": (-27.595, -48.548), "Joinville": (-26.304, -48.846),
    "Porto Alegre": (-30.035, -51.218), "Caxias do Sul": (-29.168, -51.179),
}

ORDEM_NIVEL = ["Baixo", "Médio", "Alto", "Excelente"]


def carregar_bruto(caminho=CSV_PATH) -> pd.DataFrame:
    return pd.read_csv(caminho)


def tratar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Limpeza + engenharia de atributos. Não remove linhas: apenas sinaliza inconsistências."""
    df = df.copy()
    # --- limpeza ---
    df = df.drop_duplicates()
    df["data"] = pd.to_datetime(df["data"])
    for col in ["regiao", "uf", "municipio", "rede_ensino", "disciplina", "nivel_desempenho"]:
        df[col] = df[col].astype(str).str.strip()
    df["ano"] = df["ano"].astype(int)
    df["semestre"] = df["semestre"].astype(int)

    # --- engenharia de atributos ---
    df["periodo"] = df["ano"].astype(str) + "-S" + df["semestre"].astype(str)
    df["taxa_total"] = (df["taxa_aprovacao"] + df["taxa_reprovacao"]).round(2)
    df["taxas_inconsistentes"] = df["taxa_total"] > 100          # aprovação + reprovação não pode passar de 100%
    df["situacao_notas"] = np.where(df["media_notas"] >= 60, "Acima da média (≥60)", "Abaixo da média (<60)")
    df["periodo_pandemia"] = df["ano"].between(2020, 2021)
    df["faixa_renda"] = pd.qcut(df["renda_media_familiar"], 3, labels=["Baixa", "Média", "Alta"])
    df["faixa_internet"] = pd.cut(df["acesso_internet"], [0, 50, 75, 100],
                                  labels=["Baixo (<50%)", "Médio (50–75%)", "Alto (>75%)"])
    # nível recalculado pelos quartis do índice (o nível original não segue o índice – ver notebook)
    df["nivel_calculado"] = pd.qcut(df["indice_desempenho"], 4, labels=ORDEM_NIVEL)
    df["lat"] = df["municipio"].map(lambda m: COORDENADAS.get(m, (np.nan, np.nan))[0])
    df["lon"] = df["municipio"].map(lambda m: COORDENADAS.get(m, (np.nan, np.nan))[1])
    return df.reset_index(drop=True)


def carregar_tratado() -> pd.DataFrame:
    return tratar_dados(carregar_bruto())
