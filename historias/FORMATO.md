# Formato de una historia

Cada historia es un JSON en `historias/pendientes/NNN-slug.json`. Se publican por orden de nombre, así que el número manda.

```json
{
 "id": "007-tardigrados",                 // igual que el nombre del archivo, sin .json
 "titulo": "El animal que sobrevive al espacio 🐻🚀",   // máx. 90 caracteres; se añade #shorts solo
 "descripcion": "Dos frases que enganchen.",
 "hashtags": ["#datoscuriosos", "#ciencia", "#shorts"],
 "etiquetas": ["tardígrados", "ciencia"],
 "paleta": "ciencia",                      // historia | animales | oceano | ciencia | espacio | cuerpo | comida | rareza
 "miniatura": {"texto": "SOBREVIVE AL ESPACIO", "emojis": ["🐻", "🚀"]},
 "nota_veracidad": "Qué está comprobado y qué no.",
 "fuentes": ["Autor (año), publicación"],
 "claves": ["palabras", "que", "salen", "en", "verde"],
 "escenas": [ { "texto": "Frase narrada", "tipo": "emoji", "emojis": ["🐻"], "rotulo": "Texto del cartel" } ]
}
```

## Tipos de escena

| tipo | campos | qué se ve |
|---|---|---|
| `emoji` | `emojis` (1-3), `rotulo` | emojis grandes que rebotan |
| `numero` | `valor` ("22.000"), `unidad`, `emojis` (1), `rotulo` | número gigante que cuenta hacia arriba |
| `fecha` | `anio`, `emojis` (1), `rotulo` | año grande con línea de tiempo |
| `versus` | `emojis` (2), `rotulos` (2), `rotulo` | dos cosas enfrentadas con un VS |
| `sello` | `emojis`, `sello` | emojis y un sello rojo encima |
| `duda` | `emojis`, `sello` (por defecto "¿LEYENDA?") | sello naranja: para lo que no está comprobado |
| `lista` | `items`: [["🥶","Frío"], ...] (máx. 3) | filas que aparecen una a una |
| `pregunta` | `emojis` (opcional) | la mascota "?" con emojis girando |
| `final` | — | mascota + "¡SÍGUENOS!" + confeti (siempre la última) |

## Reglas editoriales

- 10-12 escenas, unas 130-160 palabras en total: dura entre 45 y 65 segundos.
- La primera frase es el gancho: lo más sorprendente, sin rodeos.
- Español neutro, frases cortas, números escritos con letra en `texto` (la voz los lee mejor) y con cifras en `valor`/`anio`.
- **Veracidad:** solo hechos con fuente. Si algo es leyenda, discutido o poco comprobable, dilo en la narración ("dicen que", "según algunos relatos") y usa una escena `duda`. Explica el matiz en `nota_veracidad`.
- Nada de temas que ya estén en `historias/pendientes/` ni en esta lista de hechos: Gran Guerra del Emú, Wojtek el oso soldado, Napoleón y los conejos, epidemia de baile de 1518, pulpo de tres corazones, miel que nunca caduca.
- Emojis: solo emojis estándar (Twemoji 15.1); se comprueban al validar.
- La última escena es `final` y termina con "Síguenos para más curiosidades."
