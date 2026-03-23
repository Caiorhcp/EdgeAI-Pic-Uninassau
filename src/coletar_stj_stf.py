# src/coletar_stj_stf.py
# Coleta documentos jurídicos públicos do STJ, STF, Planalto e JusBrasil
# Todos os dados são de domínio público conforme CF/88 art. 5 XIV e Lei 12.527/2011

import os
import re
import json
import time
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; PIC-EdgeAI-UNISSAU/1.0; pesquisa academica)"
}
DELAY = 1.5  # segundos entre requisições — respeito ao servidor

# ─── Funções utilitárias ──────────────────────────────────────────────────────
def limpar_texto(texto: str) -> str:
    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()

def salvar_dataset(novos: list, caminho="data/raw/dataset_juridico.json"):
    """Carrega o dataset existente e adiciona novos registros sem duplicar."""
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            existentes = json.load(f)
    else:
        existentes = []

    textos_existentes = {item["texto"][:100] for item in existentes}
    adicionados = 0
    for item in novos:
        if item["texto"][:100] not in textos_existentes:
            existentes.append(item)
            textos_existentes.add(item["texto"][:100])
            adicionados += 1

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(existentes, f, ensure_ascii=False, indent=2)

    return adicionados

# ─── 1. LGPD — ANPD e Planalto ───────────────────────────────────────────────
def coletar_lgpd() -> list:
    """
    Extrai trechos da Lei 13.709/2018 (LGPD) diretamente do Planalto.
    Fonte: https://www.planalto.gov.br — domínio público.
    """
    print("Coletando LGPD do Planalto...")
    url = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm"
    registros = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        # Extrair parágrafos do corpo da lei
        paragrafos = soup.find_all("p")
        for p in paragrafos:
            texto = limpar_texto(p.get_text())
            # Filtrar parágrafos relevantes (mínimo 60 chars, máximo 400)
            if 60 <= len(texto) <= 400:
                # Só incluir se tiver conteúdo jurídico LGPD
                palavras_chave = ["dado", "pessoal", "tratamento", "titular",
                                  "controlador", "operador", "consentimento",
                                  "privacidade", "proteção", "anpd"]
                if any(p in texto.lower() for p in palavras_chave):
                    registros.append({"texto": texto, "classe": "lgpd",
                                     "fonte": "Planalto - Lei 13709/2018"})
        time.sleep(DELAY)

    except Exception as e:
        print(f"  Erro LGPD Planalto: {e}")

    # Complementar com trechos da Lei 13.853/2019 (altera LGPD)
    url2 = "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2019/lei/l13853.htm"
    try:
        resp2 = requests.get(url2, headers=HEADERS, timeout=15)
        resp2.encoding = "utf-8"
        soup2 = BeautifulSoup(resp2.text, "lxml")
        for p in soup2.find_all("p"):
            texto = limpar_texto(p.get_text())
            if 60 <= len(texto) <= 400:
                if any(k in texto.lower() for k in ["dado", "pessoal", "anpd", "titular"]):
                    registros.append({"texto": texto, "classe": "lgpd",
                                     "fonte": "Planalto - Lei 13853/2019"})
        time.sleep(DELAY)
    except Exception as e:
        print(f"  Erro Lei 13853: {e}")

    print(f"  LGPD: {len(registros)} trechos coletados")
    return registros


# ─── 2. Constituição Federal — artigos relevantes ────────────────────────────
def coletar_constituicao() -> list:
    """
    Extrai artigos da CF/88 do Planalto — classe 'outro'.
    """
    print("Coletando Constituição Federal...")
    url = "https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm"
    registros = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        for p in soup.find_all("p"):
            texto = limpar_texto(p.get_text())
            if 60 <= len(texto) <= 400:
                palavras = ["artigo", "art.", "direito", "dever", "garantia",
                           "princípio", "lei", "federal", "estado", "república"]
                if any(k in texto.lower() for k in palavras):
                    registros.append({"texto": texto, "classe": "outro",
                                     "fonte": "Planalto - CF/1988"})
        time.sleep(DELAY)
    except Exception as e:
        print(f"  Erro CF: {e}")

    print(f"  CF/88: {len(registros)} trechos coletados")
    return registros


# ─── 3. Código Civil — contratos e responsabilidade civil ────────────────────
def coletar_codigo_civil() -> list:
    """
    Extrai artigos do Código Civil (Lei 10.406/2002) — classes contrato e outro.
    """
    print("Coletando Código Civil...")
    url = "https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm"
    registros = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        for p in soup.find_all("p"):
            texto = limpar_texto(p.get_text())
            if 60 <= len(texto) <= 400:
                # Termos de contrato
                termos_contrato = ["contrato", "contratante", "contratado",
                                   "cláusula", "rescisão", "prestação",
                                   "obrigação", "pacto", "convenção"]
                # Termos gerais
                termos_outros = ["artigo", "direito", "dever", "responsável",
                                 "prazo", "nulo", "válido", "indenização"]

                if any(k in texto.lower() for k in termos_contrato):
                    registros.append({"texto": texto, "classe": "contrato",
                                     "fonte": "Planalto - CC/2002"})
                elif any(k in texto.lower() for k in termos_outros):
                    registros.append({"texto": texto, "classe": "outro",
                                     "fonte": "Planalto - CC/2002"})
        time.sleep(DELAY)
    except Exception as e:
        print(f"  Erro CC: {e}")

    print(f"  CC/2002: {len(registros)} trechos coletados")
    return registros


