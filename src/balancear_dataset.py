# src/balancear_dataset.py
# Complementa as classes deficientes e balanceia o dataset
import os
import json
import random
import requests
from bs4 import BeautifulSoup
import time

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; PIC-EdgeAI-UNISSAU/1.0)"}
DELAY   = 1.5

def limpar(texto):
    import re
    return re.sub(r"\s+", " ", texto).strip()

# ─── Acórdãos sintéticos baseados em padrões reais do STJ/STF ─────────────────
# Como as APIs estão bloqueadas, usamos textos baseados em padrões
# extraídos de publicações públicas do DJe (Diário da Justiça Eletrônico)

ACORDAOS = [
    "ACÓRDÃO. Vistos, relatados e discutidos estes autos, acordam os Ministros da Terceira Turma do Superior Tribunal de Justiça, por unanimidade, negar provimento ao recurso especial, nos termos do voto do Senhor Ministro Relator.",
    "EMENTA: Recurso especial. Direito Civil. Responsabilidade civil. Dano moral. Inscrição indevida em cadastro de inadimplentes. Dano presumido. Valor da indenização. Razoabilidade e proporcionalidade. Recurso não provido.",
    "DECISÃO: Trata-se de agravo interno interposto contra decisão monocrática que negou seguimento ao recurso especial, com fundamento na Súmula 83 do STJ. Não merece prosperar o inconformismo.",
    "Por maioria de votos, o Tribunal deu provimento ao recurso de apelação para reformar a sentença de primeiro grau, vencido o Desembargador Relator, que mantinha a decisão recorrida.",
    "EMENTA: Direito Processual Civil. Embargos de declaração. Omissão. Ausência. Efeito infringente. Impossibilidade. Os embargos de declaração não se prestam à rediscussão da causa já decidida.",
    "A jurisprudência desta Corte Superior é firme no sentido de que o termo inicial da prescrição da pretensão indenizatória é a data do conhecimento do dano e de sua autoria pelo lesado.",
    "Recurso especial provido para afastar a condenação em danos morais, por não restar demonstrado nos autos o efetivo abalo à honra ou à imagem do recorrido.",
    "ACÓRDÃO. A Turma, por votação unânime, conheceu do recurso especial e lhe deu provimento para restabelecer a sentença de primeiro grau, condenando a parte ré ao pagamento de indenização.",
    "Nos termos do artigo 105, inciso III, alínea a, da Constituição Federal, compete ao Superior Tribunal de Justiça julgar os recursos especiais quando a decisão recorrida contrariar tratado ou lei federal.",
    "O acórdão recorrido está em conformidade com a jurisprudência consolidada desta Corte, razão pela qual incide o óbice da Súmula 83 do STJ ao conhecimento do recurso especial.",
    "EMENTA: Processo Civil. Agravo interno no recurso especial. Decisão monocrática mantida. Ausência de argumentos novos capazes de infirmar os fundamentos da decisão agravada.",
    "Por unanimidade, a Turma decidiu pela manutenção do acórdão recorrido, que fixou o valor da indenização por danos morais em conformidade com os princípios da razoabilidade e proporcionalidade.",
    "ACÓRDÃO: STF, Tribunal Pleno. Por maioria, o Tribunal julgou procedente a ação direta de inconstitucionalidade, declarando inconstitucional o dispositivo impugnado.",
    "EMENTA: Constitucional. Ação Direta de Inconstitucionalidade. Princípio da legalidade. Reserva legal. Delegação legislativa. Inconstitucionalidade reconhecida. Procedência da ação.",
    "Habeas corpus. Impetração em substituição a recurso ordinário. Não cabimento. Writ não conhecido. A utilização do habeas corpus como substituto do recurso ordinário não é admitida por esta Corte.",
    "DECISÃO: Vistos. Trata-se de mandado de segurança impetrado contra ato do Ministro de Estado. Após análise dos autos, verifico que não estão presentes os requisitos para concessão da liminar.",
    "EMENTA: Tributário. ICMS. Base de cálculo. Inclusão do próprio imposto. Constitucionalidade reconhecida pelo Supremo Tribunal Federal em regime de repercussão geral.",
    "O recurso extraordinário não merece provimento, pois a decisão recorrida está em consonância com a jurisprudência desta Corte acerca da matéria constitucional em debate.",
    "ACÓRDÃO. STJ. Recurso Especial. Direito do Consumidor. Vício do produto. Prazo decadencial. Contagem. Termo inicial. Ciência do vício pelo consumidor. Recurso desprovido.",
    "Por votação unânime, o colegiado negou provimento ao agravo regimental, mantendo a decisão que havia inadmitido o recurso especial por ausência dos pressupostos de admissibilidade.",
    "EMENTA: Civil. Família. Alimentos. Revisão. Alteração das condições econômicas das partes. Comprovação. Necessária. Ausência. Manutenção do quantum fixado. Recurso improvido.",
    "Conforme pacífico entendimento desta Corte Superior, a responsabilidade objetiva do fornecedor independe de culpa, bastando a comprovação do dano e do nexo causal com o produto ou serviço.",
    "ACÓRDÃO: Vistos, acordam os Desembargadores da Câmara Cível em, por unanimidade, negar provimento ao recurso de apelação, mantendo a sentença recorrida em todos os seus termos.",
    "EMENTA: Previdenciário. Aposentadoria por invalidez. Laudo pericial. Incapacidade total e permanente. Comprovação. Concessão do benefício. Recurso da autarquia desprovido.",
    "A fixação do valor dos honorários advocatícios deve observar os critérios estabelecidos no artigo 85 do CPC, levando em consideração o grau de zelo do profissional e o lugar de prestação do serviço.",
    "DECISÃO MONOCRÁTICA: Nego seguimento ao recurso especial, porquanto a matéria objeto do recurso encontra-se pacificada neste Superior Tribunal de Justiça, nos termos da Súmula 568.",
    "O prazo para interposição do recurso especial é de quinze dias, contado da publicação do acórdão recorrido no Diário da Justiça, conforme dispõe o artigo 1.003 do Código de Processo Civil.",
    "EMENTA: Processo Civil. Nulidade. Cerceamento de defesa. Indeferimento de prova. Decisão fundamentada. Ausência de prejuízo demonstrado. Nulidade não reconhecida. Apelo improvido.",
    "Por força do efeito vinculante das súmulas do Supremo Tribunal Federal, os órgãos do Poder Judiciário e a Administração Pública direta e indireta estão obrigados a aplicar o enunciado.",
    "ACÓRDÃO. Direito Penal. Tráfico de entorpecentes. Quantidade e natureza da droga. Fundamentação idônea para a fixação da pena-base acima do mínimo legal. Recurso não provido.",
    "Segundo a orientação jurisprudencial desta Corte, a simples devolução indevida de cheque não gera, por si só, dano moral presumido, sendo necessária a comprovação do efetivo abalo.",
    "EMENTA: Administrativo. Servidor público. Estabilidade. Requisitos. Avaliação especial de desempenho. Ausência. Demissão. Legalidade reconhecida. Mandado de segurança denegado.",
    "O recurso não comporta conhecimento na parte em que pretende o reexame do conjunto fático-probatório dos autos, o que encontra óbice na Súmula 7 desta Corte Superior.",
    "ACÓRDÃO: Por unanimidade, o Pleno do Tribunal de Justiça declarou a inconstitucionalidade da lei estadual por vício formal, em razão de invasão de competência privativa da União.",
    "Nos termos do artigo 927 do Código Civil, aquele que por ato ilícito causar dano a outrem fica obrigado a repará-lo, independentemente de culpa, nos casos especificados em lei.",
    "EMENTA: Trabalhista. Horas extras. Acordo de compensação de jornada. Validade. Norma coletiva. Ausência de irregularidades. Pagamento indevido. Recurso da empresa provido.",
    "A tese fixada sob o rito dos recursos repetitivos tem natureza vinculante, obrigando os demais órgãos do Poder Judiciário quando se depararem com controvérsia idêntica.",
    "DECISÃO: O presente recurso extraordinário não apresenta repercussão geral, pois a questão constitucional suscitada possui natureza eminentemente infraconstitucional.",
    "Por maioria, o Tribunal Superior do Trabalho deu provimento ao recurso de revista para reconhecer o vínculo empregatício entre as partes e condenar a reclamada ao pagamento das verbas rescisórias.",
    "EMENTA: Eleitoral. Recurso Ordinário. Registro de candidatura. Inelegibilidade. Lei Complementar 135/2010. Aplicação imediata. Constitucionalidade reconhecida. Recurso desprovido.",
    "A legitimidade ativa para propositura da ação popular é de qualquer cidadão, entendendo-se como tal o nacional que está no gozo de seus direitos políticos, conforme artigo 1 da Lei 4.717/65.",
    "ACÓRDÃO. Processual Civil. Ação rescisória. Coisa julgada. Violação manifesta de norma jurídica. Não configurada. Pedido improcedente. Ação julgada improcedente por unanimidade.",
    "O princípio da não culpabilidade, insculpido no artigo 5, inciso LVII, da Constituição Federal, impede a execução da pena antes do trânsito em julgado da sentença penal condenatória.",
    "EMENTA: Direito Civil. Testamento. Interpretação. Vontade do testador. Prevalência. Forma solene. Observância. Nulidade não reconhecida. Recurso do herdeiro preterido desprovido.",
    "Segundo o entendimento consolidado nesta Corte, a responsabilidade do Estado pelos atos de seus agentes é objetiva, na modalidade risco administrativo, nos termos do artigo 37 da CF.",
]

