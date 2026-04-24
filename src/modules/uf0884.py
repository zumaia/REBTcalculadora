"""
UF0884 - Instalaciones de Enlace
Cálculo de CGP, LGA, Centralización y Derivaciones Individuales
Según ITC-BT-12, ITC-BT-13, ITC-BT-14, ITC-BT-15
"""

import math
from typing import Dict, List, Tuple

VOLTAJE_FASE = 230
VOLTAJE_LINEA = 400
COS_PHI_DEFAULT = 0.8

IZ_TABLES = {
    "B1": {
        "2xPVC": {1.5: 14.5, 2.5: 18.5, 4: 24, 6: 31, 10: 42, 16: 56, 25: 73, 35: 89},
        "3xPVC": {1.5: 13, 2.5: 16.5, 4: 21, 6: 27, 10: 36, 16: 48, 25: 62, 35: 77},
    },
    "B2": {
        "2xPVC": {1.5: 13, 2.5: 17.5, 4: 22, 6: 28, 10: 38, 16: 52, 25: 68, 35: 84},
    },
}

DT_MAX = {
    "vivienda": {"lga": 1, "di": 1},
    "edificio": {"lga": 0.5, "di": 1},
}

RESISTIVIDAD = {"cobre": 0.018, "aluminio": 0.028}


def calcular_intensidad(potencia: float, tension: float = VOLTAJE_FASE, fp: float = 1.0) -> float:
    return potencia / (tension * fp)


def calcular_intensidad_trifasica(potencia: float, tension: float = VOLTAJE_LINEA, fp: float = 0.8) -> float:
    return potencia / (tension * fp * math.sqrt(3))


def calcular_seccion_cdt(potencia: float, longitud: float, cdt_percent: float,
                       tension: float = VOLTAJE_FASE, fp: float = 1.0,
                       material: str = "cobre") -> float:
    cdt = (cdt_percent / 100) * tension
    resistividad = RESISTIVIDAD[material]
    seccion = (2 * resistividad * potencia * longitud) / (cdt * tension * fp)
    return math.ceil(seccion * 10) / 10


def calcular_seccion_por_intensidad(intensidad: float, metodo: str = "B1",
                                  aislamiento: str = "2xPVC") -> Tuple[float, int]:
    tabla = IZ_TABLES.get(metodo, IZ_TABLES["B1"]).get(aislamiento, IZ_TABLES["B1"]["2xPVC"])
    for seccion, iz in tabla.items():
        if iz >= intensidad:
            return seccion, iz
    return 25, 73


def calcular_pia(intensidad: float) -> int:
    comerciales = [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100]
    for calibres in comerciales:
        if calibres >= intensidad:
            return calibres
    return comerciales[-1]


def calcular_fusible(intensidad: float) -> int:
    comerciales = [10, 16, 20, 25, 32, 35, 40, 50, 63, 80, 100, 125, 160, 200, 250]
    for calibres in comerciales:
        if calibres >= intensidad:
            return calibres
    return comerciales[-1]


def get_tubo_diametro(seccion: int, n_conductores: int = 3) -> int:
    tabla_tubos = {1.5: 16, 2.5: 20, 4: 20, 6: 25, 10: 32, 16: 40, 25: 40, 35: 50, 50: 63, 70: 63, 95: 75}
    base = tabla_tubos.get(seccion, 40)
    if n_conductores > 3:
        base = int(base * 1.5)
    return base


def normalizar_seccion(seccion: float) -> int:
    normalizadas = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120]
    for s in normalizadas:
        if s >= seccion:
            return s
    return normalizadas[-1]


def previson_carga_viviendas(num_viviendas_basicas: int, num_viviendas_elevadas: int) -> float:
    """Calcula la預visión de carga total del edificio"""
    potencia_basica = 5750
    potencia_elevada = 9200
    
    # Coeficiente de simultaneidad según ITC-BT-10
    # Viviendas grado básico: 5750W, grado elevado: 9200W
    potencia = (num_viviendas_basicas * potencia_basica) + (num_viviendas_elevadas * potencia_elevada)
    
    # Aplicar coeficiente de simultaneidad
    if num_viviendas_elevadas <= 3:
        coef = 1.0
    elif num_viviendas_elevadas <= 5:
        coef = 0.8
    elif num_viviendas_elevadas <= 10:
        coef = 0.7
    elif num_viviendas_elevadas <= 15:
        coef = 0.6
    else:
        coef = 0.5
    
    return potencia * coef


def calcular_lga(num_viviendas: int, potencia_viviendas: float, potencia_servicios: float = 0,
                longitud: float = 10, es_trifasica: bool = False) -> Dict:
    """Calcula la Línea General de Alimentación"""
    potencia_total = potencia_viviendas + potencia_servicios
    
    if es_trifasica:
        intensidad = calcular_intensidad_trifasica(potencia_total, 400, 0.9)
        tension = 400
    else:
        intensidad = calcular_intensidad(potencia_total, 230, 0.9)
        tension = 230
    
    cdt_max = DT_MAX["edificio"]["lga"]
    seccion_cdt = calcular_seccion_cdt(potencia_total, longitud, cdt_max, tension, 0.9)
    aislamiento = "3xPVC" if es_trifasica else "2xPVC"
    seccion, iz = calcular_seccion_por_intensidad(intensidad, "B1", aislamiento)
    seccion_final = normalizar_seccion(max(seccion, seccion_cdt, 6))
    
    n_conductores = 5 if es_trifasica else 3
    tubo = get_tubo_diametro(seccion_final, n_conductores)
    fusible = calcular_fusible(intensidad)
    iga = calcular_pia(intensidad)
    
    return {
        "potencia": potencia_total,
        "intensidad": round(intensidad, 2),
        "seccion_cdt": round(seccion_cdt, 2),
        "seccion": seccion_final,
        "tubo": tubo,
        "n_conductores": n_conductores,
        "fusible": fusible,
        "iga": iga,
        "cdt_max": cdt_max
    }


