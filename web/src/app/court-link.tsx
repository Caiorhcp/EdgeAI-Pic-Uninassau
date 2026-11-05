"use client";

import { ExternalLink, Upload } from "lucide-react";
import { useState } from "react";
import { portalFor } from "@/lib/courts";

/** Leva até a área de envio de PDFs (id="enviar" no analisador) e abre a escolha de arquivos. */
export function goToUpload() {
  const area = document.getElementById("enviar");
  area?.scrollIntoView({ behavior: "smooth", block: "center" });
  area?.querySelector<HTMLInputElement>("input[type=file]")?.click();
}

/**
 * Abre a consulta pública do tribunal com o número já copiado, e explica como trazer os autos.
 * O download em si fica com o usuário: os tribunais exigem login/certificado ou CAPTCHA, que não automatizamos.
 */
export function CourtLink({ numero, compact }: { numero: string; compact?: boolean }) {
  const [opened, setOpened] = useState(false);
  const portal = portalFor(numero);
  if (!portal) return null;

  async function open() {
    try {
      await navigator.clipboard.writeText(numero);
    } catch {
      // sem permissão de área de transferência: o número continua visível na tela
    }
    window.open(portal!.url, "_blank", "noopener,noreferrer");
    setOpened(true);
  }

  return (
    <div className={compact ? "inline" : "space-y-2"}>
      <button type="button" onClick={open}
        className={compact
          ? "inline-flex items-center gap-1 text-xs text-accent underline-offset-2 hover:underline"
          : "inline-flex items-center gap-2 rounded-lg border border-line px-3 py-1.5 text-sm font-medium hover:bg-surface"}>
        <ExternalLink className={compact ? "size-3" : "size-4"} aria-hidden /> Abrir autos no {portal.court}
        {!compact && <span className="text-muted">({portal.system})</span>}
      </button>
      {opened && (
        <div className="rounded-lg bg-surface p-3 text-sm" role="status">
          <p>
            {portal.prefilled ? "A consulta abriu já com o processo pesquisado." : `Número ${numero} copiado: cole na busca do ${portal.court}.`}{" "}
            Abra o processo e use a opção de baixar os autos em PDF. Em geral o download completo exige login de
            advogado, gov.br da parte ou a senha do processo.
          </p>
          <button type="button" onClick={goToUpload}
            className="mt-2 inline-flex items-center gap-2 rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-on-accent">
            <Upload className="size-4" aria-hidden /> Já baixei: adicionar os autos
          </button>
        </div>
      )}
    </div>
  );
}
