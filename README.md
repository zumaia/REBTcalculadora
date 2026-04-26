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
- ✅ Sección de cables por intensité y caída de tensión
- ✅ Selección de protecciones (PIA, IGA, fusibles)
- ✅ Dimensionado de tubos
- ✅ Esquema unifilar ASCII
- ✅ Cálculo de edificios completos

## 🚀 Despliegue

```bash
# Desarrollo
pip install -r requirements.txt
python app.py

# Producción
gunicorn app:app --bind 0.0.0.0:$PORT
```

## 📁 Estructura

```
REBT_Project/
├── app.py              # Aplicación Flask
├── src/
│   ├── engine_rebt.py  # Motor de cálculo
│   ├── modules/       # Módulos UF
│   └── schemes.py     # Generación esquemas
├── templates/
│   └── index.html    # Interfaz web
├── ejercicios/       # Ejercicios prácticos
├── esquemas/        # Esquemas generados
└── normativa/       # PDFs ITC-BT
```

## 📖 Uso

1. Abre `http://localhost:5000`
2. Selecciona el tipo de cálculo
3. Introduce los datos
4. Obtén resultados y esquema

## 🛠️ Tecnologías

- Python 3.12+
- Flask
- Jinja2

## 📝 Licencia

MIT License - Ver archivo `LICENSE`

---

⚡ Instalaciones eléctricas - ITC-BT 12, 13, 14, 15, 19, 25, 28, 44