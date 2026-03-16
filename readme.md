# ⚖️ Edge AI Jurídico

> Classificação inteligente de documentos jurídicos com TensorFlow Lite —
> 90% de acurácia, 806 KB, 0.012 ms por inferência, sem internet, respeitando a LGPD.

**PIC — Projeto de Iniciação Científica · UNISSAU**
**Orientação:** Prof. Msc. Afonso Calábria
**Desenvolvedor:** Caio R.

---

## 📌 O que é este projeto?

Este projeto desenvolve um sistema de **Inteligência Artificial embarcada (Edge AI)** capaz de:

- **Classificar automaticamente** documentos jurídicos em 5 categorias
- **Extrair entidades jurídicas** como CPF, CNPJ, artigos de lei e tribunais
- **Calcular o risco LGPD** de cada documento analisado
- **Resumir automaticamente** o conteúdo de processos longos
- **Processar PDFs digitais e escaneados** com OCR automático
- **Gerar relatório PDF profissional** com todos os resultados

Tudo isso rodando **100% no dispositivo** — sem internet, sem servidor, sem enviar dados para a nuvem — respeitando integralmente a **Lei Geral de Proteção de Dados (Lei 13.709/2018)**.

---

## 🎯 Por que este projeto existe?

### O problema

Advogados, servidores de tribunais e escritórios jurídicos lidam diariamente com centenas de documentos: petições, acórdãos, contratos, decisões, textos de leis. A triagem manual desses documentos é:

- **Lenta** — um servidor pode levar horas para categorizar um lote de processos
- **Cara** — tempo profissional gasto em tarefa repetitiva
- **Propensa a erros** — fadiga e volume reduzem a precisão humana
- **Problemática para a LGPD** — enviar documentos para APIs externas (como ChatGPT) expõe dados pessoais sensíveis de partes processuais

### A solução

Um modelo de IA leve e otimizado que roda **diretamente no dispositivo do usuário**. Sem precisar de internet. Sem enviar nenhum dado para servidores externos. Classificando documentos em milissegundos.

### Por que Edge AI especificamente?

Edge AI significa rodar a inteligência artificial "na borda" — no próprio dispositivo, não na nuvem. As vantagens para o contexto jurídico são:

| Aspecto | IA na nuvem | Edge AI (este projeto) |
|---------|------------|----------------------|
| Privacidade | Dados saem do dispositivo | Dados nunca saem |
| Velocidade | Depende da internet | 0.012 ms por inferência |
| Custo | Por requisição | Zero após instalação |
| LGPD | Risco de violação | Conforme por design |
| Disponibilidade | Requer conexão | Funciona offline |

---

## ✅ Resultados obtidos

### Acurácia e desempenho

| Métrica | Valor |
|---------|-------|
| Acurácia geral | **90.0%** |
| LGPD (F1-score) | **0.97** |
| Contrato (F1-score) | **0.91** |
| Acórdão (F1-score) | **0.93** |
| Petição (F1-score) | **0.84** |
| Latência por inferência | **0.012 ms** |
| Throughput | **83.000+ inferências/segundo** |

### Compressão do modelo (Edge AI)

| Modelo | Tamanho | Redução |
|--------|---------|---------|
| Keras float32 (treino) | 9.549 KB | — |
| TFLite base | 3.166 KB | 67% |
| **TFLite INT8 (deploy)** | **806 KB** | **92%** |

### Comparação com baselines

| Modelo | Acurácia | Latência | Tamanho | Edge? |
|--------|----------|----------|---------|-------|
| SVM Linear | 93.0% | 0.010 ms | 118 KB | ❌ |
| SVM RBF | 91.9% | 4.990 ms | 41.337 KB | ❌ |
| Regressão Logística | 88.7% | 0.010 ms | 118 KB | ❌ |
| Naive Bayes | 85.7% | 0.007 ms | 235 KB | ❌ |
| **Edge AI TFLite INT8** | **90.0%** | **0.012 ms** | **806 KB** | **✅** |

