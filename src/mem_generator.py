"""
Generador de Memoria Técnica de Diseño (MEM)
Documento obligatorio según REBT ITC-BT-04
"""

from datetime import datetime
from typing import Dict, List, Optional
from src.engine_rebt import (
    calcular_intensidad, calcular_intensidad_trifasica,
    calcular_seccion_cdt, calcular_seccion_por_intensidad,
    calcular_pia, calcular_tubo, normalizar_seccion,
    CIRCUITOS_ITC25
)


def generar_mem_vivienda(datos: Dict, resultado: Dict) -> str:
    """Genera MEM para vivienda"""
    
    fecha = datetime.now().strftime("%d/%m/%Y")
    
    mem = f"""
MEMORIA TÉCNICA DE DISEÑO (MEM)
REGLAMENTO ELECTROTÉCNICO DE BAJA TENSIÓN
ITC-BT-04

================================================================================
1. DATOS GENERALES
================================================================================
Fecha: {fecha}
Tipo de instalación: VIVIENDA
Grado de electrificación: {resultado['electrificacion'].upper()}
Potencia total: {resultado['potencia_total']} W ({resultado['potencia_total']/1000:.2f} kW)

================================================================================
2. POTENCIA PREVISTA POR CIRCUTO (ITC-BT-25)
================================================================================
"""
    
    for circ in resultado['circuitos']:
        mem += f"""
{circ.codigo} - {circ.nombre[:30]:30s} P={circ.potencia:5d}W  I={circ.intensidad:5.2f}A  S={circ.seccion}mm²  PIA={circ.pia}A"""
    
    di = resultado['derivacion_individual']
    mem += f"""

================================================================================
3. DERIVACIÓN INDIVIDUAL
================================================================================
Potencia: {di.potencia} W
Intensidad: {di.intensidad:.2f} A
Sección: {di.seccion} mm²
Tubo: {di.tubo} mm (Ø exterior)
Protección (IGA): {di.iga} A

================================================================================
4. CÁLCULOS JUSTIFICATIVOS
================================================================================
4.1 Intensidad:
    I = P / (U × fp)
    I = {di.potencia} / (230 × 0.8) = {di.intensidad:.2f} A

4.2 Sección por intensidad admisible:
    Según ITC-BT-19, método B1, PVC
    Sección calculada: {di.seccion} mm²

4.3 Sección por caída de tensión:
    CDT máx: 1% (derivación individual)
    S = 2 × ρ × P × L / (ΔU% × U × fp)
    S = {di.seccion} mm² (calculada)

================================================================================
5. ESPECIFICACIONES TÉCNICAS
================================================================================
- Tensión nominal: 230V / 400V
- Frecuencia: 50 Hz
- Grado de protección: IP44
- Sistema de instalación: Tubos en serie M20, M25, M32
- Conductor: Cobre rgido tipo H07V-K
- Aislamiento: XLPE (para tubos) o PVC (para cables)
- Protección diferencial: 30mA
- Protección magnetotérmica:PIA en cada circuito

================================================================================
6. ESQUEMA UNIFILAR (simplificado)
================================================================================
CGP (Caja de General de Protección)
    │
    ├─── IGA {di.iga}A
    │         │
    │    ┌───┴───┐
    │    │       │
    │   C1      C2   ... (circuitos)
    │    │       │
    └───┴───────┴── → Derivación Individual {di.seccion}mm²

================================================================================
7. PRESUPUESTO APROXIMADO (materiales)
================================================================================
- Cuadro eléctrico completo: 150-250 €
- Cable (200m): 80-120 €
- Tubos y accesorios: 60-100 €
- Mecanismos y tomas: 100-200 €
- Mano de obra: 200-400 €
─────────────────────────────────
TOTAL APROXIMADO: 500-1000 €

================================================================================
8. DECLARACIÓN
================================================================================
La presente Memoria Técnica de Diseño se elabora conforme a lo establecido
en la ITC-BT-04 del REBT, indicando que la instalación diseñada
cumple con los requisitos de seguridad establecidos.

Fdo.: ________________________
Fecha: {fecha}

"""
    return mem


