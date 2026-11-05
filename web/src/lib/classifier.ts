// Inferência do classificador de tipo de documento, 100% no navegador.
// Espelha ml/train.py (normalize + predict_from_json); a paridade é testada em classifier.test.ts.

export interface Model {
  version: number;
  stopwords: string[];
  classes: string[];
  labels: string[];
  terms: string[];
  idf: number[];
  coef: number[][];
  intercept: number[];
  prior: number[]; // frequência de cada classe no treino
}

export interface Prediction {
  label: string;
  probability: number;
}

const TOKEN_RE = /[a-zà-öø-ÿ]+/g;
const EMAIL_RE = /\S+@\S+/g;
const URL_RE = /(https?:\/\/|www\.)\S+/g;

export class Classifier {
  private readonly index: Map<string, number>;
  private readonly stopwords: Set<string>;

  constructor(readonly model: Model) {
    this.index = new Map(model.terms.map((t, i) => [t, i]));
    this.stopwords = new Set(model.stopwords);
  }

  normalize(text: string): string[] {
    const t = text.toLowerCase().normalize("NFC").replace(EMAIL_RE, " email ").replace(URL_RE, " site ");
    return (t.match(TOKEN_RE) ?? []).filter((w) => w.length > 1 && !this.stopwords.has(w));
  }

  /** Probabilidade de cada classe, na ordem de model.classes. */
  probabilities(text: string): number[] {
    const tokens = this.normalize(text);
    const counts = new Map<number, number>();
    const add = (gram: string) => {
      const i = this.index.get(gram);
      if (i !== undefined) counts.set(i, (counts.get(i) ?? 0) + 1);
    };
    tokens.forEach(add);
    for (let k = 0; k + 1 < tokens.length; k++) add(`${tokens[k]} ${tokens[k + 1]}`);

    // TF-IDF sublinear + normalização L2, igual ao TfidfVectorizer(sublinear_tf=True)
    const x: [number, number][] = [];
    let norm = 0;
    for (const [i, c] of counts) {
      const v = (1 + Math.log(c)) * this.model.idf[i];
      x.push([i, v]);
      norm += v * v;
    }
    norm = Math.sqrt(norm) || 1;

    const logits = [...this.model.intercept];
    for (const [i, v] of x) {
      const w = this.model.coef[i];
      for (let c = 0; c < logits.length; c++) logits[c] += w[c] * (v / norm);
    }
    const max = Math.max(...logits);
    const exp = logits.map((l) => Math.exp(l - max));
    const sum = exp.reduce((a, b) => a + b, 0);
    return exp.map((e) => e / sum);
  }

  /**
   * Probabilidades supondo classes igualmente frequentes. O treino tem 90% de páginas "outros"
   * (processos inteiros); quem usa o site envia uma peça por vez. Ver test_uniform_prior em ml/metrics.json.
   */
  uniformPrior(probs: number[]): number[] {
    const p = probs.map((x, c) => x / this.model.prior[c]);
    const sum = p.reduce((a, b) => a + b, 0);
    return p.map((x) => x / sum);
  }

  /** Classes ordenadas da mais para a menos provável, com prior uniforme. */
  predict(text: string): Prediction[] {
    return this.uniformPrior(this.probabilities(text))
      .map((probability, c) => ({ label: this.model.labels[c], probability }))
      .sort((a, b) => b.probability - a.probability);
  }
}
