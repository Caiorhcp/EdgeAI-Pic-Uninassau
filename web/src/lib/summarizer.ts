// Resumo extrativo: escolhe as frases mais centrais (similaridade TF-IDF média com as demais)
// com bônus para termos que costumam marcar decisão e pedido. Portado de sumarizador.py.

const STOPWORDS = new Set(
  ("de a o que e do da em um para com uma os no se na por mais as dos como mas ao ele das à seu sua ou " +
    "quando muito nos já eu também só pelo pela até isso ela entre depois sem mesmo aos seus quem nas me " +
    "esse eles essa num nem suas meu às minha numa pelos elas havia seja qual será nós lhe deles essas " +
    "esses pelas este dele não foi ser são está tem").split(" "),
);

const KEY_TERMS = [
  "decide", "decidiu", "acórdão", "sentença", "unanimidade", "provido", "provimento", "negado", "improvido",
  "procedente", "improcedente", "requer", "pedido", "condeno", "julgo", "indenização", "danos", "recurso",
];

// Abreviações que terminam em ponto mas não encerram a frase ("art. 5º", "nº 123", "Exmo. Sr.")
const ABBREV = /\b(?:art|arts|inc|incs|al|fl|fls|n|nº|p|pp|ex|exmo|exma|sr|sra|dr|dra|min|des|rel|proc|cf|c\/c)\.$/i;
const MAX_SENTENCE = 400; // blocos maiores costumam ser cabeçalho ou qualificação das partes

export function splitSentences(text: string): string[] {
  const parts = text.replace(/\s+/g, " ").split(/(?<=[.!?;])\s+(?=[A-ZÀ-Ú0-9"“(])/);
  const sentences: string[] = [];
  for (const part of parts) {
    const prev = sentences.at(-1);
    if (prev !== undefined && ABBREV.test(prev)) sentences[sentences.length - 1] = `${prev} ${part}`;
    else sentences.push(part);
  }
  return sentences
    .map((s) => s.trim())
    .filter((s) => s.length >= 30 && s.length <= MAX_SENTENCE && s.replace(/[^a-zA-ZÀ-ú]/g, "").length >= 15)
    .filter((s) => !isHeading(s) && !isBoilerplate(s));
}

/** Cabeçalho com rótulos ("Autor: … Ré: …", "Processo nº …") e fecho "Cidade, 10 de maio de 2024." não resumem nada. */
function isBoilerplate(s: string): boolean {
  if (/^[^,]{2,40},\s*\d{1,2}\s+de\s+[a-zç]+\s+de\s+\d{4}\.?$/i.test(s)) return true;
  if (/^(?:autos|processo)\s+n[º°.]/i.test(s)) return true;
  return /^[\p{Lu}][\p{Ll}]+\s*:/u.test(s); // começa com rótulo ("Apelado:", "Autor:")
}

/** Títulos de seção ("DOS FATOS", "RAZÕES DO RECURSO") vêm quase todo em maiúsculas. */
function isHeading(s: string): boolean {
  const letters = s.replace(/[^a-zA-ZÀ-ú]/g, "");
  return letters.replace(/[^A-ZÀ-Þ]/g, "").length / letters.length > 0.7;
}

const words = (s: string) => (s.toLowerCase().match(/[a-zà-ú]+/g) ?? []).filter((w) => w.length > 2 && !STOPWORDS.has(w));

export function summarize(text: string, n = 5): string[] {
  const sentences = splitSentences(text);
  if (sentences.length <= n) return sentences;

  const docs = sentences.map(words);
  const df = new Map<string, number>();
  docs.forEach((d) => new Set(d).forEach((w) => df.set(w, (df.get(w) ?? 0) + 1)));

  const vectors = docs.map((d) => {
    const tf = new Map<string, number>();
    d.forEach((w) => tf.set(w, (tf.get(w) ?? 0) + 1));
    const v = new Map<string, number>();
    let norm = 0;
    for (const [w, c] of tf) {
      const x = c * (Math.log((1 + docs.length) / (1 + df.get(w)!)) + 1);
      v.set(w, x);
      norm += x * x;
    }
    norm = Math.sqrt(norm) || 1;
    for (const [w, x] of v) v.set(w, x / norm);
    return v;
  });

  const cosine = (a: Map<string, number>, b: Map<string, number>) => {
    let s = 0;
    for (const [w, x] of a) s += x * (b.get(w) ?? 0);
    return s;
  };

  const scores = vectors.map((v, i) => {
    const centrality = vectors.reduce((s, u) => s + cosine(v, u), 0) / vectors.length;
    const lower = sentences[i].toLowerCase();
    const bonus = Math.min(0.6, KEY_TERMS.filter((t) => lower.includes(t)).length * 0.15);
    return centrality + bonus;
  });

  return scores
    .map((s, i) => [s, i] as const)
    .sort((a, b) => b[0] - a[0])
    .slice(0, n)
    .map(([, i]) => i)
    .sort((a, b) => a - b) // mantém a ordem original do texto
    .map((i) => sentences[i]);
}
