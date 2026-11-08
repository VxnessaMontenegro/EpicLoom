# NORMAS DE REQUERIMIENTOS (EDÍTAME CON LAS TUYAS)

## Idioma y estilo
- Todo en español, redacción clara, sin jerga innecesaria.
- Títulos cortos (máximo 80 caracteres), empezando con sustantivo o verbo de acción.

## Épica
- Representa un objetivo de negocio grande.
- Incluye descripción y valor de negocio esperado.

## Feature
- Capacidad funcional que entrega valor completo y agrupa varias historias de usuario.
- Debe poder explicarse en una frase.

## Historia de usuario
- Formato obligatorio: "Como <rol>, quiero <acción>, para <beneficio>".
- Debe cumplir INVEST: Independiente, Negociable, Valiosa, Estimable, Pequeña, Testeable.
- Cada historia debe poder completarse en un sprint.
- Mínimo 2 y máximo 6 criterios de aceptación.
- Criterios en formato Gherkin: Dado / Cuando / Entonces.
- Incluir al menos un criterio para un caso de error o excepción.
- No mezclar detalles técnicos de implementación en la historia.
- Sugerir puntos de historia con la escala Fibonacci (1, 2, 3, 5, 8).

## Task
- Trabajo técnico concreto, que una persona termina en 1 día o menos.
- Título empieza con verbo en infinitivo (ej: "Crear endpoint de login").
- Cada historia debe tener al menos 2 tasks (desarrollo y pruebas).

## Definición de listo (DoR)
- Rol, acción y beneficio definidos.
- Criterios de aceptación revisables y sin ambigüedad.
- Dependencias mencionadas en la descripción si existen.

## Reglas extra tuyas (agrega aquí)
- (ejemplo) Prefijo del módulo en el título: [PAGOS], [USUARIOS]...
- (ejemplo) Siempre incluir criterio de seguridad si hay datos personales.
