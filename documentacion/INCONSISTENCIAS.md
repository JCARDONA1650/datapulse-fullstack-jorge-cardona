# Inconsistencias y deuda técnica detectadas

Registro de contradicciones o ambigüedades reales encontradas en `HU_GLOBAL.md` / `PROMPT.md` durante el desarrollo, la decisión tomada para seguir avanzando, y la forma óptima de resolverlo si hubiera más tiempo o se pudiera repreguntar al negocio. No incluye los "Puntos ambiguos" de la sección 13 de `HU_GLOBAL.md` (esos ya están resueltos y documentados en el `README.md`) — este archivo es solo para hallazgos que **no estaban señalados como ambiguos** por el propio documento.

---

## 1. Bracket de inflación vs. caso de prueba obligatorio del IRPC (Fase 2/3)

**Dónde:** `HU_GLOBAL.md`, Épica 4 — tabla de Score Económico y "Caso de prueba obligatorio (Colombia)".

**Qué pasa:** la tabla de brackets define Inflación como `>50→-40`, `>10→-25`, `>5→-10`. El caso de prueba usa Inflación=9.2 (cae en el bracket `>5`, penalización -10) pero el documento afirma que la penalización debe ser -25 para que el Score Económico resulte en 45 y el IRPC final en 69 (MODERADO).

**Verificación:** aplicando la fórmula literal, Score Económico = 100 -5 -10 -15 -10 = 60 (no 45), lo que da IRPC = 24+27+24 = 75 → BAJO (no 69/MODERADO).

**Decisión tomada (confirmada por el usuario):** implementar los brackets exactamente como están escritos en la tabla. El test del caso Colombia queda con el resultado real (Score Económico=60, IRPC=75, BAJO) y lo documenta explícitamente como una divergencia conocida respecto al documento original.

**Alternativas consideradas:**
- Ajustar el dato de inflación de Colombia en el seed (9.2 → >10) para forzar 69/MODERADO sin tocar la fórmula.
- Bajar el umbral medio de la fórmula (>10 → >8) para que 9.2 caiga en el bracket alto — afecta a los 10 países, no solo a Colombia.

**Forma óptima de resolverlo:** confirmar con quien escribió la prueba técnica cuál de los dos números (9.2 o -25) es el erróneo. Sin esa confirmación, la fórmula escrita es la fuente más confiable porque es una regla general (afecta a los 10 países), mientras que el caso de prueba es un solo ejemplo numérico.

**Impacto:** si el evaluador espera ver exactamente "69 / MODERADO" al correr el caso de Colombia, este sistema mostrará "75 / BAJO" en su lugar, con la explicación correspondiente en README y en el código.

---

<!-- Agregar nuevos hallazgos abajo, con el mismo formato, a medida que aparezcan en fases posteriores. -->
