import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { analyze } from "./analyze";
import { Classifier, type Model } from "./classifier";

const clf = new Classifier(JSON.parse(readFileSync(join(__dirname, "../../public/model.json"), "utf-8")) as Model);

const sentenca =
  "PODER JUDICIÁRIO. JUSTIÇA FEDERAL. Juizado Especial Cível. SENTENÇA. Relatório dispensado nos termos do art. 38 " +
  "da Lei 9.099/95. Fundamento e decido. Trata-se de ação em que a parte autora pretende a revisão do benefício. " +
  "Ante o exposto, JULGO PROCEDENTE o pedido e condeno o réu ao pagamento das diferenças. Sem custas e honorários.";
const recurso =
  "EXCELENTÍSSIMO SENHOR PRESIDENTE DA TURMA RECURSAL. A UNIÃO, inconformada com o acórdão, vem interpor " +
  "RECURSO EXTRAORDINÁRIO com fundamento no art. 102, III, a, da Constituição Federal. Da repercussão geral. " +
  "Do prequestionamento. Requer seja admitido e provido o presente recurso extraordinário.";

const despacho =
  "PODER JUDICIÁRIO JUSTIÇA FEDERAL TURMA RECURSAL. DECISÃO. Trata-se de recurso extraordinário interposto pela parte " +
  "autora em face de acórdão proferido pela Turma Recursal. Decido. O recurso não merece seguimento. O Supremo Tribunal " +
  "Federal reconheceu a inexistência de repercussão geral. Ante o exposto, nego seguimento ao recurso extraordinário. Intimem-se.";

describe("analyze", () => {
  const res = analyze(clf, [
    { number: 1, text: recurso, ocr: false },
    { number: 2, text: recurso, ocr: false },
    { number: 3, text: sentenca, ocr: false },
    { number: 4, text: despacho, ocr: false },
  ]);

  it("classifica cada página e agrupa em trechos", () => {
    expect(res.segments).toEqual([
      { label: "Petição de RE", from: 1, to: 2 },
      { label: "Sentença", from: 3, to: 3 },
      { label: "Despacho", from: 4, to: 4 },
    ]);
  });

  it("probabilidades do documento somam 1", () => {
    expect(res.ranking.reduce((s, p) => s + p.probability, 0)).toBeCloseTo(1, 6);
    expect(res.ranking[0].label).toBe("Petição de RE");
  });

  it("extrai entidades e resumo", () => {
    expect(res.entities.map((e) => e.type)).toContain("LEI");
    expect(res.summary.length).toBeGreaterThan(0);
  });
});
