"""Cria o banco SQLite relacional (SQLAlchemy) a partir do CSV tratado.
Uso:  python database/criar_banco.py
Modelo: municipios (1) ──< desempenho (N)
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import Boolean, Column, Date, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, relationship

from utils import DB_PATH, carregar_tratado

Base = declarative_base()


class Municipio(Base):
    __tablename__ = "municipios"
    id = Column(Integer, primary_key=True)
    municipio = Column(String, unique=True, nullable=False)
    uf = Column(String(2), nullable=False)
    regiao = Column(String, nullable=False)
    lat = Column(Float)
    lon = Column(Float)
    registros = relationship("Desempenho", back_populates="municipio_rel")


class Desempenho(Base):
    __tablename__ = "desempenho"
    id = Column(Integer, primary_key=True)
    municipio_id = Column(Integer, ForeignKey("municipios.id"), nullable=False)
    ano = Column(Integer)
    semestre = Column(Integer)
    data = Column(Date)
    rede_ensino = Column(String)
    disciplina = Column(String)
    media_notas = Column(Float)
    taxa_aprovacao = Column(Float)
    taxa_reprovacao = Column(Float)
    acesso_internet = Column(Float)
    renda_media_familiar = Column(Float)
    indice_desempenho = Column(Float)
    nivel_desempenho = Column(String)
    taxas_inconsistentes = Column(Boolean)
    municipio_rel = relationship("Municipio", back_populates="registros")


def criar_banco():
    df = carregar_tratado()
    DB_PATH.parent.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    engine = create_engine(f"sqlite:///{DB_PATH}")
    Base.metadata.create_all(engine)

    mun = (df[["municipio", "uf", "regiao", "lat", "lon"]]
           .drop_duplicates("municipio").reset_index(drop=True))
    mun.insert(0, "id", mun.index + 1)
    mun.to_sql("municipios", engine, if_exists="append", index=False)

    fato = df.merge(mun[["id", "municipio"]].rename(columns={"id": "municipio_id"}), on="municipio")
    fato["data"] = fato["data"].dt.date
    cols = ["municipio_id", "ano", "semestre", "data", "rede_ensino", "disciplina", "media_notas",
            "taxa_aprovacao", "taxa_reprovacao", "acesso_internet", "renda_media_familiar",
            "indice_desempenho", "nivel_desempenho", "taxas_inconsistentes"]
    fato[cols].to_sql("desempenho", engine, if_exists="append", index=False)
    print(f"Banco criado em {DB_PATH}: {len(mun)} municípios, {len(fato)} registros.")


if __name__ == "__main__":
    criar_banco()