# ─── 4. CPC — petições e processo civil ──────────────────────────────────────
def coletar_cpc() -> list:
    """
    Extrai artigos do CPC (Lei 13.105/2015) — classe peticao e outro.
    """
    print("Coletando CPC...")
    url = "https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm"
    registros = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        for p in soup.find_all("p"):
            texto = limpar_texto(p.get_text())
            if 60 <= len(texto) <= 400:
                termos_peticao = ["petição", "requerimento", "autor", "réu",
                                  "citação", "intimação", "prazo processual",
                                  "recurso", "apelação", "embargos"]
                termos_outros  = ["processo", "juiz", "tribunal", "sentença",
                                  "decisão", "despacho", "audiência"]

                if any(k in texto.lower() for k in termos_peticao):
                    registros.append({"texto": texto, "classe": "peticao",
                                     "fonte": "Planalto - CPC/2015"})
                elif any(k in texto.lower() for k in termos_outros):
                    registros.append({"texto": texto, "classe": "outro",
                                     "fonte": "Planalto - CPC/2015"})
        time.sleep(DELAY)
    except Exception as e:
        print(f"  Erro CPC: {e}")

    print(f"  CPC/2015: {len(registros)} trechos coletados")
    return registros


# ─── 5. STJ — jurisprudência pública ─────────────────────────────────────────
def coletar_stj_api() -> list:
    """
    Consulta a API pública do STJ para buscar ementas de acórdãos.
    Fonte: https://jurisprudencia.stj.jus.br — dados públicos.
    """
    print("Coletando acórdãos do STJ via API...")
    registros = []

    termos_busca = [
        "dano moral", "responsabilidade civil",
        "recurso especial", "prescrição",
        "proteção de dados", "LGPD"
    ]

    for termo in termos_busca:
        url = (
            "https://jurisprudencia.stj.jus.br/docs/api/search"
            f"?query={quote(termo)}"
            "&rows=15&start=0"
            "&tipo=acordao"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                docs = data.get("docs", [])
                for doc in docs:
                    # Ementa
                    ementa = doc.get("ementa", "")
                    if ementa and len(ementa) > 60:
                        registros.append({
                            "texto": limpar_texto(ementa)[:400],
                            "classe": "acordao",
                            "fonte": f"STJ - API - {termo}"
                        })
                    # Decisão
                    decisao = doc.get("decisao", "")
                    if decisao and len(decisao) > 60:
                        registros.append({
                            "texto": limpar_texto(decisao)[:400],
                            "classe": "acordao",
                            "fonte": f"STJ - API - {termo}"
                        })
            time.sleep(DELAY)
        except Exception as e:
            print(f"  Erro STJ API ({termo}): {e}")

    print(f"  STJ: {len(registros)} ementas coletadas")
    return registros


# ─── 6. STF — jurisprudência pública ─────────────────────────────────────────
def coletar_stf_api() -> list:
    """
    Consulta a API pública do STF para buscar ementas.
    Fonte: https://jurisprudencia.stf.jus.br — dados públicos.
    """
    print("Coletando acórdãos do STF via API...")
    registros = []

    termos_busca = [
        "direitos fundamentais", "inconstitucionalidade",
        "habeas corpus", "mandado de segurança",
        "proteção de dados pessoais"
    ]

    for termo in termos_busca:
        url = (
            "https://jurisprudencia.stf.jus.br/api/search/search"
            f"?query={quote(termo)}"
            "&pageSize=10&page=1"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("hits", {}).get("hits", [])
                for hit in hits:
                    src = hit.get("_source", {})
                    ementa = src.get("ementa", "")
                    if ementa and len(ementa) > 60:
                        registros.append({
                            "texto": limpar_texto(ementa)[:400],
                            "classe": "acordao",
                            "fonte": f"STF - API - {termo}"
                        })
            time.sleep(DELAY)
        except Exception as e:
            print(f"  Erro STF API ({termo}): {e}")

    print(f"  STF: {len(registros)} ementas coletadas")
    return registros


# ─── Pipeline principal ───────────────────────────────────────────────────────
def main():
    print("=" * 56)
    print("Coleta de dados jurídicos públicos")
    print("Fontes: Planalto, STJ, STF — domínio público")
    print("=" * 56)

    os.makedirs("data/raw", exist_ok=True)

    todos = []
    todos += coletar_lgpd()
    todos += coletar_constituicao()
    todos += coletar_codigo_civil()
    todos += coletar_cpc()
    todos += coletar_stj_api()
    todos += coletar_stf_api()

    print(f"\nTotal coletado: {len(todos)} registros")

    # Salvar e reportar
    adicionados = salvar_dataset(todos)

    # Contar distribuição final
    with open("data/raw/dataset_juridico.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    contagem = {}
    for item in dataset:
        contagem[item["classe"]] = contagem.get(item["classe"], 0) + 1

    print(f"Adicionados ao dataset: {adicionados} novos registros")
    print(f"Total no dataset agora: {len(dataset)}")
    print("\nDistribuição por classe:")
    for classe, qtd in sorted(contagem.items()):
        barra = "█" * (qtd // 5)
        status = "✅" if qtd >= 100 else "⚠️" if qtd >= 50 else "❌"
        print(f"  {status} {classe:10s}: {qtd:4d} {barra}")

    print("\nMeta para artigo: 100+ amostras por classe")
    print("Dataset salvo em data/raw/dataset_juridico.json")
    print("\nPróximo passo: python src/preprocessar.py && python src/treinar_modelo.py")


if __name__ == "__main__":
    main()