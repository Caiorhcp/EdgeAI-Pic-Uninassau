import { describe, expect, it } from "vitest";
import { extractEntities } from "./ner";
import { fixOcrText } from "./pdf";

describe("fixOcrText", () => {
  it("recupera e-mail com @ lido como Q (saída real do tesseract)", () => {
    const fixed = fixOcrText("Intimem-se. Contato: fulano Qexemplo.com\n");
    expect(fixed).toContain("fulano@exemplo.com");
    expect(extractEntities(fixed).map((e) => e.type)).toContain("EMAIL");
  });

  it("outras leituras comuns do @", () => {
    expect(fixOcrText("joao.silva©tjsp.jus.br")).toBe("joao.silva@tjsp.jus.br");
    expect(fixOcrText("maria @ escritorio.adv.br")).toBe("maria@escritorio.adv.br");
  });

  it("não mexe em texto comum", () => {
    const text = "O réu Qualquer deve pagar. Acesse www.stf.jus.br para consultar.";
    expect(fixOcrText(text)).toBe(text);
  });
});
