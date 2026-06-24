# Referências teóricas e metodológicas

## Referencial central

**SAFFIOTI, Heleieth I. B.**  
*Gênero, patriarcado, violência.* São Paulo: Fundação Perseu Abramo, 2004.  
→ Fundamento do conceito de nó de opressões. Capítulo 1 ("Conceituando gênero") e Capítulo 4 ("O nó") são centrais para justificar a unidade analítica dos grupos estruturais.

**SAFFIOTI, Heleieth I. B.**  
*A mulher na sociedade de classes: mito e realidade.* 3. ed. São Paulo: Expressão Popular, 2013.  
→ Articulação raça–gênero–classe no capitalismo dependente brasileiro. Referência para a análise regional.

## Metodologia de dados educacionais

**INEP.**  
*Microdados ENEM 2025 — Leia-me e Documentos Técnicos.* Brasília: INEP/MEC, 2026.  
→ Dicionário de variáveis, nota sobre anonimização LGPD, separação dos arquivos PARTICIPANTES e RESULTADOS.

**D'IGNAZIO, Catherine; KLEIN, Lauren F.**  
*Data Feminism.* Cambridge: MIT Press, 2020.  
→ Capítulo 4 ("What Gets Counted Counts") fundamenta a crítica às categorias binárias de gênero no instrumento INEP. Capítulo 1 ("The Power Chapter") para o posicionamento epistemológico do dashboard narrativo.

## Estatística e análise de desigualdade

**ROBINSON, W.S.**  
Ecological Correlations and the Behavior of Individuals.  
*American Sociological Review*, v. 15, n. 3, p. 351–357, 1950.  
→ Fundamentação da distinção entre correlações ecológicas (nível agregado) e individuais. Essencial para esta análise, dado que os dados de 2025+ não permitem junção individual.

**SUBRAMANIAN, S.V.; JONES, K.; KREUTER, F.**  
Multilevel Methods for Public Health Research.  
In: *Social Epidemiology*. 2. ed. Oxford: Oxford University Press, 2014.  
→ Alternativa metodológica para quando dados individuais não estão disponíveis: modelos multinível com variáveis contextuais.

**WOOLDRIDGE, Jeffrey M.**  
*Introductory Econometrics: A Modern Approach.* 6. ed. Mason: Cengage, 2015.  
→ Capítulo 7 para justificativa do uso de variáveis categóricas na regressão ecológica.

## Sobre raça/cor no Brasil

**OSÓRIO, Rafael Guerreiro.**  
O sistema classificatório de cor ou raça do IBGE.  
*Texto para Discussão IPEA*, n. 996, 2003.  
→ Discussão sobre autodeclaração vs. heteroclassificação; limitações analíticas das categorias Preta/Parda.

**PAIXÃO, Marcelo (org.).**  
*Relatório Anual das Desigualdades Raciais no Brasil 2009–2010.*  
Rio de Janeiro: Garamond/LAESER/UFRJ, 2010.  
→ Precedente metodológico para agrupamento Preta+Parda como "negra".

## Educação e desigualdade no Brasil

**RIBEIRO, Carlos Antonio Costa.**  
*Estrutura de classe e mobilidade social no Brasil.* Bauru: EDUSC, 2007.

**FERRARO, Alceu Ravanello.**  
Direito à educação no Brasil e dívida educacional: e se o povo cobrasse?  
*Educação e Pesquisa*, São Paulo, v. 34, n. 2, p. 273–289, 2008.

---

## Notas metodológicas sobre as variáveis

### Por que agrupar Preta + Parda como "Negra"?

A distinção IBGE entre Preta e Parda é analiticamente problemática para o estudo do nó de opressões. Ambas as categorias partilham posição estrutural semelhante no sistema patriarcal-racista-capitalista brasileiro — o que a literatura especializada (Osório, 2003; Paixão, 2010) e os dados do IBGE consistentemente confirmam. O agrupamento como "negra" segue a autoidentificação do movimento negro e da tradição acadêmica crítica brasileira. Transparência: os microdados permitem desfazer o agrupamento; qualquer análise pode ser replicada com as categorias originais.

### Por que gênero binário?

O questionário INEP oferece apenas M/F. Isso é uma limitação política do instrumento — não da análise. O projeto documenta explicitamente essa ausência como dado: pessoas trans e não-binárias são invisibilizadas pela base. Recomendação metodológica: sinalizar essa limitação no dashboard e no README como chamada para mudança no instrumento, não como omissão neutra.

### Por que análise ecológica (nível UF)?

A partir de 2020, o INEP dividiu os microdados em PARTICIPANTES (demografia) e RESULTADOS (notas), sem chave de junção individual, por exigência da LGPD. Isso impede a análise individual (Cohen's d, OLS com grupo_no como variável individual). A análise ecológica (nível UF) permite identificar associações entre composição demográfica regional e desempenho regional, mas está sujeita à **falácia ecológica**: correlações agregadas não implicam relações individuais.

### Encoding de presença (mudança 2025)

Em 2024 e anteriores, TP_PRESENCA_* usava: 1=presente, 2=ausente, 3=eliminado.  
Em 2025, o encoding mudou para: 0=Faltou, 1=Presente, 2=Eliminado.

### Tipo de escola (mudança 2025)

Em 2024 e anteriores, TP_ESCOLA usava: 1=Não respondeu, 2=Pública, 3=Privada.  
Em 2025, TP_DEPENDENCIA_ADM_ESC usa: 1=Federal, 2=Estadual, 3=Municipal, 4=Privada (NaN=Não respondeu). Agrupamos Federal+Estadual+Municipal como "Pública".

### Renda (mudança 2025)

Em 2024, a renda era Q006 (A–Q). Em 2025, Q006 passou a ser "Você possui renda?" (A=Não, B=Sim) e Q007 é a renda familiar mensal (A–Q), com faixas ajustadas ao salário mínimo de 2025 (R$1.518,00).