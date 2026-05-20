# src/application/dtos/processo_input_dto.py
# DTO de entrada para consulta de processo judicial por número CNJ

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProcessoInputDTO:
    """
    DTO de entrada para a consulta de um processo judicial.

    Attributes:
        numero_cnj: Número do processo no formato CNJ
                    (NNNNNNN-DD.AAAA.J.TT.OOOO)
        tribunal_hint: Sigla do tribunal para direcionar a busca (opcional).
                       Ex: 'STJ', 'STF', 'TJSP'
    """
    numero_cnj: str
    tribunal_hint: str | None = field(default=None)

    def __post_init__(self) -> None:
        import re
        numero_limpo = re.sub(r"[\s\-\.]", "", self.numero_cnj)
        if len(numero_limpo) < 20:
            raise ValueError(
                f"Número CNJ inválido: '{self.numero_cnj}'. "
                "Formato esperado: NNNNNNN-DD.AAAA.J.TT.OOOO"
            )
