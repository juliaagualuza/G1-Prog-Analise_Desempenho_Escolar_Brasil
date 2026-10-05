# 🎓 Desempenho Escolar no Brasil — Projeto G1

Projeto de análise e visualização de dados (Python + Pandas + Matplotlib + Seaborn + Streamlit) sobre o desempenho escolar no Brasil (2015–2024).

- 🌐 Página do projeto (GitHub Pages): `https://SEU-USUARIO.github.io/projeto-g1/`
- 📊 Dashboard (Streamlit): `https://SEU-APP.streamlit.app`
- 💻 Repositório: `https://github.com/SEU-USUARIO/projeto-g1`

> ⚠️ A base é **simulada** — os resultados não representam estatísticas oficiais.

## Dados

Disciplina: Linguagem de Programação

Professor: Alexandre Neves Louzada

Nome Aluna: Júlia Agualuza Barboza

## Problema
Como o desempenho escolar varia entre regiões, redes de ensino, disciplinas e anos? Renda e acesso à internet estão associados às notas?

## Estrutura
```
projeto-g1/
├── app.py                 # dashboard Streamlit
├── utils.py               # tratamento e engenharia de atributos (compartilhado)
├── requirements.txt
├── README.md
├── index.html             # página do projeto (GitHub Pages)
├── dados/                 # CSV original
├── database/              # criar_banco.py (SQLAlchemy) + desempenho_escolar.db
├── notebooks/             # analise_desempenho_escolar.ipynb
└── imagens/               # gráficos exportados pelo notebook
```

## Como executar
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python database/criar_banco.py     # (opcional) recria o banco SQLite
streamlit run app.py
```

## Funcionalidades
**Intermediárias:** filtros múltiplos · KPIs dinâmicos · gráficos interativos (Plotly) · análise temporal · tratamento de dados · dashboard em abas · visualizações comparativas · análise geográfica · upload de CSV.

**Avançadas:** persistência em banco (SQLAlchemy + SQLite) · modelagem relacional (`municipios` 1—N `desempenho`) · mapa interativo (Plotly) · correlação estatística (Pearson, p-valor, regressão) · séries temporais com média móvel.

## Principais achados
- Média das notas: **65,0** · aprovação **77,4%** · reprovação **18,4%**.
- Centro-Oeste (68,8) lidera; Norte (63,2) tem a menor média. Rede pública × privada: 65,0 × 64,9 (sem diferença significativa).
- Correlação entre renda/internet e notas ≈ **0,01** (não significativa).
- **Qualidade dos dados:** 39,3% dos registros têm aprovação + reprovação > 100%; o nível de desempenho original não segue o índice.

## Publicação
1. **GitHub:** crie o repositório e envie todos os arquivos.
2. **GitHub Pages:** *Settings → Pages → Deploy from a branch → main / (root)*.
3. **Streamlit Community Cloud:** share.streamlit.io → *New app* → repositório → arquivo `app.py`.
4. Substitua os links `SEU-USUARIO` / `SEU-APP` / `SEU NOME AQUI` no `README.md` e no `index.html`.
