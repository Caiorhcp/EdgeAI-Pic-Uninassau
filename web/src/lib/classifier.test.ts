import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { Classifier, type Model } from "./classifier";

const model = JSON.parse(readFileSync(join(__dirname, "../../public/model.json"), "utf-8")) as Model;
// Gerado por ml/test_export.py a partir da implementação Python
const cases = JSON.parse(readFileSync(join(__dirname, "__fixtures__/parity.json"), "utf-8")) as {
  text: string;
  probs: number[];
}[];

describe("Classifier", () => {
  const clf = new Classifier(model);

  it("normaliza igual ao Python", () => {
    expect(clf.normalize("Tribunal de Justiça do Rio")).toEqual(["tribunal", "justiça", "rio"]);
    expect(clf.normalize("contato: joao@ex.com, www.stf.jus.br")).toEqual(["contato", "email", "site"]);
    expect(clf.normalize("Lei 11.419/2006, Art. 5º")).toEqual(["lei", "art"]);
  });

  it.each(cases.map((c, i) => [i, c] as const))("bate com a inferência Python (caso %i)", (_, c) => {
    const got = clf.probabilities(c.text);
    got.forEach((p, k) => expect(p).toBeCloseTo(c.probs[k], 4));
  });
});
