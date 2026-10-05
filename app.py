"""Dashboard — Desempenho Escolar no Brasil (Avaliação G1)
Executar:  streamlit run app.py
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import streamlit as st
from scipy import stats
from sqlalchemy import create_engine

from utils import DB_PATH, ORDEM_NIVEL, carregar_tratado, tratar_dados

st.set_page_config(page_title="Desempenho Escolar no Brasil", page_icon="🎓", layout="wide")
sns.set_theme(style="whitegrid", palette="viridis")

METRICAS = {
    "Média das notas": "media_notas",
    "Taxa de aprovação (%)": "taxa_aprovacao",
    "Taxa de reprovação (%)": "taxa_reprovacao",
    "Índice de desempenho": "indice_desempenho",
    "Acesso à internet (%)": "acesso_internet",
    "Renda média familiar (R$)": "renda_media_familiar",
}

SQL = """
SELECT d.ano, d.semestre, d.data, m.regiao, m.uf, m.municipio, d.rede_ensino, d.disciplina,
       d.media_notas, d.taxa_aprovacao, d.taxa_reprovacao, d.acesso_internet,
       d.renda_media_familiar, d.indice_desempenho, d.nivel_desempenho
FROM desempenho d JOIN municipios m ON m.id = d.municipio_id
"""


# ------------------------------------------------------------------ dados
@st.cache_data(show_spinner="Carregando dados...")
def carregar_dados() -> tuple[pd.DataFrame, str]:
    """Fonte principal: banco SQLite (SQLAlchemy, tabelas relacionadas). Fallback: CSV."""
    if DB_PATH.exists():
        engine = create_engine(f"sqlite:///{DB_PATH}")
        with engine.connect() as con:
            return tratar_dados(pd.read_sql(SQL, con)), "Banco SQLite (SQLAlchemy)"
    return carregar_tratado(), "CSV (dados/)"


def ler_upload(arquivo) -> pd.DataFrame:
    return tratar_dados(pd.read_csv(arquivo))


def sentido_correlacao(r: float) -> str:
    forca = abs(r)
    if forca < 0.10:
        nivel = "desprezível"
    elif forca < 0.30:
        nivel = "fraca"
    elif forca < 0.60:
        nivel = "moderada"
    else:
        nivel = "forte"
    return f"{nivel} ({'positiva' if r > 0 else 'negativa'})" if nivel != "desprezível" else nivel


# ------------------------------------------------------------------ cabeçalho
st.title("🎓 Desempenho Escolar no Brasil")
st.markdown(
    """
**Problema:** como o desempenho escolar (notas, aprovação e reprovação) varia entre regiões, redes de ensino,
disciplinas e ao longo do tempo (2015–2024)? E fatores como **renda familiar** e **acesso à internet**
estão associados a esse desempenho?

