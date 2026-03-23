# src/application/dtos/documento_input_dto.py
# DTO de entrada para o caso de uso de análise de documento

from pydantic import BaseModel, Field
from typing import Optional

class DocumentoInputDTO(BaseModel):
    """
    Data Transfer Object de entrada — dados do documento a ser analisado.
    Validação estrita com Pydantic.
    """
    texto: str = Field(..., min_length=10, description="Texto extraído do documento")
    nome: str = Field("Documento", description="Nome do arquivo ou identificador")
    tipo_extracao: Optional[str] = Field(None, description="Como foi obtido ('digital', 'escaneado', 'digitado')")
    n_frases_resumo: int = Field(4, ge=1, le=20, description="Quantas frases no resumo automático")
