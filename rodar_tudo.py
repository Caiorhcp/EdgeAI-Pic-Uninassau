# rodar_tudo.py
import os
import sys
import time
import subprocess

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"]  = "2"

PYTHON  = sys.executable
VERDE   = "\033[92m"
AMARELO = "\033[93m"
VERMELHO= "\033[91m"
AZUL    = "\033[94m"
CIANO   = "\033[96m"
RESET   = "\033[0m"
NEGRITO = "\033[1m"

def log(msg, cor=RESET):
    print(f"{cor}{msg}{RESET}", flush=True)

def limpar():
    os.system("cls" if os.name == "nt" else "clear")

def cabecalho():
    log(f"""
{AZUL}{NEGRITO}╔══════════════════════════════════════════════════════════╗
║   ⚖️  Edge AI Jurídico — Pipeline Interativo              ║
║   PIC UNISSAU · Prof. Msc. Afonso Calábria               ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")

def menu_principal(passos, status):
    cabecalho()
    log(f"  {'#':<4} {'Descrição':<42} {'Status'}", CIANO)
    log(f"  {'─'*60}", CIANO)

    for i, (_, desc, _) in enumerate(passos):
        n      = f"{i+1:02d}"
        s      = status[i]
        nome   = desc.split("—")[1].strip() if "—" in desc else desc
        if s == "ok":
            icone = f"{VERDE}✅ OK     {RESET}"
        elif s == "erro":
            icone = f"{VERMELHO}❌ ERRO   {RESET}"
        elif s == "pulado":
            icone = f"{AMARELO}⏭  PULADO {RESET}"
        else:
            icone = f"  ⬜ aguardando"
        log(f"  {n:<4} {nome:<42} {icone}")

    log("")
    concluidos = sum(1 for s in status if s == "ok")
    log(f"  Progresso: {concluidos}/{len(passos)} passos concluídos", CIANO)
    log("")

def rodar_passo(script, descricao):
    log(f"\n{AZUL}{'─'*60}", AZUL)
    log(f"  ▶  {descricao}", NEGRITO)
    log(f"  →  {script}", AZUL)
    log(f"{'─'*60}{RESET}\n")

    t0        = time.time()
    resultado = subprocess.run([PYTHON, script])
    duracao   = time.time() - t0

    if resultado.returncode == 0:
        log(f"\n{VERDE}✅ Concluído em {duracao:.1f}s{RESET}")
        return True, duracao
    else:
        log(f"\n{VERMELHO}❌ Falhou em {duracao:.1f}s (código {resultado.returncode}){RESET}")
        return False, duracao

def perguntar(pergunta, opcoes):
    """Exibe uma pergunta e retorna a escolha do usuário."""
    while True:
        log(f"\n{CIANO}{pergunta}{RESET}")
        for k, v in opcoes.items():
            log(f"  {NEGRITO}[{k}]{RESET} {v}")
        resp = input(f"\n  Escolha: ").strip().lower()
        if resp in opcoes:
            return resp
        log(f"  {AMARELO}Opção inválida. Tente novamente.{RESET}")

def main():
    limpar()
    cabecalho()

    PASSOS = [
        # (script, descrição, obrigatório)
        ("src/coletar_dados.py",
         "Passo 01 — Dataset base (225 amostras curadas)",
         True),
        ("src/coletar_stj_stf.py",
         "Passo 02 — Expandir com Planalto / STJ / STF",
         True),
        ("src/balancear_dataset.py",
         "Passo 03 — Balancear classes deficientes",
         True),
        ("src/adicionar_dados_manuais.py",
         "Passo 04 — Complementar acórdão e contrato",
         True),
        ("src/preprocessar.py",
         "Passo 05 — Pré-processamento TF-IDF",
         True),
        ("src/treinar_modelo.py",
         "Passo 06 — Treinar rede neural densa",
         True),
        ("src/converter_tflite.py",
         "Passo 07 — Converter para TFLite INT8",
         True),
        ("src/pruning_modelo.py",
         "Passo 08 — Pruning por magnitude (opcional)",
         False),
        ("src/relatorio_metricas.py",
         "Passo 09 — Gerar relatório de métricas",
         True),
        ("src/baseline_svm.py",
         "Passo 10 — Comparação com baselines (SVM, LR, NB)",
         True),
        ("src/validacao_kfold.py",
         "Passo 11 — Validação cruzada 10-fold ⏳ (~15 min)",
         True),
    ]

    status  = ["pendente"] * len(PASSOS)
    tempos  = [0.0]        * len(PASSOS)
    inicio  = time.time()

    # ── Modo de execução ──────────────────────────────────────────────────────
    modo = perguntar(
        "Como deseja executar o pipeline?",
        {
            "1": "Automático — rodar tudo em sequência sem pausas",
            "2": "Passo a passo — confirmar antes de cada etapa",
            "3": "Escolher passos — selecionar quais rodar",
            "s": "Sair",
        }
    )

    if modo == "s":
        log("\nAté logo!", AMARELO)
        sys.exit(0)

    # ── Escolher passos ───────────────────────────────────────────────────────
    passos_selecionados = list(range(len(PASSOS)))

    if modo == "3":
        limpar()
        menu_principal(PASSOS, status)
        log("  Digite os números dos passos separados por vírgula.", CIANO)
        log("  Exemplo: 1,2,5,6,7  ou  6,7  para só retreinar\n", CIANO)
        entrada = input("  Passos: ").strip()
        try:
            selecionados = [int(x.strip()) - 1 for x in entrada.split(",")]
            selecionados = [s for s in selecionados if 0 <= s < len(PASSOS)]
            if not selecionados:
                raise ValueError
            passos_selecionados = selecionados
        except ValueError:
            log("Entrada inválida. Rodando todos os passos.", AMARELO)

    # ── Executar ──────────────────────────────────────────────────────────────
    for i in passos_selecionados:
        script, descricao, obrigatorio = PASSOS[i]

        limpar()
        menu_principal(PASSOS, status)

        # Passo a passo: pedir confirmação
        if modo == "2":
            nome = descricao.split("—")[1].strip() if "—" in descricao else descricao
            resp = perguntar(
                f"Próximo: {descricao}",
                {
                    "r": f"▶  Rodar agora",
                    "p": f"⏭  Pular este passo",
                    "s": f"⏹  Parar aqui",
                }
            )
            if resp == "p":
                status[i] = "pulado"
                log(f"  Passo pulado.", AMARELO)
                continue
            if resp == "s":
                log(f"\n  Pipeline pausado pelo usuário.", AMARELO)
                break

        # Rodar
        ok, duracao = rodar_passo(script, descricao)
        tempos[i]   = duracao

        if ok:
            status[i] = "ok"
        else:
            status[i] = "erro"
            if obrigatorio and modo != "3":
                resp = perguntar(
                    f"❌ O passo falhou. O que deseja fazer?",
                    {
                        "t": "Tentar novamente",
                        "c": "Continuar mesmo assim",
                        "s": "Parar o pipeline",
                    }
                )
                if resp == "t":
                    ok, duracao = rodar_passo(script, descricao)
                    tempos[i]   = duracao
                    status[i]   = "ok" if ok else "erro"
                elif resp == "s":
                    log("\n  Pipeline interrompido.", VERMELHO)
                    break
                # "c" → continua mesmo com erro

        # Pausa breve entre passos no modo automático
        if modo == "1" and i < passos_selecionados[-1]:
            time.sleep(0.5)

    # ── Resumo final ──────────────────────────────────────────────────────────
    limpar()
    menu_principal(PASSOS, status)

    duracao_total = time.time() - inicio
    mins = int(duracao_total // 60)
    segs = int(duracao_total % 60)

    ok_count     = sum(1 for s in status if s == "ok")
    erro_count   = sum(1 for s in status if s == "erro")
    pulado_count = sum(1 for s in status if s == "pulado")

    log(f"{AZUL}{'─'*60}{RESET}")
    log(f"  ⏱️  Tempo total : {mins}min {segs}s")
    log(f"  ✅  Concluídos : {ok_count}")
    log(f"  ❌  Com erro   : {erro_count}")
    log(f"  ⏭️  Pulados    : {pulado_count}")
    log(f"{AZUL}{'─'*60}{RESET}")

    if erro_count == 0 and ok_count > 0:
        log(f"""
{VERDE}{NEGRITO}  🎉 Pipeline concluído com sucesso!

  Arquivos gerados:
  ├── data/raw/dataset_juridico.json              ← dataset
  ├── models/tflite/modelo_juridico_int8.tflite   ← modelo edge
  ├── models/relatorio/relatorio_metricas.png     ← métricas
  ├── models/relatorio/comparacao_baseline.png    ← vs SVM
  └── models/relatorio/kfold_resultados.png       ← k-fold

  Para abrir a interface:
  → streamlit run app.py
{RESET}""")
    elif erro_count > 0:
        log(f"\n  {AMARELO}⚠️  {erro_count} passo(s) com erro — verifique os logs acima.{RESET}")

    # Oferecer abrir o app
    if ok_count > 0:
        resp = input(f"\n  {CIANO}Abrir a interface agora? (s/n): {RESET}").strip().lower()
        if resp == "s":
            log("\n  Iniciando Streamlit…", VERDE)
            subprocess.run([PYTHON, "-m", "streamlit", "run", "app.py"])


if __name__ == "__main__":
    main()