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
- **22 Calculadoras temáticas integradas (PDFs)**

## 🆕️ Calculadoras Implementadas (22 total)

### 4 Calculadoras Principales
1. **Sección de Cable** - Por amperaje y potencia (ITC-BT-19)
2. **Caída de Tensión** - Monofásica y trifásica (ITC-BT-25)
3. **Protección** - Sobrecarga y cortocircuito (curvas B, C, D)
4. **Paneles Solares** - Dimensionado completo sistema fotovoltaico

### 18 Calculadoras PDF (Carpeta CalculadorasBase)
5. **Baterías Solares** - Capacidad (Ah) y Autonomía
6. **Consumo Diario Solar** - Wh/Ah para dimensionado
7. **Divisor de Tensión** - Con y sin carga
8. **Factor de Potencia** - Corrección y coseno fi
9. **Resistencias en Paralelo** - Fórmula y resultado
10. **Consumo Eléctrico** - Convierte kWh a costo
11. **Cortocircuito Simplificada** - Icc sin datos de red
12. **Cortocircuito por Impedancias** - Datos de red
13. **Electrodos de Tierra** - Placas, cables y picas (ITC-BT-18)
14. **Longitud Máxima de Cable** - Distancia y voltaje
15. **Picas de Tierra** - ¿Cuántas jabalinas necesitas?
16. **Potencia Eléctrica** - Monofásica y trifásica
17. **Resistencia de un Conductor** - Resistividad
18. **Sección de Cables** - Potencia y distancia
19. **Sección por Caída de Tensión** - Distancia
20. **Ley de Ohm y Potencia** - V, I, R, P
21. **Código de Colores** - Resistencias 4 y 5 bandas

---

## 🏗️ Arquitectura

