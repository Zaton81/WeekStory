---
applyTo: "templates/**/*.html, static/**/*.js, static/**/*.css"
description: "Reglas de frontend para plantillas Django, parciales HTMX y reproductor Web Speech API"
---

# Directrices de Frontend: HTMX + Web Speech API

## 1. Parciales HTMX (`templates/stories/*_partial.html`)
- Todo template parcial debe tener un contenedor raíz con un `id` único para facilitar `hx-target` y `hx-swap="outerHTML"`.
- Garantiza el envío del token CSRF en peticiones POST de HTMX.

## 2. Síntesis de Voz en Navegador (`static/js/main.js`)
- Usa exclusivamente `window.speechSynthesis` y `SpeechSynthesisUtterance`.
- Verifica soporte con `if ("speechSynthesis" in window)` antes de mostrar controles de audio.
- Divide el texto del relato por párrafos (`<p>`) o frases y encadénalos con `utterance.onend` para evitar el límite de 15 segundos en Chrome de escritorio.
- Dispara `speechSynthesis.speak()` siempre desde un evento `click` directo del usuario para compatibilidad con iOS Safari.
- Ejecuta `window.speechSynthesis.cancel()` en los eventos `beforeunload` y `htmx:beforeRequest`.