O SVM Linear tem 3pp a mais, mas não converte para TFLite e não roda em Android ou microcontrolador. O Edge AI entrega acurácia competitiva com viabilidade real de deployment.

---

## 🗂️ Classes de documentos detectados

| Classe | Descrição | Exemplos |
|--------|-----------|---------|
| 🔒 **LGPD** | Textos sobre proteção de dados | Lei 13.709/2018, políticas de privacidade |
| ⚖️ **Acórdão** | Decisões colegiadas de tribunais | STJ, STF, TRFs |
| 📄 **Contrato** | Instrumentos contratuais | Prestação de serviços, locação, compra e venda |
| 📋 **Petição** | Requerimentos judiciais | Petição inicial, embargos, mandado de segurança |
| 📚 **Outro** | Textos jurídicos gerais | CF/88, Código Civil, doutrina |

---

## 🏗️ Arquitetura completa do sistema

```
pic-edge-ai-juridico/
│
├── app.py                          ← Interface principal (Streamlit)
├── verificar_ambiente.py           ← Checagem do ambiente de desenvolvimento
├── README.md                       ← Este arquivo
│
├── src/                            ← Código-fonte de cada módulo
│   ├── coletar_dados.py            ← Dataset base com amostras curadas
│   ├── coletar_stj_stf.py          ← Coleta automática de fontes públicas
│   ├── adicionar_dados_manuais.py  ← Complemento manual de classes deficientes
│   ├── balancear_dataset.py        ← Balanceamento das classes
│   ├── preprocessar.py             ← Limpeza, TF-IDF e vetorização
│   ├── treinar_modelo.py           ← Treinamento da rede neural densa
│   ├── converter_tflite.py         ← Conversão e quantização INT8
│   ├── pruning_modelo.py           ← Poda de pesos por magnitude
│   ├── relatorio_metricas.py       ← Gráficos e métricas do modelo
│   ├── baseline_svm.py             ← Comparação com modelos clássicos
│   ├── ner_juridico.py             ← Extração de entidades jurídicas
│   ├── sumarizador.py              ← Sumarização extrativa edge
│   ├── ocr_juridico.py             ← OCR para PDFs escaneados
│   └── gerar_relatorio.py          ← Geração de relatório PDF
│
├── data/
│   ├── raw/
│   │   └── dataset_juridico.json   ← 2.343 amostras rotuladas
│   └── processed/
│       ├── X_train.npy             ← Matriz TF-IDF de treino
│       ├── X_test.npy              ← Matriz TF-IDF de teste
│       ├── y_train.npy             ← Labels de treino
│       ├── y_test.npy              ← Labels de teste
│       ├── vectorizer.pkl          ← TF-IDF treinado (serializado)
│       └── encoder.pkl             ← Codificador de classes (serializado)
│
└── models/
    ├── modelo_juridico.keras       ← Modelo completo Keras (treino)
    ├── pesos_base.weights.h5       ← Pesos isolados (compatibilidade)
    ├── grafico_treinamento.png     ← Curvas de acurácia e loss
    ├── relatorio/
    │   ├── relatorio_metricas.png      ← Relatório visual completo
    │   ├── comparacao_baseline.png     ← Gráfico comparativo
    │   └── comparacao_baseline.json    ← Dados da comparação
    └── tflite/
        ├── modelo_juridico.tflite          ← TFLite base
        ├── modelo_juridico_int8.tflite     ← TFLite INT8 ← deploy
        └── modelo_pruned_final.tflite      ← TFLite com pruning
```

---

## ⚙️ Como o projeto funciona — passo a passo

### Pipeline completo explicado

