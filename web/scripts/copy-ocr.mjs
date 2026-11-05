// Copia worker, motor WASM e idioma do OCR para public/tesseract, para o site não depender de CDN.
// Roda antes de `dev` e `build` (ver package.json).
import { cpSync, mkdirSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const pkg = (name) => dirname(require.resolve(`${name}/package.json`));
const out = join(import.meta.dirname, "..", "public", "tesseract");
mkdirSync(join(out, "lang"), { recursive: true });

cpSync(join(pkg("tesseract.js"), "dist", "worker.min.js"), join(out, "worker.min.js"));
// O worker escolhe a variante (simd, relaxedsimd...) conforme o navegador; só usamos o modo LSTM.
const core = pkg("tesseract.js-core");
for (const f of readdirSync(core).filter((f) => f.endsWith("lstm.wasm.js"))) cpSync(join(core, f), join(out, f));
cpSync(join(pkg("@tesseract.js-data/por"), "4.0.0_best_int", "por.traineddata.gz"), join(out, "lang", "por.traineddata.gz"));

console.log("OCR copiado para public/tesseract");