```
REBT_Project/
├── app.py                    # Aplicación Flask principal
├── src/
│   ├── engine_rebt.py         # Motor de cálculo REBT (UF0884, UF0887)
│   ├── calculadoras_pdf.py     # 22 módulos calculadoras PDF
│   ├── schemes.py             # Generación esquemas SVG
│   ├── svg_generator.py       # Generación SVG profesional
│   ├── mem_generator.py       # Generador MEM (proyectos)
│   ├── proyecto_generator.py  # Generador proyectos completos
│   ├── resolver.py            # Resolución ejercicios IA
│   ├── ollama_client.py       # Cliente Ollama local
│   └── modules/
│       ├── uf0884.py          # Instalaciones enlace
│       └── uf0887.py          # Instalaciones viviendas
├── templates/
│   ├── index.html             # Landing page (REBT info)
│   ├── index_vivienda.html    # Circuitos C1-C13 (ITC-BT-25)
│   ├── index_edificio.html    # Edificios (ITC-BT-10)
│   ├── index_circuito.html    # Cálculo genérico
│   ├── index_di.html          # Derivación individual
│   ├── index_ejercicios.html  # Resolución IA
│   ├── index_proyecto.html    # Generador proyectos
│   ├── index_buscar.html      # Búsqueda normativa
│   ├── calc_seccion.html       # Calculadora sección cable
│   ├── calc_caida.html        # Calculadora caída tensión
│   ├── calc_proteccion.html    # Calculadora protección
│   ├── calc_solar.html        # Calculadora paneles solares
│   ├── calc_baterias_solares.html
│   ├── calc_consumo_diario.html
│   ├── calc_divisor.html
│   ├── calc_fp.html
│   ├── calc_rparalelo.html
│   ├── calc_costo.html
│   ├── calc_icc_simplificado.html
│   ├── calc_icc_impedancias.html
│   ├── calc_tierra.html
│   ├── calc_longitud_max.html
│   ├── calc_picas.html
│   ├── calc_potencia_elec.html
│   ├── calc_rconductor.html
│   ├── calc_seccion_pot_dist.html
│   ├── calc_seccion_caida_dist.html
│   ├── calc_ohm.html
│   └── calc_codigo_colores.html
├── CalculadorasBase/         # PDFs originales (22 calculadoras)
├── vercel.json               # Config Vercel
└── requirements.txt         # Dependencias
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

## 🌐 Estructura (29 páginas total)

### Páginas Principales (7)
| URL | Página | Descripción |
|-----|--------|-------------|
| `/` | Landing | Info REBT + 22 calculadoras |
| `/vivienda` | Vivienda | Circuitos C1-C13 (ITC-BT-25) |
| `/edificio` | Edificio | CGP, LGA, centralización (ITC-BT-10) |
| `/circuito` | Circuito | Cálculo genérico |
| `/di` | DI | Derivación individual |
| `/ejercicios` | Ejercicios | Resolución con IA |
| `/proyecto` | Proyecto | Generador proyectos |
| `/buscar` | Buscar | Búsqueda normativa |

### Calculadoras PDF (22)
| URL | Calculadora | Descripción |
|-----|-------------|-------------|
| `/calc_seccion` | Sección Cable | Amperaje y potencia |
| `/calc_caida` | Caída Tensión | Monofásica/trifásica |
| `/calc_proteccion` | Protección | Sobrecarga/cortocircuito |
| `/calc_solar` | Paneles Solares | Dimensionado completo |
| `/calc_baterias_solares` | Baterías | Capacidad y autonomía |
| `/calc_consumo_diario` | Consumo Diario | Wh/Ah |
| `/calc_divisor` | Divisor Tensión | Con/sin carga |
| `/calc_fp` | Factor Potencia | Corrección |
| `/calc_rparalelo` | R Paralelo | Fórmula y resultado |
| `/calc_costo` | Costo | kWh a € |
| `/calc_icc_simplificado` | ICC Simplificado | Sin datos red |
| `/calc_icc_impedancias` | ICC Impedancias | Con datos red |
| `/calc_tierra` | Electrodos Tierra | Placas, cables, picas |
| `/calc_longitud_max` | Longitud Máxima | Distancia y voltaje |
| `/calc_picas` | Picas Tierra | ¿Cuántas jabalinas? |
| `/calc_potencia_elec` | Potencia Eléctrica | Mono/trifásica |
| `/calc_rconductor` | R Conductor | Resistividad |
| `/calc_seccion_pot_dist` | Sección Potencia | Potencia y distancia |
| `/calc_seccion_caida_dist` | Sección Caída | Distancia |
| `/calc_ohm` | Ley Ohm | V, I, R, P |
| `/calc_codigo_colores` | Código Colores | 4 y 5 bandas |

**Header de navegación**: 22 iconos en todas las páginas para cambio rápido entre calculadoras.

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

- **Abril 2026**: 22 calculadoras PDF integradas, landing page `/`, navegación completa 22 enlaces, 29 páginas total
- **Abril 2026**: Separación en 7 páginas principales, header de navegación, botones MEM/SVG
- **2025**: RAG con normativa, resolución ejercicios IA
- **2024**: Cálculo básico viviendas y edificios

## ✅ Funcionalidades Completadas (Actualizado Abril 2026)

✅ 22 Calculadoras temáticas integradas (PDFs)
✅ Landing page `/` con información REBT
✅ 29 páginas total (7 principales + 22 calculadoras)
✅ Navegación completa con 22 enlaces en todas las páginas
✅ Cálculo automático circuitos C1-C13 (ITC-BT-25)
✅ Electrificación básica/elevada automática
✅ Sección cables por intensidad y caída tensión
✅ Selección protecciones (PIA, IGA, fusibles)
✅ Dimensionado tubos (ITC-BT-21)
✅ Esquema unifilar SVG
✅ Cálculo edificios completos (ITC-BT-10)
✅ Resolución ejercicios con IA (Ollama local)
✅ Búsqueda normativa REBT
✅ Tema oscuro unificado (Inter font)
✅ Módulo `calculadoras_pdf.py` con 22 funciones
✅ Plantillas HTML unificadas con mismo diseño

**Autores:** -
**Licencia:** MIT