def calcular_servicios_generales(potencia: float, superficie: str, ventilacion: str) -> float:
    """Calcula la potencia de servicios generales del edificio"""
    # Ascensores
    potencia_ascensor = 0
    
    # Alumbrado逃生
    potencia_alumbrado = superficie * 10  # 10 W/m²
    
    # Ventilación forzada
    if ventilacion == "forzada":
        potencia_ventilacion = superficie * 3  # 3 W/m²
    else:
        potencia_ventilacion = superficie * 1  # 1 W/m²
    
    # Porteros, interfonos, etc.
    potencia_auxiliares = 200
    
    return potencia + potencia_ascensor + potencia_alumbrado + potencia_ventilacion + potencia_auxiliares


def calcular_local_comercial(superficie: float) -> float:
    """Calcula la potencia prevista para un local comercial"""
    # 100 W/m² hasta 100m², más 50 W/m² del resto
    if superficie <= 100:
        return superficie * 100
    else:
        return 10000 + (superficie - 100) * 50


def calcular_garaje(superficie: float, ventilacion: str) -> float:
    """Calcula la potencia prevista para un garaje"""
    if ventilacion == "forzada":
        return superficie * 3  # 3 W/m² con ventilación forzada
    else:
        return superficie * 1  # 1 W/m² con ventilación natural


def calcular_edificio_completo(num_viviendas_basicas: int, num_viviendas_elevadas: int,
                               potencia_servicios: float = 0, superficie_local: float = 0,
                               superficie_garaje: float = 0, ventilacion_garaje: str = "natural",
                               longitud_lga: float = 10, es_trifasica: bool = False,
                               longitud_di: float = 15) -> Dict:
    """Calcula toda la instalación de enlace de un edificio"""
    
    # 1. Previsión de cargas
    pot_basicas = num_viviendas_basicas * 5750
    pot_elevadas = num_viviendas_elevadas * 9200
    pot_viviendas = pot_basicas + pot_elevadas
    
    # Coeficiente de simultaneidad
    n_total = num_viviendas_basicas + num_viviendas_elevadas
    if n_total <= 3:
        coef = 1.0
    elif n_total <= 5:
        coef = 0.8
    elif n_total <= 10:
        coef = 0.7
    elif n_total <= 15:
        coef = 0.6
    else:
        coef = 0.5
    
    pot_viviendas_coef = pot_viviendas * coef
    
    # 2. Servicios generales
    pot_serv = potencia_servicios if potencia_servicios > 0 else calcular_garaje(superficie_garaje, ventilacion_garaje)
    
    # 3. Local comercial
    pot_local = calcular_local_comercial(superficie_local) if superficie_local > 0 else 0
    
    # Potencia total
    pot_total = pot_viviendas_coef + pot_serv + pot_local
    
    # Cálculo LGA
    lga = calcular_lga(n_total, pot_total, 0, longitud_lga, es_trifasica)
    
    # Derivaciones individuales por vivienda
    di_por_vivienda = []
    for i in range(num_viviendas_basicas):
        potencia = 5750 * 1.5
        intensidad = calcular_intensidad(potencia, 230)
        seccion = normalizar_seccion(max(6, calcular_seccion_cdt(potencia, longitud_di, 1, 230)))
        di_por_vivienda.append({
            "vivienda": i + 1,
            "tipo": "básica",
            "potencia": potencia,
            "intensidad": round(intensidad, 2),
            "seccion": seccion,
            "tubo": get_tubo_diametro(seccion, 3)
        })
    
    for i in range(num_viviendas_elevadas):
        potencia = 9200 * 1.5
        intensidad = calcular_intensidad(potencia, 230)
        seccion = normalizar_seccion(max(6, calcular_seccion_cdt(potencia, longitud_di, 1, 230)))
        di_por_vivienda.append({
            "vivienda": num_viviendas_basicas + i + 1,
            "tipo": "elevada",
            "potencia": potencia,
            "intensidad": round(intensidad, 2),
            "seccion": seccion,
            "tubo": get_tubo_diametro(seccion, 3)
        })
    
    return {
        "num_viviendas": num_viviendas_basicas + num_viviendas_elevadas,
        "potencia_viviendas": pot_viviendas,
        "potencia_viviendas_coef": pot_viviendas_coef,
        "potencia_servicios": pot_serv,
        "potencia_local": pot_local,
        "potencia_total": pot_total,
        "coef_simultaneidad": coef,
        "lga": lga,
        "derivaciones_individuales": di_por_vivienda
    }