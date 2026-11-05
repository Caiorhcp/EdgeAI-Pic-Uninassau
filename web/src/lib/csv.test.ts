import { expect, it } from "vitest";
import { toCsv } from "./csv";

it("separa por ponto e vírgula e escapa aspas, quebras e o próprio separador", () => {
  expect(toCsv(["a", "b"], [["x;y", 'diz "oi"'], ["linha\nnova", 3]])).toBe(
    '﻿a;b\r\n"x;y";"diz ""oi"""\r\n"linha\nnova";3',
  );
});