```
1. COLETA
   Documentos jurídicos públicos (Planalto, STJ, STF, curadoria manual)
   └── 2.343 amostras em 5 classes
           │
           ▼
2. PRÉ-PROCESSAMENTO
   Limpeza de texto → TF-IDF com bigramas → Matriz numérica
   └── Por que TF-IDF? Pondera palavras raras mais importantes
       "dados pessoais" vale mais que "o" ou "de"
           │
           ▼
3. TREINAMENTO
   Rede Neural Densa: Dense(256) → Dense(128) → Dense(64) → Softmax(5)
   └── Por que densa e não LSTM/BERT? Compatível com TFLite,
       leve, rápido, suficiente para classificação por vocabulário
           │
           ▼
4. OTIMIZAÇÃO EDGE
   Keras float32 → TFLite → Quantização INT8
   └── Por que INT8? Pesos de 32 bits → 8 bits = 4x menor,
       sem perda de acurácia para este domínio
           │
           ▼
5. DEPLOY
   Arquivo .tflite de 806 KB roda em qualquer dispositivo
   └── Android, Raspberry Pi, Windows, Linux, macOS
```

### Por que cada técnica foi escolhida

**TF-IDF em vez de Embedding ou BERT**
> Com 2.343 amostras, modelos baseados em embedding precisariam de muito mais dados para aprender representações úteis. O TF-IDF captura o vocabulário jurídico específico de cada classe (ex: "dados pessoais" → lgpd, "recurso especial" → acordao) de forma eficiente e interpretável.

**Quantização INT8 em vez de Float32**
> Pesos float32 usam 32 bits por valor. A quantização INT8 mapeia esses valores para 8 bits, reduzindo o tamanho em 75% com perda de acurácia de 0pp neste projeto. É a técnica padrão da indústria para deploy mobile.

**Pruning por magnitude**
> Remove os pesos com menor valor absoluto — aqueles que menos contribuem para a decisão. No projeto, o pruning funcionou como regularização, elevando a acurácia de 62% para 64% nas versões anteriores do dataset.

**NER por regex especializado em vez de spaCy**
> Para entidades jurídicas bem definidas (CPF, CNPJ, número de processo CNJ, artigos de lei), regex compilado é mais rápido e mais preciso que modelos de NER genéricos. Não requer GPU, não requer download de modelo, funciona offline.

**Sumarização extrativa em vez de gerativa**
> Sumarização extrativa seleciona as frases mais importantes do próprio texto — não gera texto novo. Para edge AI, isso é ideal: sem modelo de linguagem pesado, sem risco de alucinação, processamento em milissegundos.

---

## 🚀 Como instalar e executar

### Pré-requisitos obrigatórios

- **Python 3.11.x** — TensorFlow 2.15 não suporta Python 3.12+
- **Git**
- **VS Code** (recomendado)
- **Tesseract 5** — para OCR de PDFs escaneados

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/pic-edge-ai-juridico.git
cd pic-edge-ai-juridico
```

### 2. Criar ambiente virtual com Python 3.11

```bash
# Windows
py -3.11 -m venv venv
venv\Scripts\activate

