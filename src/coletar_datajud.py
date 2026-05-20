# src/coletar_datajud.py
# Coleta de dados jurídicos via API pública do Datajud (CNJ)
# Fonte: https://datajud-wiki.cnj.jus.br/ — dados públicos
# Uso acadêmico — PIC UNISSAU

import os
import json
import time
import requests

# ─── Chave da API Pública do Datajud (CNJ) ────────────────────────────────────
# Configure via: set DATAJUD_API_KEY=<chave>
# Obtenha a vigente em: https://datajud-wiki.cnj.jus.br/api-publica/acesso
DATAJUD_API_KEY = os.environ.get("DATAJUD_API_KEY", "")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PIC-EdgeAI-UNISSAU/2.0; pesquisa academica)",
    "Content-Type": "application/json",
}
if DATAJUD_API_KEY:
    HEADERS["Authorization"] = f"APIKey {DATAJUD_API_KEY}"
else:
    print("⚠️  DATAJUD_API_KEY não configurada! Requisições ao Datajud serão rejeitadas (401).")
    print("   Obtenha a chave em: https://datajud-wiki.cnj.jus.br/api-publica/acesso")
    print("   Configure: set DATAJUD_API_KEY=<sua_chave>\n")
DELAY   = 1.5
TIMEOUT = 20

# Índices do Datajud por tribunal
TRIBUNAIS_INDICES = {
    "TJSP":  "tjsp",
    "TJRJ":  "tjrj",
    "TJMG":  "tjmg",
    "TJRS":  "tjrs",
    "TJPR":  "tjpr",
    "STJ":   "stj",
    "STF":   "stf",
    "TRF3":  "trf3",
    "TRF4":  "trf4",
    "TST":   "tst",
}

BASE_URL = "https://api-publica.datajud.cnj.jus.br"


def buscar_processos_datajud(indice: str, assunto: str, limite: int = 20) -> list:
    """
    Busca processos no Datajud por assunto/tribunal e extrai textos de ementas/movimentos.
    """
    url = f"{BASE_URL}/api_publica_{indice}/_search"
    payload = {
        "query": {
            "match": {"assunto.descricao": assunto}
        },
        "size": limite,
        "_source": ["numeroProcesso", "classe", "assunto", "partes", "movimentos"],
    }

    registros = []
    try:
        resp = requests.post(url, json=payload, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code != 200:
            print(f"  Datajud {indice} ({assunto}): HTTP {resp.status_code}")
            return registros

        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])

        for hit in hits:
            src = hit.get("_source", {})
            classe  = src.get("classe", {})
            desc_classe = classe.get("descricao", "") if isinstance(classe, dict) else str(classe)

            assuntos_raw = src.get("assunto", [])
            desc_assunto = ""
            if assuntos_raw and isinstance(assuntos_raw, list):
                desc_assunto = assuntos_raw[0].get("descricao", "") if assuntos_raw else ""

            partes_raw = src.get("partes", [])
            partes_txt = " ".join([
                p.get("nome", "") for p in partes_raw[:3] if p.get("nome")
            ])

            movimentos_raw = src.get("movimentos", [])
            movimentos_txt = " | ".join([
                m.get("nome", "") for m in movimentos_raw[:5] if m.get("nome")
            ])

            # Montar texto para dataset
            partes = []
            if desc_classe:
                partes.append(desc_classe + ".")
            if desc_assunto:
                partes.append(f"Assunto: {desc_assunto}.")
            if partes_txt:
                partes.append(f"Partes: {partes_txt}.")
            if movimentos_txt:
                partes.append(f"Movimentos: {movimentos_txt}.")

            texto = " ".join(partes).strip()
            if len(texto) >= 60:
                # Determinar classe do dataset
                classe_dataset = _inferir_classe_dataset(desc_classe, desc_assunto)
                registros.append({
                    "texto": texto[:500],
                    "classe": classe_dataset,
                    "fonte": f"Datajud-{indice.upper()}-{assunto}"
                })

        time.sleep(DELAY)
    except Exception as exc:
        print(f"  Erro Datajud {indice} ({assunto}): {exc}")

    return registros


