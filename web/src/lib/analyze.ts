import { Classifier, type Model, type Prediction } from "./classifier";
import { anonymize, exposureScore, extractEntities, type Entity } from "./ner";
import type { Page } from "./pdf";
import { summarize } from "./summarizer";

export interface Segment {
  label: string;
  from: number;
  to: number;
}

export interface Analysis {
  ranking: Prediction[]; // tipo predominante no documento todo
  segments: Segment[]; // páginas consecutivas com o mesmo tipo
  entities: Entity[];
  exposure: ReturnType<typeof exposureScore>;
  summary: string[];
  anonymized: string;
  text: string;
  ocrPages: number;
  ms: number;
}

let classifier: Promise<Classifier> | null = null;

export function loadClassifier(): Promise<Classifier> {
  classifier ??= fetch("/model.json")
    .then((r) => {
      if (!r.ok) throw new Error(`Falha ao carregar o modelo (${r.status})`);
      return r.json() as Promise<Model>;
    })
    .then((m) => new Classifier(m))
    .catch((e) => {
      classifier = null; // permite tentar de novo
      throw e;
    });
  return classifier;
}

export function analyze(clf: Classifier, pages: Page[]): Analysis {
  const t0 = performance.now();
  const perPage = pages.map((p) => clf.uniformPrior(clf.probabilities(p.text)));

  // O modelo foi treinado por página (como no VICTOR); o documento é a média das páginas.
  const mean = clf.model.classes.map((_, c) => perPage.reduce((s, p) => s + p[c], 0) / perPage.length);
  const ranking = mean
    .map((probability, c) => ({ label: clf.model.labels[c], probability }))
    .sort((a, b) => b.probability - a.probability);

  const segments: Segment[] = [];
  perPage.forEach((p, i) => {
    const label = clf.model.labels[p.indexOf(Math.max(...p))];
    const last = segments.at(-1);
    if (last?.label === label) last.to = pages[i].number;
    else segments.push({ label, from: pages[i].number, to: pages[i].number });
  });

  const text = pages.map((p) => p.text).join("\n\n");
  const entities = extractEntities(text);
  return {
    ranking,
    segments,
    entities,
    exposure: exposureScore(entities),
    summary: summarize(text, 5),
    anonymized: anonymize(text, entities),
    text,
    ocrPages: pages.filter((p) => p.ocr).length,
    ms: performance.now() - t0,
  };
}
