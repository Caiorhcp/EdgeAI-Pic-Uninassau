# ⚖️ Edge AI Jurídico

> **Classificação inteligente de documentos jurídicos com TensorFlow Lite integrado a uma Arquitetura Limpa (DDD)** — 90% de acurácia, modelo de 806 KB, 0.012 ms por inferência. Execução offline, respeitando rigorosamente a LGPD.

**PIC — Projeto de Iniciação Científica · UNISSAU**  
**Orientação:** Prof. Msc. Afonso Calábria  
**Desenvolvedor:** Caio R.  

---

## 📌 O que é este projeto?

Este projeto desenvolve um sistema de **Inteligência Artificial embarcada (Edge AI)** focado no domínio jurídico, capaz de:

- **Classificar automaticamente** documentos em 5 categorias principais (LGPD, Acórdão, Contrato, Petição, Outros).
- **Extrair entidades jurídicas (NER)** como CPF, CNPJ, processos, súmulas e tribunais.
- **Analisar risco LGPD** detectando presença e volume de dados pessoais sensíveis.
- **Sumarizar processos longos** através de métodos extrativos rápidos.
- **Processar PDFs digitais e escaneados**, empregando OCR automaticamente quando necessário.
- **Gerar relatórios profissionais em PDF** com a auditoria completa da análise.

Tudo isso roda **100% local no dispositivo** — sem necessidade de internet, garantindo que os dados não sejam enviados para servidores de terceiros ou nuvem, um pilar fundamental da **Lei Geral de Proteção de Dados (Lei 13.709/2018)**.

---

## 🎯 Por que este projeto existe?

### O Problema
No ecossistema jurídico (escritórios, tribunais, órgãos públicos), lida-se diariamente com montanhas de papéis e PDFs. A triagem manual é:
- **Lenta e Cara**: Tarefas repetitivas que tomam horas de profissionais altamente qualificados.
- **Suscetível a Fadiga**: O volume colossal prejudica a precisão humana.
- **Insegura (Cloud)**: Utilizar LLMs em nuvem (como ChatGPT) expõe dados sigilosos, violando diretrizes de privacidade e LGPD.

### A Solução: Edge AI Paradigm
A Inteligência Artificial "na borda" (Edge AI) traz o cérebro para perto da fonte dos dados:
- **Privacidade Absoluta**: Os dados nunca saem do computador do usuário.
- **Altíssima Velocidade**: A latência de rede é eliminada (inferência em 0.012 milissegundos).
- **Independência**: Funciona totalmente offline.

| Característica | IA em Nuvem Promíscua | Edge AI (Este Projeto) |
|---|---|---|
| **Privacidade** | Risco de vazamento de dados | Isolamento local total |
| **Custo por análise** | Baseado no consumo de tokens | Virtualmente Zero |
| **Velocidade** | Depende do servidor e da internet | Processamento instantâneo |
| **Disponibilidade** | Sujeita a quedas de serviço | Sempre disponível (offline) |

---

## 🏛️ Arquitetura de Software: Domain-Driven Design (DDD) & Clean Architecture

Para que o sistema seja sustentável e escalável, ele foi totalmente refatorado utilizando princípios de **Arquitetura Limpa** e **Domain-Driven Design (DDD)**. Isso separou o "cérebro matemático" das lógicas de negócio e da interface.

- **`src/domain/` (Coração do Sistema)**: Contém o modelo do negócio puro. *Entities* (como `Documento`), *Value Objects* (`ResultadoClassificacao`, `ClasseDocumento`), e *Interfaces/Ports* (`IExtratorRepository`, `IClassificadorRepository`). Não conhece ML, Web ou Banco de Dados.
- **`src/application/` (Orquestração)**: Contém os *Use Cases* (ex: `AnalisarDocumentoUseCase`) e os *DTOs* de entrada e saída. Cordena as ações: pede para extrair o texto, classifica, analisa LGPD e sumariza.
- **`src/infrastructure/` (Implementações e Adapters)**: As conexões com o mundo externo. É aqui que moram as bibliotecas pesadas de IA e os motores de PDF.
  - **`ml/tflite_classificador.py`**: Adapter que usa TensorFlow Lite.
  - **`nlp/ner_juridico.py` & `sumarizador.py`**: Regexes e processamento extrativo.
  - **`pdf/` & `ocr/`**: `pdfplumber` e `Tesseract OCR`.
  - **`report/`**: Gerador de relatório em `ReportLab`.
- **`src/shared/`**: Configurações transversais (variáveis de ambiente, caminhos físicos, Exceções Globais e Observabilidade / Logging).
- **`app.py`**: A camada de Apresentação (UI) em Streamlit que apenas injeta dependências e chama o fluxo da `application`.

---

## 🧠 Machine Learning: Como os Pesos (Weights) Foram Feitos

A IA não utiliza um LLM gigantesco, mas sim uma rede neural densa clássica extremamente polida para o domínio jurídico. 

