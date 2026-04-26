# 🧮 Calculadora REBT - Documentación del Proyecto

## 📋 Resumen

Aplicación web para cálculos de instalaciones eléctricas según el Reglamento Electrotécnico de Baja Tensión (REBT) español.

## 🎯 Objetivos

- Calcular circuitos eléctricos de viviendas (C1-C13) según ITC-BT-25
- Dimensionar instalaciones de enlace (CGP, LGA, DI)
- Determinar sección de cables por intensidad admisible y caída de tensión
- Seleccionar protecciones (PIA, IGA, fusibles)
- Generar esquemas unifilares en SVG
- Resolución de ejercicios con IA
- Búsqueda en normativa REBT

---

## 🏗️ Arquitectura

```
REBT_Project/
├── app.py                    # Aplicación Flask principal
├── src/
│   ├── engine_rebt.py       # Motor de cálculo REBT
│   ├── schemes.py           # Generación esquemas SVG
│   ├── pdf_extractor.py      # Extracción de texto de PDFs
│   ├── rag_vectorstore.py   # ChromaDB para RAG
│   └── resolutor.py         # Resolución ejercicios IA
├── templates/
│   ├── index.html           # Menú principal
│   ├── index_vivienda.html # Circuitos vivienda
│   ├── index_edificio.html # Instalaciones edificio
│   ├── index_circuito.html  # Cálculo circuito
│   ├── index_di.html      # Derivación individual
│   ├── index_ejercicios.html # Resolución ejercicios
│   ├── index_proyecto.html  # Generador proyectos
│   └── index_buscar.html   # Buscar normativa
├── vercel.json             # Config Vercel
└── requirements.txt       # Dependencias
```

---

## 🔌 Cálculos Implementados

### UF0887 - Viviendas (ITC-BT-25)

**Circuitos C1-C13:**

| Circuito | Descripción | Potencia | PIA | Sección |
|----------|-------------|---------|-----|---------|
| C1 | Iluminación (≤30 puntos) | 2000W | 10A | 1.5mm² |
| C2 | Tomas uso general (≤20) | 3450W | 16A | 2.5mm² |
| C3 | Cocina y horno | 5400W | 25A | 6mm² |
| C4 | Lavadora/Lavavajillas/Termo | 2500W | 20A | 4mm² |
| C5 | Tomas baños/aux. cocina | 2500W | 20A | 4mm² |

**Electrificación:**
- **Básica**: ≤30 puntos de luz, ≤20 Tomas
- **Elevada**: Más de 30 puntos, >20 Tomas, cocina, etc.

### UF0884 - Instalaciones de Enlace (ITC-BT-10)

- Coeficiente de simultaneidad
- Línea General de Alimentación (LGA)
- Derivaciones Individuales (DI)
- Cálculo de tubos

### Formulas

```
Intensidad (A) = Potencia (W) / (Tensión (V) × fp)

Sección CDT (mm²) = 2 × ρ × P × L / (ΔU% × U × fp)
    ρ = 0.018 Ω·mm²/m (cobre)
    ΔU = 3% (vivienda), 5% (concurrencia/industrial)

Sección mínima = max(sección_CDT, sección_IZ)
```

---

## 🌐 Estructura (7 páginas independientes)

| URL | Página | Descripción |
|-----|--------|-------------|
| `/` | Menú | Navegación principal |
| `/vivienda` | Vivienda | Circuitos C1-C13 |
| `/edificio` | Edificio | CGP, LGA, centralización |
| `/circuito` | Circuito | Cálculo genérico |
| `/di` | DI | Derivación individual |
| `/ejercicios` | Ejercicios | Resolución con IA |
| `/proyecto` | Proyecto | Generador proyectos |
| `/buscar` | Buscar | Búsqueda normativa |

**Header de navegación**: 7 iconos en todas las páginas para cambio rápido entre secciones.

---

## 🖥️ Interfaz Web

### Características
- Headernav con 7 iconos
- Tema dark neon
- Botones MEM y SVG para descarga
- Esquema unifilar SVG
- Resultados en tablas

### Uso
1. Seleccionar opción del header
2. Rellenar formulario
3. Clic en "Calcular"
4. Ver resultados + esquema + descargar

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

**Pasos:**
```bash
# 1. Subir a GitHub
git add .
git commit -m "Calculadora REBT v2"
git push -u origin main

# 2. Importar en Vercel
# Ir a vercel.com > Import Project > seleccionar repositorio

# 3. Configurar (sin RAG)
- Framework: Flask
- Build: pip install -r requirements.txt  
- Output: gunicorn app:app --bind 0.0.0.0:$PORT

# Notas:
- RAG excluded (sentence-transformers > 500MB)
- Búsqueda normativa solo local
```

---

## 🔧 Tecnologías

- **Python 3.12+**
- **Flask** - Web framework
- **Jinja2** - Templates
- **Gunicorn** - Servidor producción

---

## ✅ Funcionalidades Completadas

✅ Cálculo automático de circuitos según ITC-BT-25  
✅ Electrificación básica/elevada automática  
✅ Sección de cables por intensidad y caída de tensión  
✅ Selección de protecciones (PIA, IGA, fusibles)  
✅ Dimensionado de tubes (ITC-BT-21)  
✅ Esquema unifilar SVG  
✅ Cálculo de edificios completos  
✅ 7 páginas independientes  
✅ Header de navegación con iconos  
✅ Botones MEM/SVG para descarga  
✅ API REST `/api/calcular`  
✅ Resolución de ejercicios paso a paso  

---

## 📂 Archivos del Proyecto

| Archivo | Descripción |
|---------|-------------|
| `app.py` | Aplicación Flask |
| `src/engine_rebt.py` | Motor de cálculo |
| `src/schemes.py` | Generación esquemas SVG |
| `src/pdf_extractor.py` | Extracción PDFs |
| `src/rag_vectorstore.py` | ChromaDB para RAG |
| `src/resolutor.py` | Resolución ejercicios |
| `templates/index_*.html` | 7 plantillas web |
| `vercel.json` | Config Vercel |
| `requirements.txt` | Dependencias (prod) |

---

## 📅 Registro de Cambios

- **Abril 2026**: Separación en 7 páginas independientes, header de navegación, botones MEM/SVG
- **2025**: RAG con normativa, resolución ejercicios IA
- **2024**: Cálculo básico viviendas y edificios

**Autores:** -
**Licencia:** MIT