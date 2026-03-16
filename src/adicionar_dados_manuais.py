# src/adicionar_dados_manuais.py
import os, json

NOVOS = {
    "acordao": [
        "ACÓRDÃO. Por unanimidade, a Turma negou provimento ao recurso especial, mantendo o acórdão recorrido que reconheceu a responsabilidade civil da empresa por falha na prestação de serviços.",
        "EMENTA: Direito do Consumidor. Vício do produto. Responsabilidade objetiva do fornecedor. Dano moral configurado. Indenização arbitrada com base nos princípios da razoabilidade e proporcionalidade.",
        "Recurso Especial. Direito Civil. Dano moral. Protesto indevido de título. Negativação indevida. Dano in re ipsa. Dispensa de prova do prejuízo. Precedentes. Recurso não provido.",
        "DECISÃO: Nego seguimento ao agravo, porquanto o acórdão recorrido está em consonância com a jurisprudência desta Corte, incidindo, por analogia, o enunciado da Súmula 83 do STJ.",
        "Por maioria, o Tribunal deu provimento ao recurso de apelação para condenar a ré ao pagamento de danos materiais e morais, vencido o relator que mantinha a improcedência.",
        "EMENTA: Previdenciário. Benefício por incapacidade. Laudo pericial conclusivo. Incapacidade total e permanente reconhecida. Concessão de aposentadoria por invalidez. Recurso provido.",
        "A responsabilidade do Estado é objetiva, na modalidade risco administrativo, conforme artigo 37, parágrafo 6, da Constituição Federal, prescindindo da demonstração de culpa do agente.",
        "ACÓRDÃO: STJ. Terceira Turma. Relator: Min. Paulo de Tarso. Por unanimidade, deu-se provimento ao recurso especial para afastar a prescrição reconhecida no acórdão recorrido.",
        "EMENTA: Processual Civil. Ação rescisória. Coisa julgada. Violação manifesta de norma jurídica. Não configurada. Pedido julgado improcedente por unanimidade do Pleno.",
        "Segundo entendimento consolidado neste Tribunal, o dano moral decorrente de inscrição indevida em cadastro restritivo de crédito é presumido, dispensando comprovação do abalo sofrido.",
        "DECISÃO MONOCRÁTICA: O presente recurso não merece prosperar, eis que a matéria já foi objeto de julgamento por esta Corte em sede de recurso repetitivo, Tema 931.",
        "Por votação unânime, o colegiado manteve a condenação da empresa ao pagamento de horas extras, adicional noturno e reflexos, conforme apurado na liquidação de sentença.",
        "EMENTA: Trabalhista. Dispensa por justa causa. Ausência de proporcionalidade. Reconhecimento de dispensa imotivada. Pagamento das verbas rescisórias determinado. Recurso provido.",
        "A Turma, por maioria, entendeu que a questão trazida a debate não revela ofensa direta à Constituição Federal, razão pela qual não é cabível o recurso extraordinário.",
        "ACÓRDÃO: Vistos, relatados e discutidos os autos, acordam os Desembargadores, por unanimidade de votos, em negar provimento ao apelo e manter a sentença em todos os seus termos.",
        "EMENTA: Família. Divórcio. Partilha de bens. Bem adquirido antes do casamento. Comunicabilidade. Não ocorrência. Regime de comunhão parcial. Recurso parcialmente provido.",
        "O prazo prescricional para a propositura de ação indenizatória em face do Estado é de cinco anos, nos termos do Decreto 20.910/32, contado da data do evento danoso.",
        "DECISÃO: O recurso extraordinário não apresenta repercussão geral, pois a questão debatida envolve interpretação de lei infraconstitucional, sem reflexo direto na Constituição.",
        "Por unanimidade, o Tribunal de Justiça declarou a nulidade do ato administrativo impugnado, por ausência de motivação e violação ao princípio da legalidade administrativa.",
        "EMENTA: Penal. Tráfico de drogas. Pena-base. Fundamentação idônea. Quantidade e natureza do entorpecente. Circunstâncias desfavoráveis reconhecidas. Recurso desprovido.",
        "A teoria da perda de uma chance exige que a oportunidade perdida seja real, séria e com probabilidade concreta de êxito, não se aplicando a meras expectativas ou possibilidades remotas.",
        "ACÓRDÃO: O recurso de apelação não merece provimento, pois a sentença de primeiro grau apreciou corretamente as provas dos autos e aplicou com acerto a legislação pertinente.",
        "EMENTA: Consumidor. Plano de saúde. Negativa de cobertura. Procedimento essencial. Abusividade reconhecida. Obrigação de custear o tratamento. Dano moral configurado.",
        "Nos termos da Súmula 385 do STJ, da anotação irregular em cadastro de proteção ao crédito, não cabe indenização por dano moral quando preexistente legítima inscrição.",
        "DECISÃO: Tendo em vista que a matéria é objeto de recurso repetitivo ainda não julgado pelo STJ, determino a suspensão do presente feito até o julgamento definitivo do paradigma.",
        "Por maioria de votos, o Plenário do STF fixou a seguinte tese em repercussão geral: É constitucional a inclusão do ICMS na base de cálculo da CIDE-Combustíveis.",
        "EMENTA: Administrativo. Concurso público. Eliminação. Teste de aptidão física. Critérios diferenciados por sexo. Constitucionalidade reconhecida. Segurança denegada.",
        "O entendimento desta Corte é no sentido de que os juros de mora nos danos extrapatrimoniais incidem a partir do evento danoso, nos termos da Súmula 54 do STJ.",
        "ACÓRDÃO: Direito Civil. Contrato de seguro. Recusa de pagamento da indenização. Dolo ou culpa grave do segurado. Ônus da prova da seguradora. Não comprovado. Recurso improvido.",
        "EMENTA: Tributário. IPTU. Progressividade. Função social da propriedade. Constitucionalidade reconhecida. Alíquotas diferenciadas por valor venal. Legalidade. Recurso desprovido.",
        "A responsabilidade civil do médico é subjetiva, dependendo da comprovação de culpa, salvo nas hipóteses de cirurgia estética, onde a obrigação assume natureza de resultado.",
        "DECISÃO MONOCRÁTICA: Nos termos do artigo 932 do CPC, nego seguimento ao recurso especial, porquanto o acórdão recorrido está em conformidade com a jurisprudência desta Corte.",
        "Por unanimidade, negou-se provimento ao agravo regimental, mantendo-se a decisão que havia determinado o sobrestamento do feito na origem até o julgamento do recurso repetitivo.",
        "EMENTA: Processual. Tutela antecipada. Requisitos. Probabilidade do direito. Perigo de dano. Presença. Concessão da medida. Decisão mantida. Agravo interno desprovido.",
        "O STJ firmou orientação de que a compensação de danos morais com débitos do autor com o réu é vedada, por se tratar de verba de caráter alimentar e personalíssimo.",
        "ACÓRDÃO: Família. Guarda compartilhada. Litígio entre os genitores. Cabimento. Prevalência do melhor interesse da criança. Sentença reformada. Recurso do genitor provido.",
        "EMENTA: Societário. Desconsideração da personalidade jurídica. Teoria maior. Fraude ou abuso comprovados. Redirecionamento da execução. Possibilidade. Recurso provido.",
        "Segundo pacífica jurisprudência desta Corte, a ausência de defesa técnica em processo administrativo disciplinar é causa de nulidade absoluta do procedimento.",
        "DECISÃO: Diante da comprovada hipossuficiência do recorrente, defiro o pedido de gratuidade da justiça para os fins do artigo 98 do Código de Processo Civil.",
        "Por maioria, o Tribunal reconheceu a repercussão geral da questão constitucional debatida, determinando a suspensão de todos os processos que versem sobre o mesmo tema.",
        "EMENTA: Execução Fiscal. Redirecionamento. Sócio-gerente. Dissolução irregular da sociedade. Presunção. Responsabilidade pessoal. Súmula 435 do STJ. Recurso desprovido.",
        "A aplicação do Código de Defesa do Consumidor às relações bancárias foi reconhecida pelo STJ na Súmula 297, sendo cabível a revisão das cláusulas abusivas nos contratos.",
        "ACÓRDÃO: O valor arbitrado a título de danos morais, no montante de R$ 15.000,00, mostra-se razoável e proporcional à extensão do dano, não comportando revisão nesta instância.",
        "EMENTA: Ambiental. Área de preservação permanente. Construção irregular. Demolição. Obrigação de fazer. Cabimento independente de culpa. Responsabilidade objetiva reconhecida.",
        "Nos termos do artigo 489, parágrafo 1, do CPC, não se considera fundamentada a decisão que se limita a invocar conceito jurídico indeterminado sem explicar o motivo da subsunção.",
    ],
    "contrato": [
        "Contrato de Prestação de Serviços de Tecnologia da Informação. O presente instrumento tem por objeto o desenvolvimento de sistema de gestão empresarial, conforme especificações do Anexo Técnico.",
        "O Contratante efetuará o pagamento mediante apresentação de nota fiscal de serviços, no prazo de 30 dias após o aceite formal de cada entrega prevista no cronograma.",
        "Fica expressamente vedado ao Contratado prestar serviços a empresas concorrentes do Contratante durante a vigência deste contrato e por 12 meses após seu encerramento.",
        "O presente instrumento rege-se pelas disposições do Código Civil Brasileiro, Lei 10.406/2002, e pelas normas aplicáveis à espécie, prevalecendo sempre a boa-fé das partes.",
        "A inexecução total ou parcial do contrato ensejará sua rescisão, com as consequências contratuais e legais, assegurado o contraditório e a ampla defesa da parte inadimplente.",
        "Contrato de Locação Comercial. O Locador cede ao Locatário, para uso comercial, o imóvel situado na Avenida Brasil, n. 500, pelo prazo de 24 meses e aluguel mensal de R$ 4.000,00.",
        "O Locatário não poderá sublocar, ceder ou emprestar o imóvel, ou utilizá-lo para fim diverso do estabelecido neste contrato, sob pena de rescisão e multa contratual.",
        "O aluguel será reajustado anualmente pela variação do IGPM acumulada no período, independentemente de notificação, sendo o novo valor cobrado a partir do mês subsequente.",
        "Contrato de Compra e Venda. O Vendedor vende ao Comprador o veículo marca Toyota, modelo Corolla, ano 2022, placa ABC-1234, pelo preço de R$ 95.000,00, à vista.",
        "O Vendedor garante que o bem descrito neste instrumento está livre e desembaraçado de quaisquer ônus, dívidas, hipotecas, penhoras ou gravames de qualquer natureza.",
        "Contrato de Trabalho. O empregador contrata o empregado para exercer a função de Analista de Sistemas, com salário mensal de R$ 6.500,00, em regime de trabalho de 44 horas semanais.",
        "O empregado se compromete a guardar sigilo sobre todos os dados, informações e processos internos da empresa, mesmo após o término do contrato de trabalho.",
        "Contrato de Franquia. O Franqueador concede ao Franqueado o direito de uso da marca e sistema operacional, mediante pagamento de taxa inicial de R$ 80.000,00 e royalties mensais.",
        "O Franqueado compromete-se a seguir rigorosamente os padrões, processos e procedimentos estabelecidos no Manual de Operações, parte integrante deste instrumento.",
        "Contrato de Licença de Uso de Software. O Licenciante autoriza o Licenciado a utilizar o software na versão atual, de forma não exclusiva, pelo prazo de 12 meses.",
        "O Licenciado não poderá copiar, modificar, distribuir, sublicenciar ou realizar engenharia reversa do software objeto deste contrato, sob pena de rescisão imediata.",
        "Contrato de Empreitada. O Empreiteiro se obriga a executar a obra de reforma do imóvel conforme projeto aprovado, pelo preço global de R$ 120.000,00, no prazo de 90 dias.",
        "O pagamento será realizado em três parcelas iguais: 30% na assinatura, 40% na conclusão da estrutura e 30% na entrega final com aceite do Contratante.",
        "Contrato de Distribuição. O Distribuidor fica autorizado a comercializar os produtos do Fabricante na região Sul do Brasil, com exclusividade pelo prazo de 2 anos.",
        "O Distribuidor compromete-se a manter estoque mínimo dos produtos conforme tabela do Anexo A, bem como a atingir as metas mensais de vendas estabelecidas pelas partes.",
        "Termo Aditivo ao Contrato de Prestação de Serviços. As partes resolvem aditar o contrato original para prorrogar seu prazo por mais 6 meses e reajustar o valor mensal.",
        "Contrato de Comodato. O Comodante empresta gratuitamente ao Comodatário o bem descrito no Anexo I, pelo prazo de 12 meses, devendo ser devolvido no estado em que recebido.",
        "Contrato de Mútuo. O Mutuante empresta ao Mutuário a importância de R$ 50.000,00, que deverá ser devolvida no prazo de 24 meses, com juros de 1,5% ao mês.",
        "O Mutuário autoriza o desconto em conta corrente das parcelas mensais de amortização, não podendo alegar desconhecimento dos valores ou datas de vencimento.",
        "Contrato de Cessão de Crédito. O Cedente cede ao Cessionário todos os direitos creditórios decorrentes das duplicatas descritas no Anexo A, pelo valor de R$ 200.000,00.",
        "Contrato de Parceria Empresarial. As partes estabelecem parceria para desenvolvimento e comercialização conjunta de produto inovador, com divisão igualitária dos lucros.",
        "Instrumento Particular de Promessa de Compra e Venda. O Promitente Vendedor compromete-se a vender ao Promitente Comprador o imóvel matriculado sob n. 45.678.",
        "O sinal pago neste ato, no valor de R$ 30.000,00, será imputado no preço final, sendo perdido pelo Promitente Comprador em caso de desistência injustificada.",
        "Contrato de Gestão. A Organização Social compromete-se a executar o programa de trabalho aprovado, mediante repasse de recursos públicos conforme cronograma de desembolso.",
        "O presente contrato de prestação de serviços médicos rege-se pela Lei 8.078/90, sendo nulas de pleno direito as cláusulas que estabeleçam limitações ao direito do paciente.",
        "Contrato de Patrocínio. O Patrocinador aportará recursos financeiros para realização do evento em troca de inserção de sua marca nos materiais de divulgação.",
        "O contratado se responsabiliza pela obtenção de todas as licenças, alvarás e autorizações necessárias para a execução do objeto deste instrumento junto aos órgãos competentes.",
        "Contrato de Manutenção. A empresa prestadora se obriga a realizar manutenção preventiva e corretiva dos equipamentos listados no Anexo I, com SLA de 4 horas para atendimento.",
        "O presente contrato de intermediação imobiliária confere à imobiliária poderes para negociar a venda do imóvel, fazendo jus à comissão de 6% sobre o valor da transação.",
        "Contrato de Seguro de Vida. A Seguradora garante ao Segurado, mediante pagamento do prêmio mensal, o pagamento do capital segurado aos beneficiários indicados.",
        "As partes elegem o procedimento de mediação e arbitragem para resolução de conflitos, renunciando ao foro judicial, exceto para medidas cautelares de urgência.",
        "Contrato de Assessoria Jurídica. O Advogado prestará serviços de consultoria jurídica empresarial, mediante honorários mensais fixos acrescidos de êxito nas causas litigiosas.",
        "O presente instrumento é celebrado em conformidade com as disposições do Marco Civil da Internet, Lei 12.965/2014, e demais normas aplicáveis ao ambiente digital.",
        "Contrato de Desenvolvimento de Software sob Encomenda. A desenvolvedora se compromete a entregar o sistema nas condições técnicas especificadas, com garantia de 12 meses.",
        "Em cumprimento à LGPD — Lei 13.709/2018 — as partes estabelecem que os dados pessoais tratados no âmbito deste contrato terão finalidade exclusivamente contratual.",
        "Contrato de Prestação de Serviços Educacionais. A Instituição se compromete a ministrar o curso conforme grade curricular aprovada, garantindo a emissão do certificado.",
        "O cancelamento da matrícula após o início das aulas implicará pagamento de multa rescisória equivalente a 20% das mensalidades remanescentes do semestre em curso.",
        "Contrato de Agenciamento. O Agente compromete-se a representar o Representado perante terceiros, buscando oportunidades de negócio mediante comissão sobre as vendas efetivadas.",
        "Todas as notificações, intimações e comunicações entre as partes deverão ser realizadas por escrito, sendo válidas quando enviadas por e-mail com confirmação de leitura.",
        "O presente instrumento entra em vigor na data de sua assinatura, ficando condicionada sua eficácia ao implemento da condição suspensiva prevista na cláusula décima.",
    ],
}

def main():
    print("Adicionando dados manuais ao dataset...")

    with open("data/raw/dataset_juridico.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    textos_existentes = {item["texto"][:80] for item in dataset}
    adicionados = 0

    for classe, textos in NOVOS.items():
        for texto in textos:
            if texto[:80] not in textos_existentes:
                dataset.append({"texto": texto, "classe": classe,
                                 "fonte": "curadoria-manual"})
                textos_existentes.add(texto[:80])
                adicionados += 1

    with open("data/raw/dataset_juridico.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    contagem = {}
    for item in dataset:
        contagem[item["classe"]] = contagem.get(item["classe"], 0) + 1

    print(f"Adicionados: {adicionados} registros")
    print(f"Total final: {len(dataset)} amostras\n")
    print("Distribuição final:")
    for cls, qtd in sorted(contagem.items()):
        status = "✅" if qtd >= 100 else "⚠️"
        barra  = "█" * min(qtd // 10, 50)
        print(f"  {status} {cls:10s}: {qtd:4d} {barra}")

if __name__ == "__main__":
    main()