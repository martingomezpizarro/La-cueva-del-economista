---
metodo: Diagnóstico y errores típicos (control de calidad / referee)
tema: 06_quiebres_nolineal
fuentes: ["Enders (2014)", "Maddala-Kim (1998)", "Bai-Perron (1998, 2003)", "Granger-Newbold (1974)"]
---

# Diagnóstico y errores típicos (el referee)

## ¿Qué es / para qué sirve?
La checklist del control de calidad: lo que un referee mira antes de creerle a un resultado. No
estima nada nuevo; **audita** lo que hicieron los demás especialistas.

## La batería de chequeos
- **Regresión espuria:** ¿hay R² alto + Durbin-Watson bajo con series I(1) no cointegradas?
- **Residuos:** autocorrelación (Ljung-Box, Breusch-Godfrey), heterocedasticidad (ARCH-LM, White), normalidad (Jarque-Bera).
- **Estabilidad:** quiebres estructurales (CUSUM, Bai-Perron, Chow); ¿los coeficientes son estables?
- **Especificación:** forma funcional (RESET de Ramsey), variables omitidas, endogeneidad.
- **Raíz unitaria ignorada:** ¿se testeó integración antes de modelar en niveles?
- **Robustez:** ¿el resultado sobrevive a cambiar muestra/controles? (deriva a la ficha de robustez).

## Cuándo interviene
- Después de cada estimación, y antes de fijar cualquier hallazgo o conclusión.

## ⚠️ Errores típicos que debe cazar
- **R² espurio** entre series con tendencia común (Granger-Newbold).
- **Autocorrelación residual** no tratada → errores estándar inválidos (usar HAC/Newey-West).
- **Quiebre estructural** sin tratar → parámetros inestables, conclusiones frágiles.
- **Sobreajuste:** demasiados parámetros para los datos.
- **p-hacking:** elegir la especificación que da el resultado deseado.
- Interpretar **Granger como causalidad** estructural.
- Sacar conclusiones causales de evidencia solo correlacional.

## Cómo se interpreta el resultado
El veredicto del referee es un **semáforo**: verde (sólido), amarillo (sirve con reservas
explícitas), rojo (no creer hasta corregir). Cada bandera roja debe venir con **qué test la
detectó** y **cómo mitigarla** (diferenciar, HAC, agregar dummy de quiebre, cambiar método).