def generar_mem_edificio(datos: Dict, resultado: Dict) -> str:
    """Genera MEM para edificio"""
    
    fecha = datetime.now().strftime("%d/%m/%Y")
    lga = resultado['lga']
    
    mem = f"""
MEMORIA TÉCNICA DE DISEÑO (MEM)
REGLAMENTO ELECTROTÉCNICO DE BAJA TENSIÓN
ITC-BT-04

================================================================================
1. DATOS GENERALES
================================================================================
Fecha: {fecha}
Tipo de instalación: EDIFICIO DE VIVIENDAS
Número de viviendas: {resultado['num_viviendas']}
  - Básicas: {datos.get('n_viviendas_basicas', 0)}
  - Elevadas: {datos.get('n_viviendas_elevadas', 0)}
Potencia total: {resultado['potencia_total']} W ({resultado['potencia_total']/1000:.1f} kW)
Coeficiente de simultaneidad: {resultado['coef_simultaneidad']}

================================================================================
2. PREVISIÓN DE CARGAS (ITC-BT-10)
================================================================================
Viviendas básicas (5750W): {datos.get('n_viviendas_basicas', 0)} × 5750 = {datos.get('n_viviendas_basicas', 0) * 5750}W
Viviendas elevadas (9200W): {datos.get('n_viviendas_elevadas', 0)} × 9200 = {datos.get('n_viviendas_elevadas', 0) * 9200}W
Servicios comunes: {resultado['potencia_servicios']}W
Locales: {resultado['potencia_local']}W
────────────────────────────────────────────
TOTAL: {resultado['potencia_total']}W

================================================================================
3. LÍNEA GENERAL DE ALIMENTACIÓN (LGA)
================================================================================
Tensión: 400V (trifásica)
Intensidad: {lga.intensidad:.2f} A
Sección: {lga.seccion} mm²
Tubo: {lga.tubo} mm
Fusible CGP: {lga.fusible} A

================================================================================
4. DERIVACIONES INDIVIDUALES
================================================================================
"""
    
    for di in resultado['derivaciones_individuales'][:10]:
        mem += f"Vivienda {di['vivienda']:2d} ({di['tipo']:7s}): {di['seccion']:2d}mm² - {di['tubo']:2d}mm\n"
    
    if len(resultado['derivaciones_individuales']) > 10:
        mem += f"... y {len(resultado['derivaciones_individuales'])-10} más\n"
    
    mem += f"""
================================================================================
5. CÁLCULO DE LGA
================================================================================
I = P / (U × √3 × fp)
I = {resultado['potencia_total']} / (400 × 1.732 × 0.8) = {lga.intensidad:.2f}A

Sección por intensidad: {lga.seccion}mm²
Sección por CDT (1%): {lga.seccion}mm² (calculada)
Tubo: {lga.tubo}mm

================================================================================
6. DECLARACIÓN
================================================================================
La presente Memoria Técnica de Diseño se elabora conforme a lo establecido
en la ITC-BT-04 del REBT para instalaciones de enlace.

Fdo.: ________________________
Fecha: {fecha}

"""
    return mem


def generar_mem_txt(datos: Dict, tipo: str = "vivienda") -> str:
    """Genera MEM según tipo"""
    from src.engine_rebt import calcular_circuitos_vivienda, calcular_edificio
    
    if tipo == "vivienda":
        resultado = calcular_circuitos_vivienda(
            datos.get('puntos_luz', 20),
            datos.get('tomas', 20),
            datos.get('lavadora', False),
            datos.get('cocina', False),
            datos.get('aire_ac', False),
            longitud=datos.get('longitud', 25)
        )
        return generar_mem_vivienda(datos, resultado)
    else:
        resultado = calcular_edificio(
            datos.get('n_viviendas_basicas', 4),
            datos.get('n_viviendas_elevadas', 6),
            datos.get('potencia_servicios', 0),
            datos.get('superficie_local', 0),
            datos.get('superficie_garaje', 0)
        )
        return generar_mem_edificio(datos, resultado)


def guardar_mem(mem: str, filename: str = "memoria_tecnica.txt"):
    """Guarda MEM en archivo"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(mem)
    return filename


if __name__ == "__main__":
    # Ejemplo
    datos = {'puntos_luz': 25, 'tomas': 25, 'cocina': True}
    mem = generar_mem_txt(datos, "vivienda")
    print(mem)