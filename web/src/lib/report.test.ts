import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { EXAMPLE_PAGES } from "../app/example";
import { analyze } from "./analyze";
import { Classifier, type Model } from "./classifier";
import type { Instance } from "./datajud";
import { buildReport } from "./report";

const clf = new Classifier(JSON.parse(readFileSync(join(__dirname, "../../public/model.json"), "utf-8")) as Model);
const result = analyze(clf, EXAMPLE_PAGES);
const now = new Date("2026-11-05T12:00:00Z");

// O PDF sai sem compressão: o texto fica legível no conteúdo (acentos como escapes octais, por isso só ASCII aqui)
const textOf = (pdf: ReturnType<typeof buildReport>) => pdf.output();

describe("buildReport", () => {
  it("documento único com as seções principais e dados pessoais mascarados", () => {
    const pdf = buildReport({ docs: [{ name: "exemplo.pdf", result }], intimation: "2026-11-05", dockets: {}, now });
    const out = textOf(pdf);
    expect(out.startsWith("%PDF-")).toBe(true);
    // títulos de seção saem em maiúsculas ("I. IDENTIFICAÇÃO")
    for (const s of ["I. IDENTIFICA", "II. DAS PARTES E PROCURADORES", "III. DO DISPOSITIVO", "DOS PRAZOS PROCESSUAIS", "DOS VALORES", "NOTA METODOL"]) {
      expect(out).toContain(s);
    }
    expect(out).toContain("27/11/2026"); // termo final do prazo de 15 dias úteis
    expect(out).not.toContain("529.982.247-25"); // CPF do exemplo não aparece em claro
    expect(out).toContain("Carlos Alberto Exemplo");
  });

  it("lote com quadro-resumo e andamento do Datajud", () => {
    const docket: Instance[] = [{
      court: "TRF4", degree: "Turma Recursal", className: "Recurso Inominado Cível", subjects: ["Dano Moral"],
      body: "5ª Turma Recursal", filedAt: "2025-04-25T00:00:00Z", system: "eproc", updatedAt: null,
      movements: [{ date: "2026-10-01T00:00:00Z", name: "Baixa Definitiva" }, { date: "2025-05-01T00:00:00Z", name: "Distribuição" }],
    }];
    const pdf = buildReport({
      docs: [{ name: "a.pdf", result }, { name: "b.pdf", result }],
      intimation: "2026-11-05",
      dockets: { [result.processNumbers[0]]: docket },
      now,
    });
    const out = textOf(pdf);
    expect(out).toContain("Quadro-resumo");
    expect(out).toContain("Documento 2 de 2");
    expect(out).toContain("Baixa Definitiva");
    expect(pdf.getNumberOfPages()).toBeGreaterThanOrEqual(3);
  });
});