> ⚠️ A base é uma **simulação** (740 registros semestrais de 37 municípios). Os resultados servem para
> praticar análise e visualização de dados — não representam estatísticas oficiais do país.
"""
)

df_total, fonte = carregar_dados()

# ------------------------------------------------------------------ filtros
st.sidebar.header("🔎 Filtros")
upload = st.sidebar.file_uploader("Enviar outro CSV (mesmo formato)", type="csv")
if upload is not None:
    try:
        df_total, fonte = ler_upload(upload), "CSV enviado pelo usuário"
    except Exception as erro:  # noqa: BLE001
        st.sidebar.error(f"Não foi possível ler o arquivo: {erro}")
st.sidebar.caption(f"Fonte dos dados: {fonte}")

regioes = st.sidebar.multiselect("Região", sorted(df_total["regiao"].unique()),
                                 default=sorted(df_total["regiao"].unique()))
ufs_disp = sorted(df_total[df_total["regiao"].isin(regioes)]["uf"].unique())
ufs = st.sidebar.multiselect("UF", ufs_disp, default=ufs_disp)
redes = st.sidebar.multiselect("Rede de ensino", sorted(df_total["rede_ensino"].unique()),
                               default=sorted(df_total["rede_ensino"].unique()))
discs = st.sidebar.multiselect("Disciplina", sorted(df_total["disciplina"].unique()),
                               default=sorted(df_total["disciplina"].unique()))
ano_min, ano_max = int(df_total["ano"].min()), int(df_total["ano"].max())
anos = st.sidebar.slider("Período (anos)", ano_min, ano_max, (ano_min, ano_max))
so_consistentes = st.sidebar.checkbox("Excluir registros com taxas inconsistentes (aprovação + reprovação > 100%)")

df = df_total[
    df_total["regiao"].isin(regioes) & df_total["uf"].isin(ufs) & df_total["rede_ensino"].isin(redes)
    & df_total["disciplina"].isin(discs) & df_total["ano"].between(*anos)
]
if so_consistentes:
    df = df[~df["taxas_inconsistentes"]]

st.sidebar.metric("Registros selecionados", f"{len(df)} de {len(df_total)}")

if df.empty:
    st.warning("Nenhum registro para os filtros escolhidos. Ajuste os filtros na barra lateral.")
    st.stop()

# ------------------------------------------------------------------ KPIs dinâmicos
st.subheader("📌 Indicadores-chave (KPIs)")


def delta(col):
    return f"{df[col].mean() - df_total[col].mean():+.2f} vs. base completa"


k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Média das notas", f"{df['media_notas'].mean():.1f}", delta("media_notas"))
k2.metric("Taxa de aprovação", f"{df['taxa_aprovacao'].mean():.1f}%", delta("taxa_aprovacao"))
k3.metric("Taxa de reprovação", f"{df['taxa_reprovacao'].mean():.1f}%", delta("taxa_reprovacao"),
          delta_color="inverse")
k4.metric("Acesso à internet", f"{df['acesso_internet'].mean():.1f}%", delta("acesso_internet"))
k5.metric("% notas ≥ 60", f"{(df['media_notas'] >= 60).mean() * 100:.1f}%")

# ------------------------------------------------------------------ abas
aba1, aba2, aba3, aba4, aba5 = st.tabs(
    ["📊 Visão geral", "📈 Evolução temporal", "🗺️ Mapa e regiões", "🔗 Correlações", "🗃️ Dados"]
)

# ---- 1. Visão geral
with aba1:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Distribuição da média das notas**")
        fig, ax = plt.subplots(figsize=(6, 3.6))
        sns.histplot(df["media_notas"], bins=20, kde=True, ax=ax)
        ax.axvline(df["media_notas"].mean(), color="red", ls="--", label="Média")
        ax.set_xlabel("Média das notas")
        ax.set_ylabel("Frequência")
        ax.legend()
        st.pyplot(fig)
        plt.close(fig)
    with c2:
        st.markdown("**Média das notas por disciplina**")
        por_disc = df.groupby("disciplina", as_index=False)["media_notas"].mean().sort_values("media_notas")
        fig, ax = plt.subplots(figsize=(6, 3.6))
        sns.barplot(data=por_disc, x="media_notas", y="disciplina", hue="disciplina", legend=False, ax=ax)
        ax.set_xlabel("Média das notas")
        ax.set_ylabel("")
        for cont in ax.containers:
            ax.bar_label(cont, fmt="%.1f", padding=3)
        st.pyplot(fig)
        plt.close(fig)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("**Rede pública × privada**")
        fig, ax = plt.subplots(figsize=(6, 3.6))
        sns.boxplot(data=df, x="rede_ensino", y="media_notas", hue="rede_ensino", legend=False, ax=ax)
        ax.set_xlabel("")
        ax.set_ylabel("Média das notas")
        st.pyplot(fig)
        plt.close(fig)
    with c4:
        st.markdown("**Registros por nível de desempenho (classificação original)**")
        niv = df["nivel_desempenho"].value_counts().reindex(ORDEM_NIVEL).reset_index()
        niv.columns = ["nivel", "registros"]
        fig = px.bar(niv, x="nivel", y="registros", color="nivel", text="registros")
        fig.update_layout(showlegend=False, height=340, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

    mp = df.groupby("rede_ensino")["media_notas"].mean()
    gap = mp.get("Privada", np.nan) - mp.get("Pública", np.nan)
    melhor = por_disc.iloc[-1]
    st.info(
        f"**Interpretação:** a disciplina com maior média nos filtros atuais é **{melhor['disciplina']}** "
        f"({melhor['media_notas']:.1f}). "
        + (f"A diferença entre rede privada e pública é de apenas **{gap:+.2f} ponto(s)**, "
           "o que indica pouca separação entre as redes nesta base." if not np.isnan(gap) else
           "Selecione as duas redes para comparar público × privado.")
    )

# ---- 2. Temporal
with aba2:
    col_a, col_b, col_c = st.columns([2, 1, 1])
    metrica_nome = col_a.selectbox("Métrica", list(METRICAS), key="metrica_temp")
    janela = col_b.slider("Janela da média móvel (semestres)", 1, 6, 2)
    quebra = col_c.selectbox("Separar por", ["Nenhum", "regiao", "rede_ensino", "disciplina"])
    metrica = METRICAS[metrica_nome]

    chaves = ["data"] + ([] if quebra == "Nenhum" else [quebra])
    serie = df.groupby(chaves, as_index=False)[metrica].mean().sort_values("data")
    if quebra == "Nenhum":
        serie["media_movel"] = serie[metrica].rolling(janela, min_periods=1).mean()
    else:
        serie["media_movel"] = serie.groupby(quebra)[metrica].transform(
            lambda s: s.rolling(janela, min_periods=1).mean())

    fig = px.line(serie, x="data", y="media_movel", color=None if quebra == "Nenhum" else quebra,
                  markers=True, labels={"data": "Semestre", "media_movel": f"{metrica_nome} (média móvel)"})
    if quebra == "Nenhum":
        fig.add_scatter(x=serie["data"], y=serie[metrica], mode="lines", name="Valor observado",
                        line=dict(dash="dot", color="gray"))
    fig.add_vrect(x0="2020-01-01", x1="2021-12-31", fillcolor="orange", opacity=0.12,
                  annotation_text="Pandemia", annotation_position="top left")
    fig.update_layout(height=420, margin=dict(t=30))
    st.plotly_chart(fig, use_container_width=True)

    anual = df.groupby("ano")[metrica].mean().to_frame("valor")
    anual["variação % a.a."] = anual["valor"].pct_change() * 100
    cA, cB = st.columns([1, 1])
    with cA:
        st.markdown("**Média anual e variação percentual**")
        st.dataframe(anual.round(2), use_container_width=True)
    with cB:
        pand = df[df["periodo_pandemia"]][metrica].mean()
        fora = df[~df["periodo_pandemia"]][metrica].mean()
        st.markdown("**Pandemia (2020–2021) × demais anos**")
        st.metric("Durante a pandemia", f"{pand:.2f}" if pd.notna(pand) else "—",
                  f"{pand - fora:+.2f} vs. demais anos" if pd.notna(pand) and pd.notna(fora) else None)
        melhor_ano, pior_ano = anual["valor"].idxmax(), anual["valor"].idxmin()
        st.info(f"**Interpretação:** em *{metrica_nome}*, o melhor ano foi **{melhor_ano}** "
                f"({anual.loc[melhor_ano, 'valor']:.2f}) e o pior **{pior_ano}** "
                f"({anual.loc[pior_ano, 'valor']:.2f}). A série oscila de um ano para o outro, "
                "sem tendência clara de alta ou queda.")

# ---- 3. Mapa e regiões
with aba3:
    mapa_nome = st.selectbox("Métrica do mapa", list(METRICAS), key="metrica_mapa")
    mcol = METRICAS[mapa_nome]
    por_mun = (df.groupby(["municipio", "uf", "regiao", "lat", "lon"], as_index=False)
               .agg(valor=(mcol, "mean"), registros=("ano", "count")))
    fig = px.scatter_geo(por_mun, lat="lat", lon="lon", color="valor", size="registros",
                         hover_name="municipio", hover_data={"uf": True, "regiao": True, "lat": False,
                                                              "lon": False, "valor": ":.2f"},
                         color_continuous_scale="Viridis", labels={"valor": mapa_nome})
    fig.update_geos(scope="south america", showcountries=True, countrycolor="gray", showland=True,
                    landcolor="#f0f0f0", lataxis_range=[-35, 6], lonaxis_range=[-75, -32])
    fig.update_layout(height=520, margin=dict(t=10, b=0, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)

    cR1, cR2 = st.columns(2)
    por_reg = df.groupby("regiao", as_index=False)[mcol].mean().sort_values(mcol, ascending=False)
    with cR1:
        st.markdown(f"**{mapa_nome} por região**")
        fig, ax = plt.subplots(figsize=(6, 3.6))
        sns.barplot(data=por_reg, x="regiao", y=mcol, hue="regiao", legend=False, ax=ax)
        ax.set_xlabel("")
        ax.set_ylabel(mapa_nome)
        for cont in ax.containers:
            ax.bar_label(cont, fmt="%.1f", padding=3)
        st.pyplot(fig)
        plt.close(fig)
    with cR2:
        st.markdown(f"**Top 10 municípios — {mapa_nome}**")
        top = por_mun.sort_values("valor", ascending=False).head(10)[["municipio", "uf", "valor"]]
        top.columns = ["Município", "UF", mapa_nome]
        st.dataframe(top.round(2), hide_index=True, use_container_width=True)
    st.info(f"**Interpretação:** a região com maior valor de *{mapa_nome}* é **{por_reg.iloc[0]['regiao']}** "
            f"({por_reg.iloc[0][mcol]:.2f}) e a menor é **{por_reg.iloc[-1]['regiao']}** "
            f"({por_reg.iloc[-1][mcol]:.2f}). As diferenças entre regiões são pequenas frente à "
            "variação dentro de cada região.")

# ---- 4. Correlações
with aba4:
    colunas = list(METRICAS.values())
    nomes_inv = {v: k for k, v in METRICAS.items()}
    corr = df[colunas].corr()
    cC1, cC2 = st.columns([1.1, 1])
    with cC1:
        st.markdown("**Matriz de correlação de Pearson**")
        fig, ax = plt.subplots(figsize=(6.2, 4.8))
        sns.heatmap(corr.rename(index=nomes_inv, columns=nomes_inv), annot=True, fmt=".2f",
                    cmap="coolwarm", vmin=-1, vmax=1, center=0, ax=ax)
        plt.xticks(rotation=40, ha="right")
        st.pyplot(fig)
        plt.close(fig)
    with cC2:
        st.markdown("**Teste de correlação entre duas variáveis**")
        vx = st.selectbox("Variável X", list(METRICAS), index=5)
        vy = st.selectbox("Variável Y", list(METRICAS), index=0)
        if len(df) > 2 and vx != vy:
            r, p = stats.pearsonr(df[METRICAS[vx]], df[METRICAS[vy]])
            m1, m2 = st.columns(2)
            m1.metric("r de Pearson", f"{r:.3f}")
            m2.metric("p-valor", f"{p:.3f}")
            st.write(f"Correlação **{sentido_correlacao(r)}** — "
                     + ("estatisticamente significativa (p < 0,05)." if p < 0.05
                        else "**não** significativa (p ≥ 0,05)."))
        else:
            st.caption("Escolha duas variáveis diferentes.")

    if vx != vy and len(df) > 2:
        reg = stats.linregress(df[METRICAS[vx]], df[METRICAS[vy]])
        xs = np.linspace(df[METRICAS[vx]].min(), df[METRICAS[vx]].max(), 50)
        fig = px.scatter(df, x=METRICAS[vx], y=METRICAS[vy], color="rede_ensino", opacity=0.6,
                         hover_data=["municipio", "ano", "disciplina"],
                         labels={METRICAS[vx]: vx, METRICAS[vy]: vy})
        fig.add_trace(go.Scatter(x=xs, y=reg.intercept + reg.slope * xs, mode="lines",
                                 name="Reta de regressão", line=dict(color="black", dash="dash")))
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.info("**Interpretação:** as correlações entre renda, internet e desempenho ficam próximas de zero. "
            "Nesta base simulada, ter mais renda ou mais acesso à internet **não** está associado a notas maiores. "
            "Em dados reais, espera-se encontrar associação positiva — por isso estes resultados não devem "
            "ser generalizados.")

# ---- 5. Dados
with aba5:
    st.markdown("**Tabela de dados filtrados**")
    mostrar = ["data", "regiao", "uf", "municipio", "rede_ensino", "disciplina", "media_notas",
               "taxa_aprovacao", "taxa_reprovacao", "acesso_internet", "renda_media_familiar",
               "indice_desempenho", "nivel_desempenho", "taxas_inconsistentes"]
    st.dataframe(df[mostrar], use_container_width=True, hide_index=True)
    st.download_button("⬇️ Baixar dados filtrados (CSV)", df[mostrar].to_csv(index=False).encode("utf-8"),
                       "desempenho_filtrado.csv", "text/csv")
    st.markdown("**Resumo estatístico**")
    st.dataframe(df[list(METRICAS.values())].describe().round(2), use_container_width=True)
    n_inc = int(df["taxas_inconsistentes"].sum())
    st.caption(f"{n_inc} registros ({n_inc / len(df) * 100:.1f}%) possuem aprovação + reprovação acima de 100%.")

# ------------------------------------------------------------------ conclusão
st.divider()
st.subheader("📝 Conclusão executiva")
reg_m = df.groupby("regiao")["media_notas"].mean()
st.markdown(
    f"""
- Nos filtros atuais, a **média das notas é {df['media_notas'].mean():.1f}**, com **{df['taxa_aprovacao'].mean():.1f}%
  de aprovação** e **{df['taxa_reprovacao'].mean():.1f}% de reprovação**.
- A região com melhor média de notas é **{reg_m.idxmax()}** ({reg_m.max():.1f}) e a menor é
  **{reg_m.idxmin()}** ({reg_m.min():.1f}); a distância entre elas é de {reg_m.max() - reg_m.min():.1f} pontos.
- Rede pública e privada têm desempenho praticamente igual, e renda e internet mostram correlação desprezível
  com as notas.
- **Qualidade dos dados:** cerca de {df_total['taxas_inconsistentes'].mean() * 100:.0f}% dos registros têm
  aprovação + reprovação acima de 100%, e o *nível de desempenho* original não acompanha o *índice de desempenho*.
  Recomenda-se usar o filtro de consistência e o nível recalculado (notebook).
- **Limitação:** por ser uma base simulada, os padrões encontrados refletem a aleatoriedade dos dados, não a
  realidade educacional brasileira.
"""
)
st.caption("Projeto G1 — Linguagem de Programação: Análise e Visualização de Dados com Python")
