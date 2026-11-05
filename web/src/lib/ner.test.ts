import { describe, expect, it } from "vitest";
import { anonymize, exposureScore, extractEntities, isValidCnpj, isValidCpf } from "./ner";

// CPF/CNPJ gerados com dígitos verificadores válidos; não pertencem a ninguém real.
const CPF = "529.982.247-25";
const CNPJ = "11.222.333/0001-81";

describe("validação", () => {
  it("CPF", () => {
    expect(isValidCpf(CPF)).toBe(true);
    expect(isValidCpf("529.982.247-26")).toBe(false);
    expect(isValidCpf("111.111.111-11")).toBe(false);
  });
  it("CNPJ", () => {
    expect(isValidCnpj(CNPJ)).toBe(true);
    expect(isValidCnpj("11.222.333/0001-82")).toBe(false);
  });
});

describe("extractEntities", () => {
  const text =
    `Autos nº 0001234-56.2023.8.26.0100, TJSP. O autor, CPF ${CPF}, e-mail fulano@exemplo.com, ` +
    `telefone (11) 98765-4321, contra a empresa CNPJ ${CNPJ}, nos termos do art. 5º da Lei 13.709/2018 ` +
    `e da Súmula 7 do STJ, em 10 de março de 2024, valor R$ 1.500,00.`;
  const types = extractEntities(text).map((e) => e.type);

  it("encontra entidades jurídicas e pessoais", () => {
    expect(types).toEqual(
      expect.arrayContaining(["PROCESSO_CNJ", "TRIBUNAL", "CPF", "EMAIL", "TELEFONE", "CNPJ", "ARTIGO", "LEI", "SUMULA", "DATA", "VALOR"]),
    );
  });

  it("artigo com milhar", () => {
    expect(extractEntities("nos termos do art. 1.030 do CPC").map((e) => e.value)).toContain("art. 1.030");
  });

  it("ignora sequência com dígito verificador errado", () => {
    expect(extractEntities("CPF 529.982.247-26").map((e) => e.type)).not.toContain("CPF");
  });

  it("número de processo não vira CPF", () => {
    expect(extractEntities("0001234-56.2023.8.26.0100").map((e) => e.type)).toEqual(["PROCESSO_CNJ"]);
  });

  it("anonimiza só dados pessoais", () => {
    const out = anonymize(text, extractEntities(text));
    expect(out).not.toContain(CPF);
    expect(out).not.toContain("fulano@exemplo.com");
    expect(out).toContain("[CPF]");
    expect(out).toContain("Lei 13.709/2018");
  });

  it("score de exposição", () => {
    expect(exposureScore(extractEntities(text)).level).toBe("Alta");
    expect(exposureScore(extractEntities("Súmula 7 do STJ")).score).toBe(0);
  });
});
