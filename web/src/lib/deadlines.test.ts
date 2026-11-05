import { describe, expect, it } from "vitest";
import { dueDate, easter, findDeadlines, isBusinessDay } from "./deadlines";

const iso = (d: Date | null) => d?.toISOString().slice(0, 10);
const utc = (s: string) => new Date(`${s}T00:00:00Z`);

describe("findDeadlines", () => {
  it("prazos com número, por extenso e com parênteses", () => {
    const text =
      "Intime-se a parte recorrida para apresentar contrarrazões no prazo de 15 (quinze) dias. " +
      "Cumpra-se em cinco dias corridos. Manifeste-se em até 48 horas. O contrato vigora em 2 de maio de 2024.";
    const found = findDeadlines(text);
    expect(found.map((d) => [d.amount, d.unit, d.businessDays])).toEqual([
      [15, "dias", true],
      [5, "dias", false],
      [48, "horas", false],
    ]);
    expect(found[0].excerpt).toContain("contrarrazões");
  });
});

describe("calendário", () => {
  it("Páscoa", () => {
    expect(iso(easter(2024))).toBe("2024-03-31");
    expect(iso(easter(2026))).toBe("2026-04-05");
  });

  it("dias sem expediente", () => {
    expect(isBusinessDay(utc("2026-11-20"))).toBe(false); // Consciência Negra
    expect(isBusinessDay(utc("2026-02-17"))).toBe(false); // terça de Carnaval
    expect(isBusinessDay(utc("2026-01-10"))).toBe(false); // recesso (art. 220)
    expect(isBusinessDay(utc("2026-11-23"))).toBe(true);
  });
});

describe("dueDate", () => {
  const d = (amount: number, businessDays = true) => ({ amount, unit: "dias" as const, businessDays, excerpt: "" });

  it("15 dias úteis pulam fim de semana e feriado", () => {
    // Intimação qui 05/11/2026: começa sex 06; pula sábados, domingos e 20/11 → vence sex 27/11
    expect(iso(dueDate("2026-11-05", d(15)))).toBe("2026-11-27");
  });

  it("prazo suspenso no recesso", () => {
    // Intimação sex 18/12/2026: 1º dia útil sáb? não; seg 21/12 está no recesso; volta em qui 21/01/2027
    expect(iso(dueDate("2026-12-18", d(1)))).toBe("2027-01-21");
  });

  it("dias corridos com vencimento prorrogado", () => {
    // 2 dias corridos a partir de qui 05/11/2026 caem no sáb 07 → prorroga para seg 09
    expect(iso(dueDate("2026-11-05", d(2, false)))).toBe("2026-11-09");
  });

  it("horas não têm data calculada", () => {
    expect(dueDate("2026-11-05", { amount: 48, unit: "horas", businessDays: false, excerpt: "" })).toBeNull();
  });
});