# Linux/macOS
python3.11 -m venv venv
source venv/bin/activate
```

> **Por que ambiente virtual?** Isola as dependências do projeto das do sistema. Evita conflitos de versão — especialmente importante porque TF 2.15 exige numpy < 2.0.

### 3. Instalar dependências

```bash
pip install --upgrade pip
pip install "numpy==1.26.4" tensorflow==2.15.0
pip install scikit-learn==1.4.2 pandas matplotlib tqdm
pip install streamlit pdfplumber pytesseract pdf2image Pillow
pip install reportlab requests beautifulsoup4 lxml
```

> **Por que numpy==1.26.4?** TF 2.15 foi compilado com NumPy 1.x. NumPy 2.x quebra a compatibilidade binária e impede o TensorFlow de carregar.

### 4. Instalar Tesseract (OCR)

**Windows:**
1. Baixe o instalador em: https://github.com/UB-Mannheim/tesseract/wiki
2. Instale em `C:\Program Files\Tesseract-OCR\`
3. Durante a instalação, marque o pacote de idioma **Portuguese**
4. Adicione ao PATH ou configure em `src/ocr_juridico.py`

**Linux:**
```bash
sudo apt install tesseract-ocr tesseract-ocr-por
```

### 5. Verificar o ambiente

```bash
python verificar_ambiente.py
```

Saída esperada:
```
TensorFlow:   2.15.0  ✅
Scikit-learn: 1.4.2   ✅
NumPy:        1.26.4  ✅
Pandas:       x.x.x   ✅
Ambiente pronto!
```

---

## 🔄 Reproduzir o pipeline completo

Execute os scripts na ordem abaixo. Cada um depende do anterior.

### Passo 1 — Criar o dataset base

```bash
python src/coletar_dados.py
```

**O que faz:** Cria o arquivo `data/raw/dataset_juridico.json` com 225 amostras iniciais
curadas manualmente em 5 classes jurídicas.

**Por que é necessário:** O modelo precisa de exemplos rotulados para aprender.
Sem dados, não há treinamento.

---

### Passo 2 — Expandir com fontes públicas

```bash
python src/coletar_stj_stf.py
```

**O que faz:** Acessa o Planalto (LGPD, CF/88, CPC) e tenta as APIs do STJ e STF
para coletar trechos de documentos reais. Adiciona ao dataset existente sem duplicar.

**Por que é necessário:** 225 amostras é insuficiente para um artigo acadêmico.
O mínimo para resultados publicáveis é 100+ por classe.

**Fontes utilizadas:**
- `planalto.gov.br` — Lei 13.709/2018 (LGPD), CF/88, CPC/2015
- `jurisprudencia.stj.jus.br` — ementas de acórdãos (quando disponível)
- `jurisprudencia.stf.jus.br` — ementas de decisões (quando disponível)

---

### Passo 3 — Balancear o dataset

```bash
python src/balancear_dataset.py
python src/adicionar_dados_manuais.py
```

**O que faz:** Identifica classes com poucas amostras e as complementa.
O `balancear_dataset.py` tenta fontes alternativas; o `adicionar_dados_manuais.py`
usa curadoria manual para garantir que `acordao` e `contrato` atinjam a meta.

**Por que é necessário:** Um dataset desbalanceado (ex: 1000 amostras de `outro`
e 45 de `acordao`) faz o modelo aprender a ignorar as classes pequenas.
O balanceamento é requisito para métricas confiáveis.

---

### Passo 4 — Pré-processar os dados

```bash
python src/preprocessar.py
```

**O que faz:**
1. Carrega o dataset JSON
2. Limpa o texto (minúsculas, remove pontuação)
3. Aplica TF-IDF com 3.000 features e bigramas
4. Divide em treino (80%) e teste (20%) com estratificação
5. Salva as matrizes `.npy` e os objetos `vectorizer.pkl` e `encoder.pkl`

**Por que TF-IDF com bigramas?**
Bigramas como "dados pessoais", "recurso especial" e "danos morais" são
marcadores muito mais informativos que palavras isoladas. O TF-IDF pondera
essas expressões pela sua raridade no corpus — termos que aparecem em
poucas classes recebem mais peso.

---

### Passo 5 — Treinar o modelo

```bash
python src/treinar_modelo.py
```

**O que faz:** Treina uma rede neural densa sobre as features TF-IDF.

**Arquitetura:**
```
Input (3.000 features TF-IDF)
    └── Dense(256, relu) + BatchNorm + Dropout(0.4)
    └── Dense(128, relu) + BatchNorm + Dropout(0.3)
    └── Dense(64, relu) + Dropout(0.2)
    └── Dense(5, softmax)  ← 5 classes
