import { expect, it } from "vitest";
import { sentenceAt } from "./text";

it("não corta em ponto de milhar nem em quebra de linha", () => {
  const text = "Fundamento e decido. Ante o exposto, julgo procedente o pedido de danos morais de R$\n8.000,00, com correção. Intimem-se.";
  const at = text.indexOf("julgo");
  expect(sentenceAt(text, at)).toBe("Ante o exposto, julgo procedente o pedido de danos morais de R$ 8.000,00, com correção.");
});

it("abreviações jurídicas não encerram a frase", () => {
  const text = "Relatório. Ante o exposto, não admito o recurso, nos termos do art. 1.030, V, do CPC. Intimem-se.";
  expect(sentenceAt(text, text.indexOf("não admito"))).toBe("Ante o exposto, não admito o recurso, nos termos do art. 1.030, V, do CPC.");
});

it("trecho no fim do texto e trecho longo", () => {
  expect(sentenceAt("Primeira. Segunda sem ponto", 12)).toBe("Segunda sem ponto");
  expect(sentenceAt("a ".repeat(200), 0, 0, 20)).toHaveLength(20);
});
