"""
Generador de Proyectos Eléctricos
Basado en tus 5 proyectos reales
"""

from datetime import datetime
from typing import Dict, Optional
from src.engine_rebt import (
    calcular_circuitos_vivienda, calcular_edificio,
    calcular_intensidad, calcular_intensidad_trifasica,
    calcular_seccion_por_intensidad, calcular_pia, calcular_tubo,
    CIRCUITOS_ITC25
)


TIPOS_PROYECTO = {
    "vivienda": "Vivienda Unifamiliar",
    "local": "Local Comercial",
    "nave": "Nave Industrial",
    "oficina": "Oficina",
    "bar": "Bar/Restaurante",
}


def detectar_tipo(proyecto: Dict) -> str:
    """Detecta el tipo de proyecto"""
    nombre = proyecto.get('nombre', '').lower()
    if 'bar' in nombre or 'restaurante' in nombre or 'café' in nombre:
        return "bar"
    elif 'nave' in nombre or 'industrial' in nombre or 'taller' in nombre:
        return "nave"
    elif 'oficina' in nombre or 'despacho' in nombre:
        return "oficina"
    elif 'local' in nombre or 'tienda' in nombre:
        return "local"
    return "vivienda"


def generar_proyecto(datos: Dict) -> str:
    """Genera un proyecto eléctrico completo"""
    
    tipo = datos.get('tipo', 'vivienda')
    nombre = datos.get('nombre', 'Proyecto Eléctrico')
    direccion = datos.get('direccion', 'Sin dirección')
    superficie = datos.get('superficie', 100)
    potencia = datos.get('potencia', 5000)
    n_circuitos = datos.get('n_circuitos', 5)
    
    fecha = datetime.now().strftime("%d/%m/%Y")
    
    proyecto = f"""
================================================================================
                         MEMORIA DEL PROYECTO
                    INSTALACIÓN ELÉCTRICA DE BAJA TENSIÓN
================================================================================

DATOS GENERALES
================================================================================
Nombre del proyecto: {nombre}
Tipo de instalación: {TIPOS_PROYECTO.get(tipo, tipo)}
Dirección: {direccion}
Fecha: {fecha}
Superficie: {superficie} m²
Potencia instalada: {potencia} W

================================================================================
1. OBJETO DEL PROYECTO
================================================================================
El presente proyecto tiene por objeto establecer las características técnicas de la
instalación eléctrica de baja tensión para {TIPOS_PROYECTO.get(tipo, tipo.lower())},
cumpliendo con el Reglamento Electrotécnico de Baja Tensión (REBT) y sus ITCs.

================================================================================
2. POTENCIA PREVISTA
================================================================================
Potencia instalada: {potencia} W ({potencia/1000:.2f} kW)
"""
    
    # Cálculos según tipo
    if tipo == "vivienda":
        resultado = calcular_circuitos_vivienda(
            puntos_luz=datos.get('puntos_luz', 20),
            Tomas=datos.get('tomas', 20),
            lavadora=datos.get('lavadora', False),
            cocina=datos.get('cocina', False),
            longitud=datos.get('longitud', 25)
        )
        
        proyecto += f"""
Grado de electrificación: {resultado['electrificacion'].upper()}
Potencia total: {resultado['potencia_total']} W

CIRCUITOS (ITC-BT-25):
"""
        for circ in resultado['circuitos']:
            proyecto += f"  {circ.codigo} - {circ.nombre[:25]:25s} P={circ.potencia:5d}W  S={circ.seccion}mm²  PIA={circ.pia}A\n"
        
        di = resultado['derivacion_individual']
        proyecto += f"""
DERIVACIÓN INDIVIDUAL:
  Sección: {di.seccion} mm²
  Tubo: {di.tubo} mm
  Protección (IGA): {di.iga} A
  Potencia: {di.potencia} W
"""
    
    else:
        #Para otros tipos (local, nave, oficina, bar)
        intensidad = calcular_intensidad(potencia, 230)
        seccion, iz = calcular_seccion_por_intensidad(intensidad, "B1", "2xPVC")
        proteccion = calcular_pia(intensidad)
        tubo = calcular_tubo(seccion)
        
        proyecto += f"""
Intensidad de cálculo: {intensidad:.2f} A
Sección del conductor: {seccion} mm² (Iz={iz}A)
Protección magnetotérmica: {proteccion} A
Tubo protector: {tubo} mm

Nº de circuitos previstos: {n_circuitos}
"""
    
    # Continuar con apartados comunes
    proyecto += f"""
================================================================================
3. INSTALACIÓN DE ENLACE
================================================================================
"""
    if tipo == "vivienda":
        proyecto += f"""
- Caja general de protección (CGP): En fachada
- Línea general de alimentación (LGA): {superficie//10 + 6}mm²
- Derivación individual: {potencia//1000 + 6}mm²
- Contador: En centralización
"""
    else:
        proyecto += f"""
- Acometida: trifásica 400V
- Caja general de protección (CGP): Exterior
- Línea general de alimentación: {potencia//2000 + 10}mm²
- Contadores: Centralización
"""
    
    proyecto += f"""
================================================================================
4. INSTALACIÓN INTERIOR
================================================================================
4.1 Cuadro Principal:
"""
    if tipo == "vivienda":
        proyecto += """
- 1 Interruptor general automático (IGA)
- 1 Interruptor diferencial 30mA
- PIAs para cada circuito (C1-C13)
"""
    else:
        proyecto += f"""
- 1 Interruptor general automático: {potencia//2000 + 40}A
- 1 Interruptor diferencial 30mA
- {n_circuitos} PIAs para circuitos
"""
    
    proyecto += f"""
4.2 Tomas de corriente: {superficie // 5 + 10} uds
4.3 Puntos de luz: {superficie // 10 + 10} uds

================================================================================
5. SPECIFICACIONES TÉCNICAS
================================================================================
- Tensión nominal: 230V / 400V (trifásico para {tipo})
- Frecuencia: 50 Hz
- Grado de protección envolvente: IP44
- Sistema de instalación: Tubos corrugados
- Conductor: Cobre rígido (H07V-K)
- Aislamiento: XLPE o PVC
- Protección: Diferencial 30mA + Magnetotérmica

================================================================================
6. CÁLCULOS JUSTIFICATIVOS
================================================================================
6.1 Intensidad:
    I = P / (U × fp)
    I = {potencia} / (230 × 0.8) = {potencia / 184:.2f} A
"""
    
    if tipo != "vivienda":
        seccion, iz = calcular_seccion_por_intensidad(potencia/184, "B1", "2xPVC")
        proyecto += f"""
6.2 Sección por intensidad admisible:
    Sección calculada: {seccion} mm² (Iz={iz}A)
    Selección: Normalizar a {max(seccion, 4)}mm²
"""
    
    proyecto += f"""
================================================================================
7. DOCUMENTACIÓN GRÁFICA
================================================================================
- Plano de situación
- Plano de distribución
- Esquema unifilar
- Detalles constructivos

================================================================================
8. PRESUPUESTO APROXIMADO
================================================================================
"""
    
    # Presupuesto aproximado
    if tipo == "vivienda":
        presupuesto = 800 + potencia // 100
    elif tipo == "bar" or tipo == "local":
        presupuesto = 1500 + potencia // 50
    else:
        presupuesto = 2000 + potencia // 30
    
    proyecto += f"""
- Cuadro eléctrico: 150-250 €
- Cable y tubos: {presupuesto // 3} €
- Mecanismos: {presupuesto // 4} €
- Mano de obra: {presupuesto // 2} €
- Varios: {presupuesto // 6} €
─────────────────────────────────
TOTAL: {presupuesto} € (aprox)

================================================================================
Fdo.: ________________________
Fecha: {fecha}
================================================================================
"""
    return proyecto


def guardar_proyecto(proyecto: str, filename: str = "proyecto.txt"):
    """Guarda el proyecto"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(proyecto)
    return filename


if __name__ == "__main__":
    # Ejemplo
    datos = {
        'tipo': 'bar',
        'nombre': 'Bar El Gran',
        'direccion': 'Calle Mayor 15',
        'superficie': 120,
        'potencia': 15000,
    }
    proyecto = generar_proyecto(datos)
    print(proyecto)