```

**Por que essa arquitetura?**
- `BatchNormalization` estabiliza o treino e permite learning rate maior
- `Dropout` previne overfitting (memorizar em vez de generalizar)
- `EarlyStopping` para automaticamente quando a validação para de melhorar
- `softmax` na saída converte scores em probabilidades que somam 1

---

### Passo 6 — Converter para TFLite

```bash
python src/converter_tflite.py
```

**O que faz:**
1. Carrega o modelo Keras treinado
2. Converte para formato TFLite (remove operações de treino)
3. Aplica quantização INT8 usando um dataset representativo
4. Salva o modelo otimizado em `models/tflite/`
5. Mede latência e compara tamanhos

**O que é quantização INT8?**
Durante o treino, os pesos são números float32 (32 bits de precisão).
A quantização mapeia esses valores para int8 (8 bits), usando uma escala
de calibração calculada a partir de dados reais. Resultado: modelo 4x menor,
sem perda de acurácia perceptível para classificação de texto.

---

### Passo 7 — Pruning (opcional, recomendado para artigo)

```bash
python src/pruning_modelo.py
```

**O que faz:** Aplica poda de pesos por magnitude em 4 níveis de esparsidade
(30%, 50%, 70%, 90%) e encontra o melhor trade-off acurácia × tamanho.

**O que é pruning por magnitude?**
Pesos com valor absoluto pequeno contribuem pouco para a decisão final.
O pruning os zera, criando um modelo "esparso". Após a quantização, zeros
comprimem melhor. No projeto, o pruning funcionou principalmente como
regularização, melhorando a acurácia sem reduzir o tamanho (pois a
quantização INT8 já comprime maximamente).

---

### Passo 8 — Gerar relatório de métricas

```bash
python src/relatorio_metricas.py
```

**O que faz:** Gera o gráfico `models/relatorio/relatorio_metricas.png` com:
- Matriz de confusão
- Comparação de tamanho (Keras vs TFLite vs INT8)
- Comparação de latência
- F1-score por classe
- Tamanho relativo ao original
- Tabela resumo executivo

---

### Passo 9 — Comparação com baselines

```bash
python src/baseline_svm.py
```

**O que faz:** Treina 4 modelos clássicos de ML (SVM Linear, SVM RBF,
Regressão Logística, Naive Bayes) e compara com o Edge AI em acurácia,
latência e tamanho. Salva gráfico e JSON com os resultados.

**Por que comparar com baselines?**
Requisito acadêmico — uma banca sempre pergunta: "por que não usou SVM?"
A comparação mostra que o Edge AI é competitivo em acurácia e superior
em viabilidade de deployment.

---

### Passo 10 — Abrir a interface

```bash
streamlit run app.py
```

Acesse: `http://localhost:8501`

---

## 🖥️ Interface — guia de uso

### Aba "Carregar PDF"

1. Arraste ou selecione qualquer PDF jurídico
2. Escolha o modo: **Documento completo** ou **Página por página**
3. Clique em **Analisar PDF**

O sistema detecta automaticamente se o PDF é digital (extrai texto direto)
ou escaneado (aplica OCR com Tesseract). O badge "📄 PDF digital" ou
"📷 OCR aplicado" indica qual método foi usado.

**Modo Documento completo:** une todo o texto e classifica o documento inteiro.
Ideal para contratos, petições e acórdãos homogêneos.

**Modo Página por página:** classifica cada página individualmente e mostra
a distribuição de classes. Ideal para processos longos com múltiplos documentos.

### Aba "Digitar texto"

1. Clique em um dos 5 botões de exemplo rápido, ou cole seu texto
2. Clique em **Classificar, resumir e extrair entidades**

### O que aparece no resultado

**Classificação:** classe detectada, porcentagem de confiança, barras de
probabilidade para todas as 5 classes.

**Resumo automático:** slider para controlar o número de frases (2–8).
O algoritmo seleciona as frases mais "centrais" do documento usando
similaridade de cosseno entre vetores TF-IDF.

**NER Jurídico:** todas as entidades extraídas organizadas por tipo.
Entidades marcadas com 🔒 são dados pessoais relevantes para LGPD.

