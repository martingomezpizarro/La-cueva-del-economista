# Plan de los agentes-profesores

Todos los agentes se apoyan en **La Cueva-LM** (el RAG sobre el corpus + la bibliografía que
sube el usuario). Cada uno recibe el *contexto del análisis* (variables, frecuencia, modelo,
resultados) + los *pasajes recuperados* y produce una respuesta **fundamentada y citada**.

## Los 4 agentes

### 1. 🧭 Metodólogo (antes del análisis)
Dada la variable, frecuencia y objetivo del usuario, recomienda el método correcto y advierte
qué supuestos verificar.
> *"Tu Y parece I(1) y hay otra serie I(1): considerá cointegración (VECM/ARDL) antes de un VAR en niveles."*

**✅ Implementado (v1):** `python rag/metodologo.py "descripción del análisis"` — recupera
pasajes de La Cueva-LM + las fichas relevantes y produce la recomendación estructurada
(diagnóstico → método → supuestos → errores típicos → plan). Flag `-i` para repreguntar.

### 2. 📖 Intérprete (después del análisis)
Lee la salida (coeficientes, tests) y la traduce a lenguaje económico, citando la bibliografía.
> *"El coeficiente de largo plazo de reservas es negativo y significativo: más reservas → menor riesgo (Enders, cap. 6)."*

### 3. 🔎 Crítico / detector de patrones
Revisa serie + resultados buscando problemas y los señala:
quiebre estructural sin tratar, autocorrelación residual, raíz unitaria ignorada, R² espurio.

### 4. 🗂️ Bibliógrafo del usuario
Ingiere la bibliografía que **el usuario sube** y la suma al contexto de su investigación.

## Cómo funciona por dentro (RAG)
```
input del usuario (qué hace / qué quiere) + contexto del análisis
        │
        ▼
  recuperar pasajes relevantes del corpus  (La Cueva-LM)
        │
        ▼
  Claude redacta la respuesta SOLO con esos pasajes + cita fuente/página
```

## Las "fichas cara-al-agente" (ingrediente secreto)
Además de los libros completos, por cada tema hay una **ficha de 1 página** con: supuestos,
**errores típicos** y cuándo usar / cuándo no. Es lo que permite al agente advertir errores
teóricos de forma confiable. Ver `knowledge-base/fichas/`.

## Modelo de IA
Gemini free tier como backend por defecto (`GEMINI_API_KEY`, gratis), Claude como
alternativa paga, y modo offline sin clave — todo vía el gateway único `cueva/llm/`.
El tier de modelo de cada agente se define en el frontmatter de su skill
(`knowledge-base/skills/*.md`), que desde la fase 2 es la fuente de verdad de cada agente.