O porte de criação e compressão desse modelo é o grande destaque acadêmico do projeto:

### 1. Preparação e Vetorização (TF-IDF)
- Os documentos possuem linguagem rebuscada. Utilizar Embeddings pesados exigiria vocabulários massivos de gigabytes. 
- Optamos pelo **TF-IDF + Bigramas** com 3.000 features. O vetorizador (`vectorizer.pkl`) aprendeu que termos como `"dados pessoais"` e `"recurso especial"` carregam altíssimo peso. Ele converte os textos em uma matriz numérica flutuante que alimenta a IA.
- O `encoder.pkl` mapeia essas abstrações numéricas para o vocabulário (Acordão, Contrato, etc).

### 2. Rede Neural Densa (Keras)
- Uma arquitetura em camadas densas (256 → 128 → 64 neurônios), com camadas de **Dropout** (para evitar o overfitting e memorização cega dos dados de treinamento) e **BatchNormalization** (para estabilizar o gradiente).
- Esse modelo float32 treinado atingiu 90% de acurácia com um tamanho em disco de **~9,5 MB** (`modelo_juridico.keras`).

### 3. Edge Optimization: Quantização INT8
- Dispositivos locais processam números inteiros muito mais rápido que pontos flutuantes. 
- Usamos a técnica de **Post-Training Quantization** do TFLite para reduzir os pesos da rede de 32-bits Float para 8-bits Inteiros.
- **Resultado da Quantização**: O modelo caiu de 9,5 MB para incríveis **806 KB** (`modelo_juridico_int8.tflite`). Houve zero perda significativa na métrica de acurácia para este dataset.

### 4. Pruning por Magnitude (Poda)
- Técnicas avançadas removeram das camadas conexões próximas de `0` (pesos muito pequenos). A técnica atuou mais como uma regularização, melhorando a capacidade de generalização e facilitando o carregamento rápido do disco para a memória RAM.

---

## 🛠️ O Porquê de Cada Tecnologia

- **Python 3.11**: Linguagem mandatória devido ao ecossistema forte em dados, mas travado nessa versão específica pois o TensorFlow 2.15 possui incompatibilidades conhecidas nativas com Python 3.12+.
- **TensorFlow Lite (TFLite)**: Permite executar modelos sem depender de clusters ou instalação gigantesca do CUDA e drivers gráficos brutais. Extrai exatamente o motor de inferência (que é minúsculo).
- **Scikit-Learn (TF-IDF)**: Melhor custo-benefício para processamento tabular e textual leve. Extremamente consolidado na indústria.
- **Tesseract (PyTesseract)**: O motor OCR open-source mais robusto. Usado para "ler imagens" de PDFs escaneados quando o `pdfplumber` identifica que o arquivo é chumbo/rasterizado.
- **ReportLab**: Motor PDF programático focado na geração determinística do layout dos laudos do relatório da IA.
- **Streamlit**: Permite criar a aplicação em HTML5/CSS/JS sem precisar codificar explicitamente esses artefatos textuais. É declarativo, puramente Python, integrando muito bem com o ML.
- **Pyright & Tipagem Estática (Type Hints)**: O projeto refatorado abraça verificações de tipo rigorosas pelo Pyright. Isso blinda o fluxo de Clean Architecture contra bugs sutis em tempo de execução.
- **Pytest**: Validação automatizada para atestar que Use Cases, Entidades de Domínio e Extratores funcionem perfeitamente a cada nova inserção de código.

---

## ✅ Resultados Alcançados (Benchmarks)

| Métrica Acadêmica | Valor Obtido |
|-------------------|--------------|
| Acurácia Geral | **90.0%** |
| F1-Score do Contrato | **0.91** |
| F1-Score do Acórdão | **0.93** |
| Tempo de Inferência (Intel Core local) | **0.012 ms** (12 microssegundos) |
| Tamanho do Modelo Final | **806 KB** |

**Por que não usar SVM (Support Vector Machines)?**  
Nós comparamos (`baseline_svm.py`). O SVM Linear obteve até 93% de acurácia localmente. No entanto, o SVM RBF demora milissegundos inteiros a mais e *nenhum deles* pode ser convertido de forma eficiente em TFLite para exportação portátil a dispositivos Android/microcontroladores nativos. A Rede Neural Keras converte nativamente para o Tensor runtime móvel mantendo os 90% garantidos!

---

## 🗂️ As Classes Documentais (Categorias)

| Categoria | Descrição | Exemplo Legal |
|-----------|-----------|---------------|
| 🔒 **LGPD** | Políticas, dados ou infrações de privacidade | Lei 13.709/2018 |
| ⚖️ **Acórdão** | Decisões de Tribunais | Apelação Cível TJSP |
| 📄 **Contrato** | Prestação de serviços ou avenças materiais | Compra e Venda, Locação |
| 📋 **Petição** | Requerimentos processuais do Advogado | Petição Inicial |
| 📚 **Outros** | Letra fria da Lei (textos normativos) | Artigo ou Constituição |

