// Registra o service worker (public/sw.js) e baixa em segundo plano tudo que a análise usa,
// para o site abrir e funcionar sem internet a partir da segunda visita.

import { relaxedSimd, simd } from "wasm-feature-detect";
import { loadClassifier } from "./analyze";

/** Mesma escolha de variante que o tesseract.js faz (getCore.js), para baixar só o motor que será usado. */
async function ocrCoreVariant(): Promise<string> {
  return (await relaxedSimd()) ? "relaxedsimd-" : (await simd()) ? "simd-" : "";
}

export async function prepareOffline(): Promise<boolean> {
  if (!("serviceWorker" in navigator)) return false;
  await navigator.serviceWorker.register("/sw.js");
  await navigator.serviceWorker.ready;
  // Na primeira visita o worker só assume a página depois do clients.claim(); antes disso os fetch não passam por ele
  if (!navigator.serviceWorker.controller) {
    await new Promise((r) => navigator.serviceWorker.addEventListener("controllerchange", r, { once: true }));
  }

  // Scripts e estilos que a página carregou antes de o worker existir
  const loaded = performance
    .getEntriesByType("resource")
    .map((e) => e.name)
    .filter((u) => u.startsWith(`${location.origin}/_next/`));

  // Import dinâmico (e não estático) para baixar o mesmo chunk que o analisador carrega ao receber um PDF
  const { OCR_PATHS, pdfWorkerUrl } = await import("./pdf");

  // As requisições passam pelo service worker, que guarda cada resposta
  await Promise.all([
    fetch("/"),
    ...loaded.map((u) => fetch(u)),
    loadClassifier(),
    import("pdfjs-dist").then(() => fetch(pdfWorkerUrl())),
    import("tesseract.js"),
    fetch(OCR_PATHS.workerPath),
    fetch(`${OCR_PATHS.langPath}/por.traineddata.gz`),
    ocrCoreVariant().then((v) => fetch(`${OCR_PATHS.corePath}/tesseract-core-${v}lstm.wasm.js`)),
  ]);
  return true;
}
