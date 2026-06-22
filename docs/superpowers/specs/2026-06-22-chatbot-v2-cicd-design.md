# Spec: Chatbot v2 — Redirect Estratégico + CI/CD

**Fecha:** 2026-06-22  
**Rama:** feat/gabriel/chatbot_v2  
**Repositorio:** Backend (Django) + Frontend (Vue 3)

---

## 1. Objetivo

Extender el chatbot "Cory" para que, cuando encuentre vuelos en vivo (Sabre) o detalle de paquete, retorne al frontend un objeto `accion` con los datos necesarios para redirigir al usuario a la pantalla de resultados con datos pre-cargados — en lugar de solo responder en texto.

La reserva completa sigue ocurriendo en las vistas existentes (`ResultadosVuelos.vue`, `DetallePaquete.vue`). El chat es el punto de entrada, no el punto de cierre.

---

## 2. Arquitectura del Flujo

```
Usuario → ChatBot.vue → POST /api/chatbot
                              │
                    procesar_mensaje()
                              │
                    Groq llama tool?
                    ┌─────────┴──────────┐
                   NO                   SÍ
                    │                    │
              accion=None          ejecutar_tool()
                    │                    │
                    │         tool == buscar_vuelos_live
                    │              o get_detalle_paquete?
                    │           ┌────────┴────────┐
                    │          NO                SÍ
                    │       accion=None    _build_accion()
                    │           │                 │
                    └───────────┴─────────────────┘
                                │
                  { respuesta, historial, accion }
                                │
                         ChatBot.vue recibe
                                │
                    accion presente?
                    ┌─────┴──────┐
                   NO           SÍ
                    │            │
              burbuja texto   burbuja texto
                            + botón accion.label
                                 │ (clic usuario)
                            router.push(path, query)
                                 │
                  ResultadosVuelos.vue | DetallePaquete.vue
                  (ya leen route.query — sin cambios)
```

---

## 3. Schema JSON de Respuesta

### 3.1 Vuelos en vivo (buscar_vuelos_live)

```json
{
  "respuesta": "Encontré 3 vuelos de Quito a Miami para el 15 de julio desde $420...",
  "historial": [...],
  "accion": {
    "tipo": "redirect_vuelos",
    "label": "Ver vuelos disponibles",
    "path": "/vuelos/resultados",
    "params": {
      "origin": "UIO",
      "destination": "MIA",
      "date": "2025-07-15",
      "adults": 1,
      "tipoViaje": "idaVuelta"
    }
  }
}
```

### 3.2 Detalle de paquete (get_detalle_paquete)

```json
{
  "respuesta": "El paquete Europa Clásica dura 10 días desde $1,890...",
  "historial": [...],
  "accion": {
    "tipo": "redirect_paquete",
    "label": "Ver detalles y reservar",
    "path": "/paquetes/42",
    "params": {}
  }
}
```

### 3.3 Sin acción (respuesta informativa)

```json
{
  "respuesta": "CorpoDG opera con Avianca, LATAM y Copa Airlines.",
  "historial": [...],
  "accion": null
}
```

---

## 4. Cambios en Backend

### 4.1 `servicios/chatbot.py`

**Añadir función `_build_accion(tool_name, tool_args)`:**
- Si `tool_name == "buscar_vuelos_live"`: construye accion tipo `redirect_vuelos` con los params de `tool_args`
- Si `tool_name == "get_detalle_paquete"`: construye accion tipo `redirect_paquete` con el ID
- Cualquier otra tool: retorna `None`

**Modificar `ejecutar_tool()`:**
- Retorna `(resultado_json, accion)` en lugar de solo `resultado_json`

**Modificar `procesar_mensaje()`:**
- Acumula la acción si alguna tool call la genera
- Incluye `"accion": accion` en el dict de retorno

### 4.2 `servicios/views.py`

El endpoint ya serializa el dict de `procesar_mensaje()` — solo debe pasar el campo `accion` tal cual (puede ser `null`).

---

## 5. Cambios en Frontend

### 5.1 `src/components/ChatBot.vue`

**Historial local de mensajes:**  
Cada mensaje del asistente almacena `{ role, content, accion }` — el campo `accion` viene de la respuesta API.

**Render del botón:**  
Bajo la burbuja del asistente, si `msg.accion` existe:
```html
<button @click="irAResultados(msg.accion)">
  {{ msg.accion.label }}
</button>
```

**Handler `irAResultados(accion)`:**
```js
import { useRouter } from 'vue-router'
const router = useRouter()

function irAResultados(accion) {
  router.push({ path: accion.path, query: accion.params })
}
```

El chat permanece abierto tras el redirect (comportamiento opción A).

---

## 6. CI/CD — GitHub Actions

### 6.1 Backend Pipeline (`.github/workflows/ci.yml`)

**Trigger:** push o PR a `main`, `develop`, ramas `feat/**`  
**Stack:** Python 3.11, Django, SQLite para tests  
**Pasos:** checkout → install deps → flake8 → django test

### 6.2 Frontend Pipeline (`.github/workflows/ci.yml`)

**Trigger:** push o PR a `main`, `develop`, ramas `feat/**`  
**Stack:** Node 20, Vue 3 + Vite, Playwright  
**Pasos:** checkout → npm ci → build → playwright install → playwright test

**E2E a cubrir (mínimo para requisito Sandoval):**
1. El chatbot abre y cierra correctamente
2. Enviar mensaje retorna respuesta del asistente
3. Cuando hay acción, el botón de redirect aparece
4. El botón navega a la ruta correcta con los query params esperados

**Herramienta elegida: Playwright** — setup inmediato con `npm init playwright@latest`, soporte nativo para Vue 3 + Vite, y mejor integración con componentes flotantes que Cypress.

---

## 7. Archivos a Crear/Modificar

### Backend
- `servicios/chatbot.py` — añadir `_build_accion()`, modificar `ejecutar_tool()` y `procesar_mensaje()`
- `.github/workflows/ci.yml` — nuevo

### Frontend
- `src/components/ChatBot.vue` — añadir accion en historial local + render botón + handler
- `.github/workflows/ci.yml` — nuevo
- `tests/e2e/chatbot.spec.js` — nuevo (Playwright)

---

## 8. Lo que NO cambia

- `ResultadosVuelos.vue` — ya lee `route.query`, sin modificaciones
- `DetallePaquete.vue` — ya recibe `:id` por prop, sin modificaciones
- Lógica de Sabre / `searchFlights.py` — sin modificaciones
- Sistema de reservas con Stripe — fuera de scope
