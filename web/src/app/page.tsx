import { Cpu, Lock, Scale } from "lucide-react";
import { Analyzer } from "./analyzer";
import { OfflineStatus } from "./offline-status";

// Números de ml/metrics.json (teste do VICTOR Small, 95.526 páginas) e da Tabela 2 de Luz de Araujo et al. (LREC 2020)
const BENCHMARK = [
  { model: "Este projeto · TF-IDF + regressão logística", macro: 78.2, weighted: 94.7, highlight: true },
  { model: "SVM linear (artigo original)", macro: 76.3, weighted: 94.3 },
  { model: "CNN (artigo original)", macro: 75.8, weighted: 94.7 },
];

const REPO = "https://github.com/Caiorhcp/sapo-juridico";

export default function Home() {
  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-10 sm:px-6 sm:py-16">
      <header className="mb-10 max-w-3xl">
        <div className="mb-3 flex flex-wrap gap-2">
          <p className="inline-flex items-center gap-2 rounded-full border border-line px-3 py-1 text-xs text-muted">
            <Lock className="size-3.5" aria-hidden /> Processado no seu navegador · nenhum arquivo é enviado
          </p>
          <OfflineStatus />
        </div>
        <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">S.A.P.O.</h1>
        <p className="mt-1 text-sm font-medium uppercase tracking-wide text-accent">Sistema de Análise de Peças Offline</p>
        <p className="mt-3 text-lg text-muted">
          Classifica peças processuais, encontra dados pessoais e resume documentos jurídicos, com um modelo
          treinado em documentos reais do STF que roda inteiro no seu dispositivo.
        </p>
      </header>

      <Analyzer />

      <section className="mt-20 grid gap-10 border-t border-line pt-12 lg:grid-cols-[1fr_1.2fr]" aria-labelledby="como">
        <div>
          <h2 id="como" className="text-xl font-semibold">Como funciona</h2>
          <ul className="mt-5 space-y-5 text-sm leading-relaxed">
            <li className="flex gap-3">
              <Cpu className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
              <span>
                <strong>Classificação no navegador.</strong> Um modelo TF-IDF (uni e bigramas) com regressão logística,
                exportado para JSON (1,4 MB comprimido). A inferência é feita em TypeScript, sem servidor e sem biblioteca de ML.
              </span>
            </li>
            <li className="flex gap-3">
              <Scale className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
              <span>
                <strong>Dados reais.</strong> Treinado no VICTOR, conjunto de páginas de recursos extraordinários do STF
                rotuladas por especialistas do tribunal (UnB/STF, LREC 2020).
              </span>
            </li>
            <li className="flex gap-3">
              <Lock className="mt-0.5 size-5 shrink-0 text-accent" aria-hidden />
              <span>
                <strong>Privacidade por construção.</strong> PDF, OCR (tesseract.js), extração de entidades e anonimização
                acontecem localmente. CPF e CNPJ são validados pelos dígitos verificadores.
              </span>
            </li>
          </ul>
        </div>

        <div>
          <h2 className="text-xl font-semibold">Resultado no conjunto de teste</h2>
          <p className="mt-2 text-sm text-muted">F1 por página em 95.526 páginas, mesma divisão do artigo original.</p>
          <div className="mt-5 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left text-muted">
                  <th className="py-2 pr-4 font-medium">Modelo</th>
                  <th className="py-2 pr-4 text-right font-medium">F1 macro</th>
                  <th className="py-2 text-right font-medium">F1 ponderado</th>
                </tr>
              </thead>
              <tbody>
                {BENCHMARK.map((b) => (
                  <tr key={b.model} className={`border-b border-line ${b.highlight ? "font-semibold" : ""}`}>
                    <td className="py-2 pr-4">{b.model}</td>
                    <td className="py-2 pr-4 text-right tabular-nums">{b.macro.toFixed(1)}</td>
                    <td className="py-2 text-right tabular-nums">{b.weighted.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-4 text-sm leading-relaxed">
            No teste, 89% das páginas são &ldquo;Outros&rdquo; (certidões, procurações). Aqui no site, que recebe uma peça
            por vez, as classes são tratadas como igualmente prováveis: o recall médio por classe sobe de{" "}
            <strong>74%</strong> para <strong>87%</strong>, ao custo de mais falsos positivos em processos inteiros.
          </p>
          <p className="mt-3 text-xs leading-relaxed text-muted">
            Limitação conhecida: &ldquo;Agravo em RE&rdquo; é o tipo mais difícil (F1 de 57), confundido com petição de RE,
            o mesmo padrão do artigo. A análise de dados pessoais é por regras e não substitui avaliação jurídica.
          </p>
        </div>
      </section>

      <footer className="mt-16 flex flex-wrap justify-between gap-2 border-t border-line pt-6 text-xs text-muted">
        <span>Projeto de Iniciação Científica · UNINASSAU · Caio R.</span>
        <a href={REPO} className="underline-offset-4 hover:underline">Código no GitHub</a>
      </footer>
    </main>
  );
}
