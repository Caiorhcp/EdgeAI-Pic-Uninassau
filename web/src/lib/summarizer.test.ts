import { describe, expect, it } from "vitest";
import { splitSentences, summarize } from "./summarizer";

const text = [
  "Trata-se de recurso extraordinário interposto contra acórdão da Turma Recursal.",
  "O recorrente alega violação ao artigo 5º da Constituição Federal.",
  "A sessão foi realizada no auditório principal do fórum da comarca.",
  "O café foi servido às partes antes do início da audiência designada.",
  "Ante o exposto, nego provimento ao recurso extraordinário, por unanimidade.",
  "Custas na forma da lei, intimem-se as partes e cumpra-se a decisão.",
  "O relator destacou precedentes do Supremo Tribunal Federal sobre o tema.",
].join(" ");

describe("summarize", () => {
  it("divide em frases e descarta trechos curtos", () => {
    expect(splitSentences("Ok. Esta é uma frase longa o suficiente para entrar no resumo.")).toHaveLength(1);
  });

  it("não quebra em abreviações jurídicas", () => {
    expect(splitSentences("Com fundamento no art. 102, inciso III, da Constituição Federal. Requer o provimento do recurso interposto.")).toEqual([
      "Com fundamento no art. 102, inciso III, da Constituição Federal.",
      "Requer o provimento do recurso interposto.",
    ]);
  });

  it("devolve n frases na ordem original e prioriza o dispositivo", () => {
    const out = summarize(text, 3);
    expect(out).toHaveLength(3);
    expect(out.some((s) => s.includes("nego provimento"))).toBe(true);
    const positions = out.map((s) => text.indexOf(s));
    expect([...positions].sort((a, b) => a - b)).toEqual(positions);
  });

  it("texto curto volta inteiro", () => {
    expect(summarize("Uma única frase com tamanho suficiente para o resumo.", 5)).toHaveLength(1);
  });
});