---

## 🚀 Passo a Passo: Instalação, Treino e Uso

Siga isso na ordem caso queira construir o sistema do zero ou fazer engenharia reversa das partes de IA:

### 1. Requisitos
- **Python 3.11** (⚠️ Estritamente recomendado focar entre 3.10 e 3.11).
- **Git** e **Tesseract-OCR** instalado no sistema operacional (No Windows, extraia no diretório padrão `C:\Program Files\Tesseract-OCR\`).

### 2. Clonando e Setup Virtual
```bash
git clone https://github.com/SeuUsuario/pic-edge-ai-juridico.git
cd pic-edge-ai-juridico

# Windows
py -3.11 -m venv venv
venv\Scripts\activate

# Linux (Ubuntu)
python3.11 -m venv venv
source venv/bin/activate
```

Instale as dependências. Nota importante: O `numpy<2.0` (como 1.26.4) é amarrado para evitar que o tensor se quebre na inicialização das matrizes de tipo C:
```bash
pip install -r requirements.txt
```
*(ou instale listado via `pip install numpy==1.26.4 tensorflow==2.15.0 scikit-learn==1.4.2 ...`)*

### 3. Pipeline Completo: Concepção, Treino e Validação (Novo!)
Criamos um orquestrador unificado para rodar todo o pipeline de ponta a ponta com 11 passos organizados. Ele possui uma interface no terminal interativa e permite execução automática, passo a passo ou sob demanda:
```bash
python rodar_tudo.py
```

Esse novo script centraliza e gerencia:
- **Passos 01 a 04**: Coleta de dados (STJ, STF, Planalto, Dataset Sintético e complementos manuais) com balanceamento das 5 classes através de Data Augmentation.
- **Passo 05**: Pré-processamento e Vetorização estruturada em TF-IDF.
- **Passos 06 a 08**: Treino da Rede Neural Densa (`Keras`), Conversão para TFLite (INT8), e Pruning (atingindo impressionantes ~806KB de peso final).
- **Passos 09 a 11**: Geração de Relatórios de Métricas, Comparação analítica contra modelos clássicos Baselines (SVM, Regressão Logística, Naive Bayes), e validação cruzada robusta (*k-fold*).

Gráficos e matrizes são exportados para `models/relatorio/`. E o próprio orquestrador `rodar_tudo.py` oferece subir a UI logo após a conclusão do ciclo!

### 4. Ligando a Aplicação Edge AI e Frontend Streamlit
A interface gráfica é centralizada e inteiramente baseada em injeção de dependências para respeitar toda a Arquitetura DDD.
Caso não tenha iniciado pelo `rodar_tudo.py` e possua os pesos prontos em `models/tflite/`, inicie via:
```bash
streamlit run app.py
```
**Para visualizar no Navegador**, acesse `http://localhost:8501`.

---

## 🔍 Sobre os Módulos Não-Inteligentes (Regras de Negócio Otimizadas)

Poderíamos utilizar LLMs para extrair tudo. Mas evitamos pelo alto consumo energético e privacidade. Usamos técnicas extrativas clássicas e assertivas:

1. **NER Jurídico (`ner_juridico.py`)**: Utiliza Expressões Regulares Altamente Específicas (`Regex`) pré-compiladas em RAM (`re.compile`). Ele varre uma petição, e os padrões não batem falso negativo para CPF, CNPJ, OAB e IDs de CNJ. Ele isola tudo e atesta à máquina que a categoria local possui vazamentos.
2. **Sumarização TextRank Algébrico (`sumarizador.py`)**: Ao longo do documento, faz cálculos de centralidade de Autovetor entre as frases (`Cosseno TF-IDF`). A frase mais conectada as outras é rankeada como "Frase da Sumário Principal". O texto resultante são trechos REAIS de acórdãos, nada de reescrever informações processuais perigosas!

---

## 📊 Contexto Acadêmico (Próximos Passos)

Esta iniciação provou nossa **H1 (Hipótese Principal):** Modelos de Edge AI altamente otimizados por INT8 (TensorFlow Lite) substituem adequadamente arquiteturas LLM robustas quando o escopo é estrito, promovendo segurança da LGPD corporativa em redes desconectadas e limitadas em Hardware.

**Roadmap Acadêmico Futuro:**
- Artigo Final no padrão dos papers.
- Deploy da engine num celular ARM Android (.apk e API TFLite para Java/Kotlin) utilizando exatamente esses pesos minúsculos de 806 KB.
- Integração (PoC) com os painéis do e-SAJ - Softplan, com automações em segundo plano na triagem processual do advogado base.

---

<p align="center">
  Desenvolvido por <strong>Caio R.</strong> · PIC UNISSAU · 2026<br>
  Orientação: Prof. Msc. Afonso Calábria<br><br>
  <em>Edge AI · TensorFlow Lite · Clean Architecture · LGPD · OCR</em>
</p>