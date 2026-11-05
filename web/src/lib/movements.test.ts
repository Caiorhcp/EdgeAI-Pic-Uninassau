import { describe, expect, it } from "vitest";
import { daysBetween, humanDuration, milestoneOf, parseDatajudDate } from "./movements";

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
