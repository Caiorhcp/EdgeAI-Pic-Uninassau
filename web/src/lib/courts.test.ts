import { expect, it } from "vitest";
import { portalFor } from "./courts";

const withDv = (n: string, year: string, j: string, tr: string, origin: string) => {
  const dv = 98 - Number(BigInt(n + year + j + tr + origin + "00") % 97n);
  return `${n}-${String(dv).padStart(2, "0")}.${year}.${j}.${tr}.${origin}`;
};

it("TRF1 (processo real usado nos testes do Datajud) aponta para a consulta nova, não para o listView.seam", () => {
  const p = portalFor("0000832-35.2018.4.01.3202")!;
  expect(p).toMatchObject({ court: "TRF1", system: "PJe", prefilled: false });
  expect(p.url).not.toContain("listView.seam");
});

it("tribunais que falharam no teste do navegador caem na busca", () => {
  const n = (j: string, tr: string) => {
    const dv = 98 - Number(BigInt("0000001" + "2024" + j + tr + "0001" + "00") % 97n);
    return `0000001-${String(dv).padStart(2, "0")}.2024.${j}.${tr}.0001`;
  };
  for (const tr of ["07", "19", "16", "09"]) expect(portalFor(n("8", tr))?.url).toContain("google.com/search"); // TJDFT, TJRJ, TJPR, TJGO
});

it("TJSP abre a busca já com o número", () => {
  const n = withDv("0001234", "2025", "8", "26", "0114");
  const p = portalFor(n)!;
  expect(p).toMatchObject({ court: "TJSP", system: "e-SAJ", prefilled: true });
  expect(p.url).toContain(n);
});

it("TRT usa o PJe-JT com o número no endereço", () => {
  const n = withDv("1000000", "2020", "5", "02", "0001");
  expect(portalFor(n)?.url).toBe(`https://pje.trt2.jus.br/consultaprocessual/detalhe-processo/${n}`);
});

it("tribunal fora da lista vira busca; número inválido não gera link", () => {
  expect(portalFor(withDv("0000001", "2024", "8", "01", "0001"))?.url).toContain("google.com/search"); // TJAC
  expect(portalFor("0000832-36.2018.4.01.3202")).toBeNull();
});