**Score LGPD:** de 0 a 100, indica o risco de violação de privacidade
no documento. Calculado pela presença de dados pessoais sensíveis (CPF, CNPJ).

**Botão de download:** gera um relatório PDF profissional de 2 páginas
com todas as informações acima, pronto para arquivamento.

---

## 🔍 Módulos — o que cada arquivo faz

### `src/ner_juridico.py` — Extração de Entidades

Extrai automaticamente 11 tipos de entidades usando expressões regulares
especializadas para o domínio jurídico brasileiro:

| Entidade | Exemplo | LGPD |
|----------|---------|------|
| CPF | 123.456.789-09 | 🔒 |
| CNPJ | 12.345.678/0001-99 | 🔒 |
| OAB | OAB/SP 98765 | — |
| PROCESSO | 0001234-56.2024.8.26.0100 | — |
| ARTIGO_LEI | artigo 186, inciso III | — |
| LEI | Lei 13.709/2018 | — |
| TRIBUNAL | STJ, STF, TJSP | — |
| SUMULA | Súmula 7 do STJ | — |
| VALOR_MONETARIO | R$ 50.000,00 | — |
| DATA | 15 de março de 2024 | — |
| PRAZO | 15 dias | — |

**Por que regex e não spaCy/BERT-NER?**
Entidades jurídicas têm formato muito bem definido (CPF tem 11 dígitos,
número CNJ tem padrão NNNNNNN-DD.AAAA.J.TT.OOOO). Regex é mais preciso,
mais rápido e não requer GPU ou download de modelo.

---

### `src/sumarizador.py` — Sumarização Extrativa

Implementa o algoritmo **TextRank** simplificado com bônus jurídico:

1. Segmenta o texto em frases
2. Vetoriza cada frase com TF-IDF
3. Calcula a matriz de similaridade de cosseno entre todas as frases
4. O score de cada frase é a média das similaridades com as demais
   (frases mais "centrais" no documento são mais representativas)
5. Aplica bônus para frases com termos jurídicos importantes
   ("decide", "acórdão", "requer", "dados pessoais", etc.)
6. Retorna as N frases com maior score, na ordem original

**Por que extrativa e não gerativa?**
Sumarização gerativa (como ChatGPT) cria novo texto — pode alucinar,
distorcer fatos ou inventar referências legais. Sumarização extrativa
seleciona frases reais do documento, garantindo fidelidade total ao conteúdo.
Para documentos jurídicos, onde cada palavra tem peso legal, isso é essencial.

---

### `src/ocr_juridico.py` — OCR para PDFs Escaneados

Usa **Tesseract 5** com modelo de idioma português para extrair texto
de PDFs que são imagens digitalizadas.

**Fluxo:**
1. `pdf2image` converte cada página do PDF em imagem PNG a 300 DPI
2. `pytesseract` aplica OCR na imagem com configuração `--oem 3 --psm 6`
   (LSTM neural + bloco uniforme de texto)
3. O texto extraído segue o mesmo pipeline de classificação

**Por que 300 DPI?**
Abaixo de 200 DPI, o OCR comete erros em caracteres jurídicos com acento.
300 DPI é o padrão recomendado pelo Tesseract para documentos tipográficos.

**Detecção automática:**
A função `detectar_tipo_pdf()` extrai texto das 3 primeiras páginas com
`pdfplumber`. Se a média de caracteres por página for menor que 50,
o arquivo é classificado como escaneado e o OCR é acionado.

---

### `src/gerar_relatorio.py` — Relatório PDF

Usa **ReportLab** para gerar um relatório PDF profissional com:

1. **Cabeçalho** — título, data e hora de geração
2. **Informações do documento** — nome, caracteres extraídos, método de extração
3. **Classificação** — classe detectada com barra de probabilidade para cada classe
4. **Análise LGPD** — score de risco, número de dados pessoais detectados,
   tabela completa de entidades com flag de risco LGPD
