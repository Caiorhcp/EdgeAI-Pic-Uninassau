"use client";

import { Moon, Sun } from "lucide-react";

/** Alterna claro/escuro. O ícone muda por CSS (variante dark:), então não há estado nem diferença na hidratação. */
export function ThemeToggle() {
  function toggle() {
    const root = document.documentElement;
    const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try {
      localStorage.setItem("theme", next);
    } catch {
      // modo privado sem armazenamento: o tema vale só nesta visita
    }
  }

  return (
    <button type="button" onClick={toggle} aria-label="Alternar entre tema claro e escuro" title="Tema claro / escuro"
      className="inline-flex size-9 items-center justify-center rounded-full border border-line text-muted hover:bg-surface hover:text-foreground">
      <Moon className="size-4 dark:hidden" aria-hidden />
      <Sun className="hidden size-4 dark:block" aria-hidden />
    </button>
  );
}
