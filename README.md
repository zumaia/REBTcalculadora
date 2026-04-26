# 🧮 Calculadora REBT

Aplicación web para cálculos de instalaciones eléctricas según el Reglamento Electrotécnico de Baja Tensión (REBT).

## 📋 Módulos

| UF | Descripción |
|-----|-------------|
| **UF0884** | Instalaciones de Enlace (CGP, LGA, DI) |
| **UF0885** | Puestas a tierra |
| **UF0887** | Instalaciones en Viviendas (C1-C13) |
| **UF0888** | Locales de Pública Concurrencia |

## 🔧 Funcionalidades

- ✅ Cálculo automático de circuitos según ITC-BT-25
- ✅ Electrificación básica/elevada
- ✅ Sección de cables por intensidad y caída de tensión
- ✅ Selección de protecciones (PIA, IGA, fusibles)
- ✅ Dimensionado de tubos
- ✅ Esquema unifilar SVG
- ✅ Cálculo de edificios completos
- ✅ 7 páginas independientes con header de navegación

## 🌐 Estructura (7 páginas)

```
/                    → Menú principal
/vivienda           → Circuitos C1-C13 (ITC-BT-25)
/edificio           → Instalaciones enlace (ITC-BT-10)
/circuito           → Cálculo genérico circuito
/di                 → Derivación individual
/ejercicios          → Resolución ejercicios IA
/proyecto           → Generador proyectos
/buscar             → Búsqueda normativa REBT
```

## 🚀 Despliegue

```bash
# Desarrollo
pip install -r requirements.txt
python app.py

# Producción
gunicorn app:app --bind 0.0.0.0:$PORT
```

## 📖 Uso

1. Abre la página (localhost o desplegada)
2. Usa el header de navegación para seleccionar opción
3. Rellena el formulario
4. Obtén resultados, esquema y opciones de descarga

## 🛠️ Tecnologías

- Python 3.12+
- Flask
- Jinja2

## 📝 Licencia

MIT License - Ver archivo `LICENSE`

---

⚡ Instalaciones eléctricas - ITC-BT 12, 13, 14, 15, 19, 25, 28, 44