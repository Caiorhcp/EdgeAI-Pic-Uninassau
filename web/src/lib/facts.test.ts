import { describe, expect, it } from "vitest";
import { EXAMPLE_PAGES } from "../app/example";
import { findHeader, findLawyers, findOutcomes, findParties, findRequests, labelValues, parseDate, timeline } from "./facts";
import { extractEntities } from "./ner";

const example = EXAMPLE_PAGES.map((p) => p.text).join("\n\n");

describe("findParties", () => {
  it("rótulos e qualificação", () => {
    const parties = findParties(example);
    expect(parties).toEqual(
      expect.arrayContaining([
        { role: "Recorrente", name: "Maria das Graças Exemplo", side: "ativo" },
        { role: "Recorrido", name: "União", side: "passivo" },
      ]),
    );
  });

  it("autor e réu em linhas", () => {
    expect(findParties("Autor: João da Silva\nRé: Banco Exemplo S.A.\n")).toEqual([
      { role: "Autor", name: "João da Silva", side: "ativo" },
      { role: "Réu", name: "Banco Exemplo S.A.", side: "passivo" },
    ]);
  });
});

describe("findLawyers", () => {
  it("com e sem nome", () => {
    expect(findLawyers("Advogada: Ana Paula Souza, OAB/SP 123.456. Também atua OAB/RS 12.345.")).toEqual([
      { name: "Ana Paula Souza", oab: "OAB/SP 123.456" },
      { name: null, oab: "OAB/RS 12.345" },
    ]);
  });
});

describe("findOutcomes", () => {
  it("dispositivo da peça antes da decisão citada", () => {
    const out = findOutcomes(example);
    expect(out[0]).toMatchObject({ label: "Não admitido", own: true });
    expect(out.map((o) => o.label)).toContain("Improcedente"); // "A sentença julgou improcedente"
    expect(out.find((o) => o.label === "Improcedente")?.own).toBe(false);
  });

  it("parcialmente procedente não conta como procedente", () => {
    expect(findOutcomes("Ante o exposto, julgo parcialmente procedente o pedido.").map((o) => o.label)).toEqual([
      "Parcialmente procedente",
    ]);
  });
});

describe("cabeçalho e pedidos", () => {
  const sentenca =
    "PODER JUDICIÁRIO. JUSTIÇA ESTADUAL.\n2ª VARA CÍVEL DA COMARCA DE CAMPINAS\nJuíza de Direito: Dra. Helena Fictícia Prado\n" +
    "SENTENÇA. Trata-se de ação de indenização por danos morais em que o autor alega inscrição indevida.";

  it("juízo, comarca, magistrado e natureza da ação", () => {
    expect(findHeader(sentenca)).toEqual({
      body: "2ª Vara Cível da Comarca de Campinas",
      district: "Campinas",
      judge: "Dra. Helena Fictícia Prado",
      action: "ação de indenização por danos morais",
    });
  });

  it("relator em acórdão e campos ausentes", () => {
    const h = findHeader("ACÓRDÃO. 5ª Turma Recursal do Rio Grande do Sul. Relator: Des. Paulo Exemplo Lima\nVistos.");
    expect(h.body).toBe("5ª Turma Recursal do Rio Grande do Sul");
    expect(h.judge).toBe("Des. Paulo Exemplo Lima");
    expect(h.district).toBeNull();
  });

  it("pedidos", () => {
    expect(findRequests(example)).toEqual([
      "Ante o exposto, requer seja o presente recurso extraordinário admitido e, no mérito, provido, para reformar o acórdão e condenar a ré ao pagamento das diferenças, estimadas em R$ 48.320,15.",
    ]);
  });
});

describe("valores e datas", () => {
  it("rótulo pelo contexto", () => {
    const text = "Atribui-se à causa o valor da causa de R$ 10.000,00 e pede danos morais de R$ 5.000,00.";
    expect(labelValues(text, extractEntities(text))).toEqual([
      { label: "Valor da causa", value: "R$ 10.000,00" },
      { label: "Danos morais", value: "R$ 5.000,00" },
    ]);
  });

  it("datas por extenso e numéricas, em ordem", () => {
    expect(parseDate("14 de março de 2024")).toBe("2024-03-14");
    expect(parseDate("02/05/24")).toBe("2024-05-02");
    expect(timeline(example, extractEntities(example)).map((e) => e.date)).toEqual(["2024-03-14", "2024-05-02"]);
  });
});
