# 🧮 Calculadora REBT - Documentación del Proyecto

## 📋 Resumen

Aplicación web para cálculos de instalaciones eléctricas según el Reglamento Electrotécnico de Baja Tensión (REBT) español.

## 🎯 Objetivos

- Calcular circuitos eléctricos de viviendas (C1-C13) según ITC-BT-25
- Dimensionar instalaciones de enlace (CGP, LGA, DI)
- Determinar sección de cables por intensidad admisible y caída de tensión
- Seleccionar protecciones (PIA, IGA, fusibles)
- Generar esquemas unifilaressimple as ASCII

---

## 🏗️ Arquitectura

```
REBT_Project/
├── app.py                    # Aplicación Flask principal
├── src/
│   ├── engine_rebt.py       # Motor de cálculo REBT
│   ├── modules/
│   │   ├── uf0884.py      # Instalaciones de enlace
│   │   └── uf0887.py      # Circuitos de vivienda
│   ├── schemes.py         # Generación esquemas unifilaressimple
│   └── ollama_client.py   # Integración Ollama (opcional)
├── templates/
│   └── index.html         # Interfaz web
├── ejercicios/             # PDFs ejercicios prácticos
├── esquemas/              # Esquemas generados
├── normativa/             # PDFs ITC-BT
└── venv/                  # Entorno virtual Python
```

---

## 🔌 Cálculos Implementados

### UF0887 - Instalaciones en Viviendas (ITC-BT-25)

**Circuitos C1-C13:**

| Circuito | Descripción | Potencia | PIA | Sección |
|----------|-------------|---------|-----|---------|
| C1 | Iluminación (≤30 puntos) | 2000W | 10A | 1.5mm² |
| C2 | Tomas uso general (≤20) | 3450W | 16A | 2.5mm² |
| C3 | Cocina y horno | 5400W | 25A | 6mm² |
| C4 | Lavadora/Lavavajillas/Termo | 2500W | 20A | 4mm² |
| C5 | Tomas baños/aux. cocina | 2500W | 20A | 4mm² |
| C6 | Iluminación extra (>30) | 2000W | 10A | 1.5mm² |
| C7 | Tomas adicionales (>20) | 3450W | 16A | 2.5mm² |
| C8 | Calefacción eléctrica | 5750W | 32A | 6mm² |
| C9 | Aire acondicionado | 2500W | 20A | 4mm² |
| C10 | Secadora | 3500W | 20A | 4mm² |
| C11 | Domótica/seguridad | 500W | 10A | 1.5mm² |
| C13 | Recarga VE (ITC-BT-52) | 3680W | 20A | 2.5mm² |

**Electrificación:**
- **Básica**: ≤30 puntos de luz, ≤20 Tomas, sin equipos adicionales
- **Elevada**: Más de 30 puntos, >20 Tomas, cocina, aire acondicionado, etc.

**Fórmulas:**
```
Intensidad (A) = Potencia (W) / (Tensión (V) × fp)

Sección CDT (mm²) = 2 × ρ × P × L / (ΔU% × U × fp)
    ρ = 0.018 Ω·mm²/m (cobre)
    ΔU = 3% (vivienda), 5% (concurrencia)

Sección mínima = max(sección_CDT, sección_IZ_normalizada)
```

### UF0884 - Instalaciones de Enlace

- Previsión de cargas según ITC-BT-10
- Coeficiente de simultaneidad
- Línea General de Alimentación (LGA)
- Derivaciones Individuales (DI)
- Cálculo de tubos

---

## 🖥️ Interfaz Web

### Pestañas disponibles:
1. **Vivienda** → Circuitos C1-C13
2. **Edificio** → CGP, LGA, centralización
3. **Circuito** → Cálculo genérico
4. **DI** → Derivación individual

### Uso:
1. Seleccionar pestaña
2. Rellenar formulario
3. clic en "Calcular"
4. Ver resultados + esquema unifilar

---

## 🚀 Despliegue Local

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar
python app.py

# Abrir navegador
http://localhost:5000
```

---

## 🌐 Despliegue en Vercel

**No funciona con Ollama** (solo local). Para producción necesitarías:
- OpenAI API
- Servidor propio con Ollama

**Pasos:**
```bash
# 1. Subir a GitHub
git init
git add .
git commit -m "Calculadora REBT v1"
git remote add origin https://github.com/tu-usuario/rebt-calculadora.git
git push -u origin main

# 2. Importar en Vercel
# Ir a vercel.com > Import Project > seleccionar repositorio

# 3. Configurar
- Framework: Flask
- Build: pip install -r requirements.txt  
- Output: gunicorn app:app --bind 0.0.0.0:$PORT
```

---

## 🔧 Tecnologías

- **Python 3.12+**
- **Flask** - Web framework
- **Jinja2** - Templates
- **Gunicorn** - Servidor producción
- **Ollama** (opcional) - Chat IA local
- **RAG** - Búsqueda en documentos (pypdf, chromadb)

---

## 📝 Funcionalidades

✅ Cálculo automático de circuitos según ITC-BT-25  
✅ Electrificación básica/elevada automática  
✅ Sección de cables por intensity y caída de tensión  
✅ Selección de protecciones (PIA, IGA, fusibles)  
✅ Dimensionado de tubos (ITC-BT-21)  
✅ Esquema unifilar ASCII  
✅ Cálculo de edificios completos  
✅ API REST `/api/calcular`  
✅ RAG con PDFs de normativa y ejercicios  
✅ Resolución de ejercicios paso a paso  
✅ Búsqueda en documentos

---

## 🔄 Futuras Mejuras

- [ ] Añadir más ITCs (UF0885, UF0888)
- [x] RAG con PDFs de normativa
- [x] Resolución de ejercicios paso a paso
- [ ] Agente IA (con Ollama u OpenAI)
- [ ] Más tipos de instalaciones
- [ ] Exportar a PDF
- [ ] Tests unitarios

---

## 📂 Archivos del Proyecto

| Archivo | Descripción |
|---------|-------------|
| `app.py` | Aplicación Flask |
| `src/engine_rebt.py` | Motor de cálculo principal |
| `src/schemes.py` | Generación esquemas |
| `src/ollama_client.py` | Búsqueda RAG |
| `src/rag_extractor.py` | Extracción de texto de PDFs |
| `src/rag_vectorstore.py` | Embeddings y ChromaDB |
| `src/resolutor.py` | Resolución de ejercicios |
| `src/index_rag.py` | Script de indexación |
| `templates/index.html` | Interfaz web |
| `requirements.txt` | Dependencias Python |
| `README.md` | Descripción básica |
| `LICENSE` | Licencia MIT |

---

## 💾 Bad kups

El código fuente está en:
`/home/oscar2/Documentos/REBT_Project/`

**Autores:** -
**Fecha:** Abril 2026
**Licencia:** MIT