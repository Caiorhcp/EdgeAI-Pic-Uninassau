// Consulta de metadados de processo no Datajud. Fica no servidor para guardar a chave
// e porque a API do CNJ não aceita chamadas diretas do navegador.
// POST (e não GET) para o número do processo não aparecer em URL nem em log de acesso.

import { datajudAlias, parseCnj } from "@/lib/cnj";
import { DatajudError, fetchProcess } from "@/lib/datajud";

export const maxDuration = 60; // o Datajud pode levar ~50 s (ver lib/datajud.ts)

export async function POST(request: Request) {
  const body = (await request.json().catch(() => null)) as { numero?: unknown } | null;
  const cnj = typeof body?.numero === "string" ? parseCnj(body.numero) : null;
  if (!cnj) {
    return Response.json(
      { error: "Número inválido. Use o formato CNJ (NNNNNNN-DD.AAAA.J.TR.OOOO) com dígito verificador correto." },
      { status: 400 },
    );
  }

  const alias = datajudAlias(cnj);
  if (!alias) {
    return Response.json(
      { error: "Este tribunal (STF ou CNJ) não está disponível na API pública do Datajud." },
      { status: 422 },
    );
  }

  try {
    const instances = await fetchProcess(cnj, alias);
    if (instances.length === 0) {
      return Response.json(
        { error: "Processo não encontrado no Datajud. Ele pode estar em segredo de justiça ou ainda não ter sido indexado." },
        { status: 404 },
      );
    }
    return Response.json({ numero: cnj.formatted, instances });
  } catch (e) {
    if (e instanceof DatajudError) return Response.json({ error: e.message }, { status: e.status });
    throw e;
  }
}