def _inferir_classe_dataset(classe_processual: str, assunto: str) -> str:
    """Infere a classe do dataset (lgpd, acordao, contrato, peticao, outro)."""
    texto = (classe_processual + " " + assunto).lower()

    if any(k in texto for k in ["lgpd", "dados pessoais", "privacidade", "proteção de dados"]):
        return "lgpd"
    if any(k in texto for k in ["apelação", "recurso especial", "acórdão", "agravo", "embargos"]):
        return "acordao"
    if any(k in texto for k in ["contrato", "locação", "prestação de serviços", "compra e venda"]):
        return "contrato"
    if any(k in texto for k in ["petição", "ação", "requerimento", "mandado", "habeas corpus"]):
        return "peticao"
    return "outro"


def salvar_dataset(novos: list, caminho: str = "data/raw/dataset_juridico.json"):
    """Adiciona registros ao dataset sem duplicar."""
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            existentes = json.load(f)
    else:
        existentes = []

    textos_existentes = {item["texto"][:80] for item in existentes}
    adicionados = 0
    for item in novos:
        if item["texto"][:80] not in textos_existentes:
            existentes.append(item)
            textos_existentes.add(item["texto"][:80])
            adicionados += 1

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(existentes, f, ensure_ascii=False, indent=2)

    return adicionados


def main():
    print("=" * 56)
    print("Coleta via Datajud (CNJ) — API Pública")
    print("Fonte: api-publica.datajud.cnj.jus.br")
    print("=" * 56)

    os.makedirs("data/raw", exist_ok=True)

    todos = []

    # ─── Acórdãos ─────────────────────────────────────────────────────────
    print("\nBuscando Acórdãos...")
    termos_acordao = [
        ("tjsp", "dano moral"),
        ("tjsp", "responsabilidade civil"),
        ("tjrj", "recurso especial"),
        ("tjmg", "prescrição"),
        ("tjrs", "indenização"),
        ("trf3", "tributário"),
        ("trf4", "previdenciário"),
        ("tst",  "horas extras"),
    ]
    for indice, termo in termos_acordao:
        registros = buscar_processos_datajud(indice, termo, limite=15)
        print(f"  {indice.upper()} ({termo}): {len(registros)} registros")
        todos += registros

    # ─── Contratos ────────────────────────────────────────────────────────
    print("\nBuscando processos sobre Contratos...")
    termos_contrato = [
        ("tjsp", "contrato de prestação de serviços"),
        ("tjrj", "rescisão contratual"),
        ("tjmg", "locação"),
        ("tjpr", "compra e venda"),
    ]
    for indice, termo in termos_contrato:
        registros = buscar_processos_datajud(indice, termo, limite=15)
        print(f"  {indice.upper()} ({termo}): {len(registros)} registros")
        todos += registros

    # ─── Petições ─────────────────────────────────────────────────────────
    print("\nBuscando Petições...")
    termos_peticao = [
        ("tjsp", "ação de indenização"),
        ("tjrj", "mandado de segurança"),
        ("tjmg", "habeas corpus"),
        ("trf3", "ação ordinária"),
    ]
    for indice, termo in termos_peticao:
        registros = buscar_processos_datajud(indice, termo, limite=15)
        print(f"  {indice.upper()} ({termo}): {len(registros)} registros")
        todos += registros

    # ─── LGPD ─────────────────────────────────────────────────────────────
    print("\nBuscando processos LGPD/Dados Pessoais...")
    termos_lgpd = [
        ("tjsp", "dados pessoais"),
        ("tjrj", "proteção de dados"),
        ("tjmg", "privacidade"),
    ]
    for indice, termo in termos_lgpd:
        registros = buscar_processos_datajud(indice, termo, limite=10)
        print(f"  {indice.upper()} ({termo}): {len(registros)} registros")
        todos += registros

    print(f"\nTotal coletado: {len(todos)} registros")

    adicionados = salvar_dataset(todos)

    # Relatório final
    with open("data/raw/dataset_juridico.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    contagem: dict = {}
    for item in dataset:
        contagem[item["classe"]] = contagem.get(item["classe"], 0) + 1

    print(f"Adicionados ao dataset: {adicionados} novos registros")
    print(f"Total no dataset: {len(dataset)}")
    print("\nDistribuição por classe:")
    for classe, qtd in sorted(contagem.items()):
        barra  = "█" * (qtd // 10)
        status = "✅" if qtd >= 150 else "⚠️" if qtd >= 80 else "❌"
        print(f"  {status} {classe:10s}: {qtd:4d} {barra}")

    print("\nPróximo passo: python src/preprocessar.py && python src/treinar_modelo.py")


if __name__ == "__main__":
    main()
