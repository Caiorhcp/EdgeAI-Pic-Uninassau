import { describe, expect, it } from "vitest";
import { datajudAlias, parseCnj } from "./cnj";

// Calcula o DV para montar casos de teste sem depender de processos reais
function withDv(n: string, year: string, j: string, tr: string, origin: string): string {
  const dv = 98 - Number(BigInt(n + year + j + tr + origin + "00") % 97n);
  return `${n}-${String(dv).padStart(2, "0")}.${year}.${j}.${tr}.${origin}`;
}

describe("parseCnj", () => {
  // Número real publicado (procedimento no CNJ, citado em migalhas.com.br)
  it("aceita número com DV correto, com ou sem pontuação", () => {
    expect(parseCnj("0003741-14.2019.2.00.0000")?.formatted).toBe("0003741-14.2019.2.00.0000");
    expect(parseCnj("00037411420192000000")?.formatted).toBe("0003741-14.2019.2.00.0000");
  });

  it("rejeita DV errado e tamanho errado", () => {
    expect(parseCnj("0003741-15.2019.2.00.0000")).toBeNull();
    expect(parseCnj("123")).toBeNull();
  });
});

describe("datajudAlias", () => {
  const alias = (j: string, tr: string) => datajudAlias(parseCnj(withDv("0001234", "2023", j, tr, "0100"))!);

  it("mapeia cada ramo da Justiça", () => {
    expect(alias("3", "00")).toBe("stj");
    expect(alias("4", "04")).toBe("trf4");
    expect(alias("5", "00")).toBe("tst");
    expect(alias("5", "02")).toBe("trt2");
    expect(alias("6", "07")).toBe("tre-dft");
    expect(alias("8", "26")).toBe("tjsp");
    expect(alias("8", "07")).toBe("tjdft");
    expect(alias("9", "13")).toBe("tjmmg");
  });

  it("STF e CNJ não estão no Datajud", () => {
    expect(alias("1", "00")).toBeNull();
    expect(alias("2", "00")).toBeNull();
  });
});
