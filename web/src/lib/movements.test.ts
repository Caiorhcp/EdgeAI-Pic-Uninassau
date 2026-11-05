import { describe, expect, it } from "vitest";
import { daysBetween, describeMovement, humanDuration, milestoneOf, parseDatajudDate, redistributions } from "./movements";

describe("milestoneOf", () => {
  it("nomes reais de movimentação (TPU)", () => {
    expect(milestoneOf("Distribuição")).toBe("Distribuição");
    expect(milestoneOf("Audiência de conciliação realizada")).toBe("Audiência");
    expect(milestoneOf("Procedência em Parte")).toBe("Decisão");
    expect(milestoneOf("Não-Provimento")).toBe("Decisão");
    expect(milestoneOf("Recurso Inominado Cível")).toBe("Recurso");
    expect(milestoneOf("Trânsito em julgado")).toBe("Trânsito em julgado");
    expect(milestoneOf("Baixa Definitiva")).toBe("Baixa / arquivamento");
    expect(milestoneOf("Juntada de Petição")).toBeNull();
    expect(milestoneOf("Decurso de Prazo")).toBeNull();
  });
});

describe("dados reais do Datajud (TRF1, JEF)", () => {
  it("'Definitivo' sozinho e o código 246 são arquivamento", () => {
    expect(milestoneOf("Definitivo", 246)).toBe("Baixa / arquivamento");
    expect(milestoneOf("Definitivo")).toBe("Baixa / arquivamento");
    expect(describeMovement({ name: "Definitivo", code: 246 })).toBe("Arquivamento definitivo");
  });

  it("ausência do autor é decisão; complementos entram na descrição", () => {
    expect(milestoneOf("Ausência do autor à audiência", 11376)).toBe("Decisão");
    expect(describeMovement({ name: "Audiência", code: 970, details: ["realizada", "instrução e julgamento"] }))
      .toBe("Audiência (realizada; instrução e julgamento)");
  });

  it("redistribuição entre órgãos", () => {
    const moves = [ // mais nova primeiro, como vem da API
      { date: "2020-11-12", body: "08ª Vara JEF- Manaus" },
      { date: "2020-03-27", body: "08ª Vara JEF- Manaus" },
      { date: "2020-03-26", body: "Tefé" },
      { date: "2018-10-30", body: "Tefé" },
    ];
    expect(redistributions(moves)).toEqual([{ date: "2020-03-27", from: "Tefé", to: "08ª Vara JEF- Manaus" }]);
  });
});

describe("datas e durações", () => {
  it("formatos do Datajud", () => {
    expect(parseDatajudDate("20240314100000")?.toISOString().slice(0, 10)).toBe("2024-03-14");
    expect(parseDatajudDate("2024-03-14T10:00:00.000Z")?.toISOString().slice(0, 10)).toBe("2024-03-14");
    expect(parseDatajudDate("lixo")).toBeNull();
  });

  it("durações legíveis", () => {
    expect(daysBetween(new Date("2026-01-01"), new Date("2026-01-31"))).toBe(30);
    expect(humanDuration(1)).toBe("1 dia");
    expect(humanDuration(45)).toBe("45 dias");
    expect(humanDuration(400)).toBe("13 meses");
    expect(humanDuration(1200)).toBe("3 anos e 3 meses");
  });
});