5. **Trecho do texto** — primeiros 800 caracteres do documento analisado
6. **Ficha técnica do modelo** — arquitetura, tamanho, latência, conformidade

---

## 📊 Contexto acadêmico

### Hipótese de pesquisa

**H1:** Modelos de classificação de texto com quantização INT8 (TFLite)
mantêm acurácia equivalente ao modelo base (≤ 5pp de diferença) com
redução de ≥ 80% no tamanho, viabilizando classificação jurídica em
dispositivos edge sem envio de dados para servidores externos.

**Resultado:** H1 confirmada — 0pp de degradação com 92% de redução.

### Cronograma do PIC

| Período | Atividade |
|---------|-----------|
| SET–OUT | Revisão bibliográfica, levantamento teórico |
| OUT–NOV | Coleta de dados, seleção de modelos, implementação |
| NOV–DEZ | Otimização: quantização INT8, TFLite, métricas |
| JAN–FEV | Interface, relatórios, comparação com baselines |

### Referências principais

- **MobileNetV3** — Howard et al. (2019) — base para técnicas de compressão
- **Once For All** — Cai et al. (2020) — referência teórica de pruning
- **TensorFlow Lite** — Google (2023) — framework de deploy edge
- **Lei 13.709/2018** — LGPD — motivação do contexto jurídico
- **SAJ** — Softplan — sistema de destino para integração futura

---

## 🔭 Próximos passos (roadmap)

### Curto prazo
- [ ] Escrever artigo completo do PIC (introdução, metodologia, resultados, conclusão)
- [ ] Validação cruzada k-fold para resultados mais robustos
- [ ] Ampliar dataset para 500+ amostras por classe

### Médio prazo — Integração SAJ
O objetivo principal é conectar o modelo ao **SAJ (Sistema de Automação da Justiça)**
para varredura automática de processos:

```
SAJ (exportação XML/PDF)
        │
        ▼
Extrator de texto (pdfplumber / Tesseract OCR)
        │
        ▼
Pipeline Edge AI (classificação + NER + score LGPD)
        │
        ▼
Dashboard jurídico (triagem automática, alertas LGPD)
```

### Longo prazo
- [ ] Deploy em Android via TFLite Java API
- [ ] Deploy em Raspberry Pi para tribunais sem infraestrutura de TI
- [ ] Certificação de conformidade LGPD do pipeline completo

---

## 🛠️ Dependências

```
tensorflow==2.15.0
numpy==1.26.4
scikit-learn==1.4.2
pandas
matplotlib
streamlit
pdfplumber
pytesseract
pdf2image
Pillow
reportlab
requests
beautifulsoup4
lxml
tqdm
```

---

## ❓ Problemas comuns

**`ImportError: numpy.core._multiarray_umath failed to import`**
> NumPy 2.x foi instalado. Solução: `pip install "numpy==1.26.4" --force-reinstall`

**`tesseract is not installed or not in PATH`**
> Tesseract não está configurado. Edite a linha no `src/ocr_juridico.py`:
> `pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"`

**`TF_USE_LEGACY_KERAS / DLL load failed`**
> Conflito entre Keras 2 e Keras 3. Solução: `pip uninstall tf_keras tensorflow-model-optimization -y`
> e use apenas TensorFlow puro.

**`RecursionError: maximum recursion depth exceeded`**
> O `tensorflow-model-optimization` tem conflito com TF 2.15.
> Solução: `pip uninstall tensorflow-model-optimization -y`

---

## 📄 Licença

Projeto acadêmico de uso educacional.
Dados jurídicos utilizados são de domínio público (STJ, STF, Planalto, legislação federal).

---

<p align="center">
  Desenvolvido por <strong>Caio V.</strong> · Uninassau · 2026<br>
  Orientação: Prof. Msc. Afonso Calábria<br><br>
  <em>Edge AI · TensorFlow Lite · Direito Digital · LGPD · SAJ</em>
</p>