# ─── Contratos sintéticos baseados em modelos públicos ───────────────────────
CONTRATOS = [
    "Pelo presente instrumento particular, as partes a seguir qualificadas celebram o presente contrato de prestação de serviços, que se regerá pelas seguintes cláusulas e condições.",
    "Cláusula Primeira — Do Objeto: O presente contrato tem por objeto a prestação de serviços de consultoria empresarial, conforme especificações constantes do Anexo I.",
    "Cláusula Segunda — Do Prazo: O presente contrato terá vigência pelo prazo de 12 (doze) meses, contados da data de sua assinatura, podendo ser prorrogado mediante termo aditivo.",
    "Cláusula Terceira — Do Preço e Forma de Pagamento: Pela prestação dos serviços ora contratados, o Contratante pagará ao Contratado o valor mensal de R$ 5.000,00.",
    "Cláusula Quarta — Das Obrigações do Contratado: Executar os serviços com zelo e diligência, mantendo sigilo absoluto sobre as informações confidenciais do Contratante.",
    "Cláusula Quinta — Da Rescisão: O presente contrato poderá ser rescindido por qualquer das partes, mediante aviso prévio de 30 (trinta) dias, por escrito.",
    "Cláusula Sexta — Da Multa Rescisória: Em caso de rescisão imotivada, a parte infratora pagará à outra multa compensatória equivalente a 20% do valor total do contrato.",
    "Cláusula Sétima — Do Foro: Fica eleito o foro da Comarca de São Paulo, Estado de São Paulo, para dirimir quaisquer dúvidas ou litígios oriundos do presente contrato.",
    "As partes declaram ter lido e entendido todas as cláusulas do presente instrumento, concordando com seu conteúdo, assinando-o em duas vias de igual teor e forma.",
    "O contratado se compromete a manter absoluta confidencialidade sobre todas as informações, dados e documentos a que tiver acesso em razão da execução deste contrato.",
    "Constituem obrigações do Contratante: fornecer ao Contratado todas as informações e documentos necessários à execução dos serviços objeto do presente instrumento.",
    "O reajuste dos valores contratuais será realizado anualmente, tendo como indexador o Índice Nacional de Preços ao Consumidor Amplo — IPCA, calculado e divulgado pelo IBGE.",
    "A subcontratação total ou parcial dos serviços objeto deste contrato somente será permitida mediante prévia e expressa autorização por escrito do Contratante.",
    "Os casos omissos serão resolvidos de comum acordo entre as partes, com base nos princípios gerais do direito, especialmente os previstos no Código Civil Brasileiro.",
    "Fica vedado ao Contratado ceder ou transferir, total ou parcialmente, os direitos e obrigações decorrentes deste contrato sem a prévia anuência escrita do Contratante.",
    "O presente instrumento obriga as partes contratantes, seus herdeiros, sucessores e cessionários, não podendo ser alterado sem o consentimento mútuo e expresso de ambas.",
    "Em caso de inadimplemento de qualquer obrigação contratual, a parte inadimplente ficará sujeita ao pagamento de multa de 2% sobre o valor em aberto, mais juros de 1% ao mês.",
    "A propriedade intelectual de todos os produtos, relatórios, estudos e documentos produzidos pelo Contratado em razão deste contrato pertencerá exclusivamente ao Contratante.",
    "O Contratado declara, sob as penas da lei, que possui todos os registros, licenças e autorizações necessários ao desenvolvimento das atividades objeto do presente contrato.",
    "O aceite formal dos serviços pelo Contratante constitui condição para pagamento, devendo ser realizado no prazo de 5 dias úteis após a entrega de cada etapa.",
    "Quaisquer comunicações entre as partes deverão ser feitas por escrito, mediante correspondência com aviso de recebimento ou por correio eletrônico com confirmação de leitura.",
    "O contrato poderá ser suspenso por força maior ou caso fortuito, sem penalidades para qualquer das partes, devendo a situação ser comunicada imediatamente por escrito.",
    "O Contratado manterá durante toda a vigência do contrato, e pelo prazo de 5 anos após seu término, sigilo sobre todas as informações confidenciais do Contratante.",
    "Pelo presente instrumento, as partes estabelecem que os serviços serão prestados nas instalações do Contratante, na Avenida Paulista, n. 1000, São Paulo, SP.",
    "As despesas com deslocamento, hospedagem e alimentação necessárias à execução dos serviços fora da sede do Contratado serão reembolsadas mediante apresentação de comprovantes.",
    "O Contratado se obriga a entregar os produtos e relatórios nas datas previstas no cronograma constante do Anexo II, que integra o presente instrumento para todos os fins.",
    "Em caso de descumprimento de prazo por culpa do Contratado, será aplicada multa moratória de 0,5% ao dia sobre o valor da parcela em atraso, até o limite de 15%.",
    "O contrato somente poderá ser alterado mediante termo aditivo, devidamente firmado pelas partes e por duas testemunhas, com expressa referência ao instrumento original.",
    "O presente contrato é celebrado em caráter irrevogável e irretratável, obrigando as partes, seus herdeiros e sucessores, independentemente de outra formalidade.",
    "Declaram as partes que este instrumento expressa fielmente sua vontade, tendo sido livremente negociado e pactuado, sem qualquer vício de consentimento.",
    "O Contratante reserva-se o direito de realizar auditorias periódicas nos serviços prestados, com a finalidade de verificar o cumprimento das obrigações contratuais.",
    "A garantia contratual, no valor equivalente a 5% do total do contrato, deverá ser prestada pelo Contratado antes do início da execução dos serviços.",
    "Em atendimento à Lei 13.709/2018 — LGPD, o Contratado se compromete a tratar os dados pessoais que lhe forem confiados exclusivamente para os fins previstos neste instrumento.",
    "O Contratado não poderá utilizar o nome, marca ou logotipo do Contratante em qualquer material de divulgação ou publicidade sem autorização prévia e por escrito.",
    "As partes contratantes, por seus representantes legais, firmam o presente instrumento em 2 vias de igual teor, juntamente com as 2 testemunhas abaixo identificadas.",
    "Cláusula de Revisão: O equilíbrio econômico-financeiro do contrato será mantido durante toda a sua vigência, podendo qualquer das partes solicitar revisão motivada dos valores.",
    "O prazo para cumprimento das obrigações estabelecidas neste contrato é essencial, sendo o seu descumprimento causa de rescisão imediata independentemente de notificação prévia.",
    "O Contratado assume integral responsabilidade pelos encargos trabalhistas, previdenciários, fiscais e comerciais resultantes da execução do objeto deste contrato.",
    "Ficam excluídas do presente contrato quaisquer outras obrigações que não as expressamente aqui estabelecidas, salvo as decorrentes de lei ou de boa-fé contratual.",
    "Em caso de controvérsia sobre a interpretação das cláusulas deste contrato, prevalecerá a interpretação que melhor atenda à boa-fé e ao equilíbrio entre as partes.",
    "O presente contrato de locação comercial é celebrado entre as partes qualificadas no preâmbulo, para locação do imóvel sito à Rua das Flores, 200, São Paulo, SP.",
    "O locatário se compromete a pagar pontualmente o aluguel mensal no valor de R$ 3.500,00, até o 5º dia útil de cada mês, sob pena de multa de 10% sobre o valor devido.",
    "O contrato de compra e venda tem por objeto o imóvel descrito na matrícula n. 12345 do Cartório de Registro de Imóveis, pelo preço certo e ajustado de R$ 450.000,00.",
    "O presente contrato de franquia confere ao franqueado o direito de usar a marca, sistema e produtos do franqueador, nos termos da circular de oferta de franquia.",
    "Este contrato de licença de software autoriza o licenciado a usar o programa na versão indicada, de forma não exclusiva e intransferível, pelo período contratado.",
]

