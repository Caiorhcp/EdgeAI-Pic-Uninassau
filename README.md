# Edge AI Jurídico

[![CI](https://github.com/Caiorhcp/EdgeAI-Pic-Uninassau/actions/workflows/ci.yml/badge.svg)](https://github.com/Caiorhcp/EdgeAI-Pic-Uninassau/actions/workflows/ci.yml)

**Demo: https://edge-ai-juridico.vercel.app**

Classifica peças processuais, encontra dados pessoais (LGPD) e resume documentos jurídicos **dentro do navegador**. O PDF nunca sai do dispositivo: leitura, OCR, classificação, extração de entidades e anonimização rodam no cliente. O modelo foi treinado com páginas reais de processos do STF rotuladas por especialistas do tribunal.

Projeto de Iniciação Científica (PIC), UNINASSAU. Desenvolvimento: Caio R. · Orientação: Prof. Msc. Afonso Calábria.

## O que faz

- **Tipo de cada página**: Acórdão, Agravo em RE, Despacho, Petição de RE, Sentença ou Outros. Páginas seguidas do mesmo tipo viram uma peça (ex.: "pp. 1–2 · Petição de RE, p. 3 · Despacho").
- **Dados pessoais**: CPF e CNPJ validados pelo dígito verificador, e-mail, telefone, endereço, RG, CNH, PIS. Gera uma nota de exposição de 0 a 100 e baixa o **texto anonimizado** (`[CPF]`, `[EMAIL]`…).
- **Referências jurídicas**: número CNJ, leis, artigos, súmulas, tribunais, datas e valores.
- **Resumo extrativo**: frases mais centrais do texto (TF-IDF + similaridade), com peso maior para trechos de dispositivo e pedido.
- **PDF escaneado**: OCR automático em português com tesseract.js, servido pelo próprio site (sem CDN).
- **Consulta ao Datajud (CNJ)**: metadados públicos do processo (classe, assuntos, órgão julgador, movimentações). É a única parte que usa servidor, e só o número do processo é enviado.

## Arquitetura

```mermaid
flowchart LR
  subgraph Navegador
    PDF[PDF ou texto] --> R[pdf.js / tesseract.js]
    R --> C[Classificador TF-IDF + regressão logística<br/>model.json, 1,4 MB gzip]
    R --> N[NER por regex<br/>+ validação CPF/CNPJ]
    R --> S[Resumo extrativo]
    N --> A[Anonimização]
  end
  subgraph Servidor["Vercel (rota /api/processo)"]
    D[Valida número CNJ<br/>e escolhe o tribunal] --> DJ[(API Pública Datajud)]
  end
  N -- número CNJ --> D
  subgraph Treino["ml/ (Python, offline)"]
    V[(VICTOR / STF)] --> T[train.py] --> C
  end
```

O modelo é treinado em Python e exportado como JSON (termos, IDF, pesos). A inferência foi reescrita em TypeScript puro, sem biblioteca de ML no navegador; um teste garante que as probabilidades do TypeScript são as mesmas do scikit-learn.

## Resultados

Conjunto de teste do **VICTOR Small** ([Luz de Araujo et al., LREC 2020](https://aclanthology.org/2020.lrec-1.181/)): 95.526 páginas de recursos extraordinários do STF, mesma divisão treino/validação/teste do artigo original, F1 por página.

| Modelo | F1 macro | F1 ponderado |
|---|---|---|
| **Este projeto**: TF-IDF uni+bigramas (30 mil termos) + regressão logística | **78,2** | **94,7** |
| SVM linear (artigo original) | 76,3 | 94,3 |
| CNN (artigo original) | 75,8 | 94,7 |

F1 por classe: Acórdão 88,4 · Sentença 81,1 · Petição de RE 74,6 · Despacho 71,2 · Agravo em RE 56,8 · Outros 97,4.

**Prior uniforme no site.** No VICTOR, 89% das páginas são "Outros" (certidões, procurações), porque cada processo é inteiro. No site, o usuário envia uma peça por vez, então a inferência divide pela frequência de cada classe no treino, o que equivale a supor classes igualmente prováveis. Isso troca F1 macro por recall:

| Cenário | Recall médio por classe | F1 macro |
|---|---|---|
| Distribuição do STF (benchmark) | 74,2 | 78,2 |
| Classes igualmente prováveis (site) | **86,8** | 57,6 |

Todos os números vêm de [`ml/metrics.json`](ml/metrics.json), gerado por `ml/train.py`.

## Decisões técnicas

- **Dataset real em vez de rótulos por fonte.** A versão 1 rotulava artigos de lei pela lei de origem (CLT virava "petição"), e o modelo aprendia a reconhecer a fonte, não o tipo de documento. A versão 2 usa o VICTOR, rotulado por especialistas do STF, e compara com o baseline publicado.
- **Regressão logística em vez de rede neural.** Bateu o SVM e a CNN do artigo, gera probabilidades calibradas e cabe em 1,4 MB. A versão 1 usava TensorFlow 2.15, que prendia o projeto ao Python 3.11.
- **Inferência no navegador.** A promessa de privacidade (LGPD) fica verdadeira no produto publicado: não existe servidor que receba o documento.
- **Datajud no servidor.** A API do CNJ exige chave e não aceita chamadas do navegador. A rota valida o dígito verificador do número CNJ (ISO 7064) e escolhe o índice pelo segmento de Justiça (Resolução CNJ 65/2008). Não há dados de exemplo: se a consulta falha, a tela diz o motivo.

## Como rodar

**Site** (Node 24):

```bash
cd web
npm install
echo "DATAJUD_API_KEY=<chave pública em datajud-wiki.cnj.jus.br/api-publica/acesso>" > .env.local
npm run dev        # http://localhost:3000
npm test           # 43 testes (Vitest)
```

**Treino** (Python 3.12 com [uv](https://docs.astral.sh/uv/)): baixe os três `.parquet` de [`Luciano/victor_lrec_2020_small`](https://huggingface.co/datasets/Luciano/victor_lrec_2020_small) para `data/victor/` (`train.parquet`, `validation.parquet`, `test.parquet`).

```bash
cd ml
uv run --python 3.12 python train.py   # ~6 min; gera web/public/model.json e ml/metrics.json
uv run --python 3.12 pytest
```

## Estrutura

```
ml/
  train.py           treino, avaliação, exportação do modelo e checagem de paridade
  metrics.json       métricas do conjunto de teste
web/
  src/app/           página, analisador, consulta ao Datajud e rota /api/processo
  src/lib/           classifier, ner, summarizer, pdf, cnj, datajud (+ testes)
  public/model.json  modelo exportado
```

## Limitações

- "Agravo em RE" é a classe mais difícil (F1 de 56,8): é confundida com petição de RE, como no artigo original.
- Uma página só com a qualificação das partes se parece com uma procuração e tende a sair como "Outros".
- O modelo conhece as peças típicas de um recurso extraordinário. Contratos, pareceres e documentos de outras áreas não fazem parte das classes.
- A análise de dados pessoais usa regras e não substitui uma avaliação jurídica de conformidade com a LGPD.
- O Datajud leva de 30 a 50 segundos por consulta, tem limite de requisições e não inclui o STF.

## Dados e licença

O VICTOR é distribuído sob CC BY-NC (uso não comercial); por isso os dados não estão neste repositório. Cite o trabalho original:

> Luz de Araujo, P. H.; de Campos, T. E.; Braz, F. A.; da Silva, N. C. *VICTOR: a Dataset for Brazilian Legal Documents Classification*. LREC 2020, p. 1449–1458.

A versão 1 do projeto (Streamlit + TensorFlow Lite) está no histórico da branch `main`.
