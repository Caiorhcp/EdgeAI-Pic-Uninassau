import type { Page } from "@/lib/pdf";

// Documento fictício para demonstração. Nomes, CPF, CNPJ e contatos são inventados
// (CPF/CNPJ com dígitos verificadores válidos, mas sem titular real).
export const EXAMPLE_PAGES: Page[] = [
  {
    number: 1,
    ocr: false,
    text: `EXCELENTÍSSIMO SENHOR DESEMBARGADOR PRESIDENTE DA TURMA RECURSAL DOS JUIZADOS ESPECIAIS FEDERAIS DO RIO GRANDE DO SUL

Processo nº 5001234-05.2023.4.04.7104

MARIA DAS GRAÇAS EXEMPLO, brasileira, aposentada, inscrita no CPF sob o nº 529.982.247-25, residente na Rua das Acácias, 123, Passo Fundo/RS, CEP 99010-000, telefone (54) 99876-5432, e-mail maria.exemplo@email.com, por seu advogado infra-assinado, Carlos Alberto Exemplo, OAB/RS 12.345, vem, respeitosamente, à presença de Vossa Excelência, inconformada com o acórdão proferido pela Turma Recursal, interpor o presente

RECURSO EXTRAORDINÁRIO

com fundamento no art. 102, inciso III, alínea a, da Constituição Federal, em face da UNIÃO, pelas razões a seguir expostas.

RAZÕES DO RECURSO EXTRAORDINÁRIO. Recorrente: Maria das Graças Exemplo. Recorrida: União. Egrégio Supremo Tribunal Federal, Colenda Turma, Ínclitos Ministros.

DOS FATOS. A recorrente ajuizou ação perante o Juizado Especial Federal postulando a revisão de seu benefício previdenciário. A sentença julgou improcedente o pedido, e a Turma Recursal negou provimento ao recurso inominado, mantendo a decisão por seus próprios fundamentos. Contra esse acórdão interpõe-se o presente recurso extraordinário.`,
  },
  {
    number: 2,
    ocr: false,
    text: `DA REPERCUSSÃO GERAL. A questão debatida ultrapassa os interesses subjetivos da causa, pois envolve a correção monetária de condenações impostas à Fazenda Pública, matéria do Tema 810 do Supremo Tribunal Federal, que alcança milhares de benefícios previdenciários.

DO PREQUESTIONAMENTO. A matéria constitucional foi expressamente debatida no acórdão recorrido, que afastou a aplicação do art. 5º, inciso XXXVI, da Constituição Federal.

DO MÉRITO. O acórdão recorrido violou o direito adquirido da recorrente ao deixar de aplicar a Lei 8.213/1991 vigente à época da concessão do benefício. A jurisprudência do STF, consolidada na Súmula 359, garante que os proventos regulam-se pela lei vigente ao tempo em que o segurado reuniu os requisitos.

DOS PEDIDOS. Ante o exposto, requer seja o presente recurso extraordinário admitido e, no mérito, provido, para reformar o acórdão e condenar a ré ao pagamento das diferenças, estimadas em R$ 48.320,15.

Passo Fundo, 14 de março de 2024.`,
  },
  {
    number: 3,
    ocr: false,
    text: `PODER JUDICIÁRIO. JUSTIÇA FEDERAL. TURMA RECURSAL DO RIO GRANDE DO SUL.

DECISÃO. Trata-se de recurso extraordinário interposto contra acórdão desta Turma Recursal. Verifico que o recurso não preenche os requisitos de admissibilidade, uma vez que a alegada ofensa à Constituição, se existente, seria meramente reflexa, dependendo da prévia análise da legislação infraconstitucional, o que não autoriza a abertura da via extraordinária, conforme reiterada jurisprudência do STF.

Ante o exposto, NÃO ADMITO o recurso extraordinário, nos termos do art. 1.030, inciso V, do Código de Processo Civil. Intime-se a parte recorrente, que poderá interpor agravo no prazo de 15 (quinze) dias.

Porto Alegre, 2 de maio de 2024. Juiz Federal Presidente da Turma Recursal.`,
  },
];