def main():
    print("=" * 56)
    print("Balanceando dataset — complementando acordao e contrato")
    print("=" * 56)

    with open("data/raw/dataset_juridico.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # Contar situação atual
    contagem = {}
    for item in dataset:
        contagem[item["classe"]] = contagem.get(item["classe"], 0) + 1

    print("\nSituação antes do balanceamento:")
    for cls, qtd in sorted(contagem.items()):
        print(f"  {cls:10s}: {qtd}")

    # Adicionar acórdãos
    novos_acordaos = [{"texto": t, "classe": "acordao",
                       "fonte": "padroes-dje-publicos"}
                      for t in ACORDAOS]

    # Adicionar contratos
    novos_contratos = [{"texto": t, "classe": "contrato",
                        "fonte": "modelos-contratos-publicos"}
                       for t in CONTRATOS]

    # Tentar coletar CC/2002 com URL correta
    print("\nTentando Código Civil com URL alternativa...")
    try:
        url = "https://www.planalto.gov.br/ccivil_03/leis/2002/L10406compilada.htm"
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.encoding = "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")
        cc_textos = []
        for p in soup.find_all("p"):
            texto = limpar(p.get_text())
            if 60 <= len(texto) <= 400:
                termos = ["contrato", "obrigação", "cláusula", "prestação",
                          "rescisão", "locação", "compra", "venda", "pacto"]
                if any(k in texto.lower() for k in termos):
                    cc_textos.append({"texto": texto, "classe": "contrato",
                                      "fonte": "Planalto-CC2002-alt"})
        novos_contratos += cc_textos
        print(f"  CC/2002: {len(cc_textos)} trechos coletados")
        time.sleep(DELAY)
    except Exception as e:
        print(f"  CC/2002 alternativo: {e}")

    # Tentar STF sem verificação SSL
    print("Tentando STF com SSL desabilitado...")
    termos_stf = ["dano moral", "responsabilidade", "recurso especial",
                  "habeas corpus", "mandado segurança"]
    stf_textos = []
    for termo in termos_stf:
        try:
            url = (f"https://jurisprudencia.stf.jus.br/api/search/search"
                   f"?query={requests.utils.quote(termo)}&pageSize=10&page=1")
            resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("hits", {}).get("hits", [])
                for hit in hits:
                    src   = hit.get("_source", {})
                    ementa = src.get("ementa", "")
                    if ementa and len(ementa) > 60:
                        stf_textos.append({
                            "texto": limpar(ementa)[:400],
                            "classe": "acordao",
                            "fonte": f"STF-{termo}"
                        })
            time.sleep(DELAY)
        except Exception as e:
            print(f"  STF ({termo}): {e}")
    print(f"  STF: {len(stf_textos)} ementas coletadas")
    novos_acordaos += stf_textos

    # Adicionar tudo ao dataset
    textos_existentes = {item["texto"][:80] for item in dataset}
    adicionados = 0
    for item in novos_acordaos + novos_contratos:
        if item["texto"][:80] not in textos_existentes:
            dataset.append(item)
            textos_existentes.add(item["texto"][:80])
            adicionados += 1

    with open("data/raw/dataset_juridico.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    # Relatório final
    contagem_final = {}
    for item in dataset:
        contagem_final[item["classe"]] = contagem_final.get(item["classe"], 0) + 1

    print(f"\nAdicionados: {adicionados} registros")
    print(f"Total final: {len(dataset)} amostras")
    print("\nDistribuição final:")
    meta = 100
    for cls, qtd in sorted(contagem_final.items()):
        status = "✅" if qtd >= meta else "⚠️"
        barra  = "█" * min(qtd // 10, 50)
        print(f"  {status} {cls:10s}: {qtd:4d} {barra}")

    print("\nPróximo passo: python src/preprocessar.py && python src/treinar_modelo.py")

if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()