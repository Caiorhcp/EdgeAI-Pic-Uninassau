import { describe, expect, it } from "vitest";
import { EXAMPLE_PAGES } from "../app/example";
import { findLawyers, findOutcomes, findParties, labelValues, parseDate, timeline } from "./facts";
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
      { role: "Réu", name: "Banco Exemplo S.A", side: "passivo" },
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
