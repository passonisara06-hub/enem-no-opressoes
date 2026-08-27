# Nó de opressões no ENEM 2025
### Análise ecológica do nó raça–gênero–classe nos microdados do Exame Nacional do Ensino Médio

**Orientação teórica:** Feminismo marxista | Heleieth Saffioti  
**Conceito central:** Nó de opressões — raça, gênero e classe como sistema articulado de dominação-exploração, não como eixos independentes que se cruzam  
**Dados:** Microdados ENEM 2025 — INEP/MEC

### ⚠️ Nota metodológica

A partir de 2020, o INEP dividiu os microdados em dois arquivos (PARTICIPANTES e RESULTADOS) por exigência da LGPD, **sem chave de junção individual**. Isso significa que **não é possível vincular dados demográficos (raça, gênero) a notas individuais**. A análise é **ecológica** (nível UF): correlações agregadas não implicam relações individuais (falácia ecológica).

---

## Estrutura do projeto

```
enem_no_opressoes/
├── data/
│   ├── raw/                          # Microdados originais do INEP
│   │   ├── PARTICIPANTES_2025.csv    # Dados demográficos (sexo, raça, renda)
│   │   └── RESULTADOS_2025.csv       # Notas, presença, tipo de escola
│   └── processed/                    # Dados limpos e recodificados
├── microdados_enem_2025/             # Dados brutos do INEP (zip extraído)
├── src/
│   ├── constants.py      # Constantes centralizadas (mapeamentos, cores, paths)
│   ├── ingestao.py       # Leitura e recodificação dos dois arquivos
│   ├── grupos.py         # Métricas agregadas por UF e tipo de escola
│   ├── novas_analises.py # Métricas de trabalho reprodutivo e capital herdado
│   ├── inferencial.py    # Regressão ecológica e testes agregados
│   └── visualizacoes.py  # Funções de gráficos reutilizáveis
├── notebooks/
│   └── 01_analise_completa.ipynb
├── app/
│   └── dashboard.py      # App Streamlit narrativo
├── docs/
│   └── referencias.md    # Referências teóricas e metodológicas
├── requirements.txt
└── README.md
```

## Como usar

### 1. Instalar dependências
```bash
# Para rodar o dashboard (produção / Streamlit Cloud)
pip install -r requirements.txt

# Para rodar também o notebook de análise (jupyter, openpyxl, etc.)
pip install -r requirements-dev.txt
```

### 2. Baixar os microdados
Acesse: https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem  
Baixe os microdados do ENEM 2025 e extraia os arquivos `PARTICIPANTES_2025.csv` e `RESULTADOS_2025.csv` para `data/raw/`.

Ou crie symlinks a partir do diretório extraído:
```bash
ln -sf /caminho/para/microdados_enem_2025/DADOS/PARTICIPANTES_2025.csv data/raw/PARTICIPANTES_2025.csv
ln -sf /caminho/para/microdados_enem_2025/DADOS/RESULTADOS_2025.csv data/raw/RESULTADOS_2025.csv
```

### 3. Rodar o pipeline
```bash
python3 src/ingestao.py        # gera participantes_limpo.parquet e resultados_limpo.parquet
python3 src/grupos.py          # gera metricas_demograficas.parquet e metricas_desempenho.parquet
python3 src/novas_analises.py  # gera trabalho_reprodutivo_*.parquet e capital_herdado_*.parquet
python3 src/inferencial.py     # gera regressao_ecologica.parquet, gaps_regionais.parquet, testes_kruskal.parquet
```

### 4. Explorar o notebook
```bash
jupyter notebook notebooks/01_analise_completa.ipynb
```

### 5. Rodar o dashboard
```bash
streamlit run app/dashboard.py
```

### 6. Publicar online (Streamlit Community Cloud)

O painel pode ficar hospedado gratuitamente 24/7 no **Streamlit Community Cloud**,
gerando um link público do tipo `https://<seu-app>.streamlit.app`.

**Como o deploy funciona (dados):** o dashboard consome apenas **agregados pequenos**
(~40 KB, versionados no repo em `data/processed/`): `metricas_demograficas`,
`metricas_desempenho`, `regressao_ecologica`, `gaps_regionais`, `testes_kruskal`,
`presenca_tipo_escola` e `notas_tipo_escola`. Os microdados individuais
(`participantes_limpo` / `resultados_limpo`, ~115 MB) **não são carregados** —
todas as métricas escalares e os gráficos por tipo de escola são derivados dos
agregados. Por isso o deploy é leve e não precisa dos CSVs brutos do INEP.

**Passo a passo:**

1. Garanta que o repo está no GitHub e atualizado:
   ```bash
   git add -A && git commit -m "Deploy: dashboard usa agregados; config Streamlit Cloud"
   git push origin main
   ```
2. Acesse <https://share.streamlit.io> e entre com a conta GitHub
   (`passonisara06-hub`).
3. **New app** → selecione o repo `passonisara06-hub/enem-no-opressoes` → branch
   `main`.
4. Em **Main file path**, informe: `app/dashboard.py`
5. Em **Python version**, use a mais recente disponível (3.13+).
6. **Deploy!** A primeira build instala `requirements.txt` e inicia o app.
   O link aparece no topo quando estiver pronto.

