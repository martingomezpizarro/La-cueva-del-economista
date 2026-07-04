"""presupuesto — contabilidad de llamadas y tokens por sesión.

Un `ContadorTokens` viaja con cada sesión de la mesa: el gateway registra en él
cada llamada. Si se fija `limite_llamadas`, el gateway deja de llamar al modelo
cuando se agota (los agentes restantes responden en modo offline y lo dicen:
degradación elegante, no silencio).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ContadorTokens:
    limite_llamadas: int | None = None
    llamadas: int = 0
    tokens_entrada: int = 0
    tokens_salida: int = 0
    errores: int = 0
    por_backend: dict[str, int] = field(default_factory=dict)

    def agotado(self) -> bool:
        return self.limite_llamadas is not None and self.llamadas >= self.limite_llamadas

    def registrar(
        self, backend: str, tokens_entrada: int, tokens_salida: int, *, error: bool = False
    ) -> None:
        self.llamadas += 1
        self.tokens_entrada += tokens_entrada
        self.tokens_salida += tokens_salida
        if error:
            self.errores += 1
        self.por_backend[backend] = self.por_backend.get(backend, 0) + 1

    def to_dict(self) -> dict:
        return {
            "llamadas": self.llamadas,
            "tokens_entrada": self.tokens_entrada,
            "tokens_salida": self.tokens_salida,
            "errores": self.errores,
            "por_backend": dict(self.por_backend),
            "limite_llamadas": self.limite_llamadas,
        }
