// Leitura de PDF no navegador. Páginas sem texto (escaneadas) passam por OCR com tesseract.js.
// O arquivo nunca é enviado: só o modelo de OCR em português é baixado, uma vez.

import type { Worker as OcrWorker } from "tesseract.js";

export interface Page {
  number: number;
  text: string;
  ocr: boolean;
}

const MIN_TEXT = 50; // abaixo disso a página provavelmente é imagem
const MAX_PAGES = 200;

export async function readPdf(file: File, onProgress: (msg: string) => void): Promise<Page[]> {
  const pdfjs = await import("pdfjs-dist");
  pdfjs.GlobalWorkerOptions.workerSrc = new URL("pdfjs-dist/build/pdf.worker.min.mjs", import.meta.url).toString();

  const task = pdfjs.getDocument({ data: await file.arrayBuffer() });
  const doc = await task.promise.catch((e: unknown) => {
    throw new Error(
      e instanceof Error && e.name === "PasswordException"
        ? "Este PDF é protegido por senha."
        : "Não foi possível ler este PDF. O arquivo pode estar corrompido.",
    );
  });
  const total = Math.min(doc.numPages, MAX_PAGES);
  const pages: Page[] = [];
  let ocr: OcrWorker | null = null;

  try {
    for (let n = 1; n <= total; n++) {
      onProgress(`Lendo página ${n} de ${total}`);
      const page = await doc.getPage(n);
      const content = await page.getTextContent();
      let text = content.items.map((it) => ("str" in it ? it.str + (it.hasEOL ? "\n" : " ") : "")).join("");

      const isScanned = text.replace(/\s/g, "").length < MIN_TEXT;
      if (isScanned) {
        onProgress(`OCR da página ${n} de ${total} (página escaneada)`);
        if (!ocr) {
          const { createWorker } = await import("tesseract.js");
          ocr = await createWorker("por");
        }
        const viewport = page.getViewport({ scale: 2 });
        const canvas = document.createElement("canvas");
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        await page.render({ canvas, viewport }).promise;
        text = (await ocr.recognize(canvas)).data.text;
      }
      pages.push({ number: n, text, ocr: isScanned });
    }
  } finally {
    await ocr?.terminate();
    await task.destroy();
  }
  return pages;
}