**Observações:**
- O app entra em sleep após ~7 dias sem visitas; a primeira visita após isso
  "acorda" o app em alguns segundos.
- Se quiser um deploy mais rápido (sem instalar `jupyter`/`notebook`, que o
  dashboard não usa), crie um `requirements.txt` enxuto só para o Cloud — mas o
  atual funciona sem alteração.
- Configuração de tema está em `.streamlit/config.toml` (cores terra/âmbar).

## Variáveis centrais da análise

### PARTICIPANTES (demografia)
| Variável INEP | Descrição | Uso no projeto |
|---|---|---|
| `TP_SEXO` | Sexo declarado (M/F) | Dimensão gênero do nó |
| `TP_COR_RACA` | Cor/raça autodeclarada (0–5) | Dimensão raça do nó |
| `Q007` | Renda familiar mensal (A–Q) | Proxy de classe |
| `TP_ST_CONCLUSAO` | Situação de conclusão do EM | Contexto |
| `TP_ENSINO` | Tipo de ensino (Regular/Especial) | Contexto |
| `SG_UF_PROVA` | UF da prova | Agregação regional |

### PARTICIPANTES — trabalho reprodutivo (novas análises)
| Variável INEP | Descrição | Uso no projeto |
|---|---|---|
| `Q008` | Contrata empregado(a) doméstico(a) | Terceirização do cuidado |
| `Q005` | Nº de pessoas na residência | Carga de cuidado |
| `Q015` | Máquina de lavar roupa | Infraestrutura que reduz carga doméstica |
| `Q009` | Banheiro na residência | Infraestrutura básica |
| `TP_ESTADO_CIVIL` | Estado civil | Responsabilidade familiar |
| `TP_FAIXA_ETARIA` | Faixa etária | Fase de vida / responsabilidade |

### PARTICIPANTES — capital herdado (novas análises)
| Variável INEP | Descrição | Uso no projeto |
|---|---|---|
| `Q001`/`Q002` | Escolaridade do pai/mãe | Capital cultural herdado |
| `Q003`/`Q004` | Ocupação do pai/mãe | Classe de origem |

### RESULTADOS (desempenho)
| Variável INEP | Descrição | Uso no projeto |
|---|---|---|
| `TP_PRESENCA_*` | Presença nas provas (0=Faltou, 1=Presente, 2=Eliminado) | Análise de ausência |
| `NU_NOTA_*` | Notas por área | Variável dependente |
| `NU_NOTA_REDACAO` | Nota da redação | Variável dependente |
| `TP_DEPENDENCIA_ADM_ESC` | Tipo de escola (Federal/Estadual/Municipal/Privada) | Dimensão estrutural |
| `SG_UF_PROVA` | UF da prova | Agregação regional |

## Mudanças em relação ao formato 2024

| Aspecto | Antes (pré-2020) | 2025 |
|---------|-------------------|------|
| Estrutura | Arquivo único | Dois arquivos separados |
| Junção individual | Possível | **Impossível** (LGPD) |
| Presença | 1/2/3 | 0/1/2 |
| Tipo de escola | `TP_ESCOLA` | `TP_DEPENDENCIA_ADM_ESC` |
| Renda | `Q006` | `Q007` |
| Análise | Individual | Ecológica (UF) |

## Limitações metodológicas

1. **Análise ecológica**: Correlações por UF não implicam relações individuais (falácia ecológica)
2. **Sem Cohen's d individual**: Impossível sem dados cruzados
3. **Tipo de escola com ~64% de "Não respondeu"**: `TP_DEPENDENCIA_ADM_ESC` é ausente para a maioria dos inscritos
4. **Gênero binário**: O questionário INEP não captura identidade de gênero
5. **Raça por autodeclaração**: Captura identidade, não determinação racial objetiva
6. **Multicolinearidade raça-renda**: `% de mulheres negras` e `renda média` têm correlação de −0.76 no nível UF — são teoricamente articuladas (nó de opressões), mas o modelo não separa efeitos "puros"
7. **"Não sei" nos indicadores de capital herdado**: Excluído dos indicadores sintéticos e dos gráficos (é ausência de informação, não classe de origem); 4.5% das mães e 12% dos pais têm "Não sei" na escolaridade/ocupação
8. **Kruskal-Wallis com n=9 por grupo**: Teste de tercis de ausência com 27 UFs (n=9 por grupo) — fragilidade estatística, direção consistente mas robustez limitada
9. **Escolaridade dos pais — categorias D e E quase idênticas**: INEP D = "completou 8ª/9º, não Médio" e E = "completou Médio, não Faculdade" — ambas mapeadas como "Médio completo" e "Médio completo (sem superior)" respetivamente

## Referências teóricas

- SAFFIOTI, Heleieth. *Gênero, patriarcado, violência*. São Paulo: Fundação Perseu Abramo, 2004.
- SAFFIOTI, Heleieth. *A mulher na sociedade de classes*. São Paulo: Expressão Popular, 2013.
- D'IGNAZIO, Catherine; KLEIN, Lauren F. *Data Feminism*. MIT Press, 2020.
- INEP. *Microdados ENEM 2025 — Leia-me e Documentos Técnicos*.