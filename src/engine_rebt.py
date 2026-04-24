"""
Motor de Cálculo REBT - Módulos UF0884, UF0885, UF0887, UF0888
"""

import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# ============================================================
# CONSTANTES
# ============================================================

VOLTAJE_FASE = 230
VOLTAJE_LINEA = 400
COS_PHI_DEFAULT = 0.8

# ITC-BT-19: Intensidades máximas admisibles (A) para cables en tubo
IZ_TABLES = {
    "B1": {  # Conductores aislados en tubo empotrado
        "2xPVC": {1.5: 14.5, 2.5: 18.5, 4: 24, 6: 31, 10: 42, 16: 56, 25: 73, 35: 89, 50: 108, 70: 136, 95: 161},
        "3xPVC": {1.5: 13, 2.5: 16.5, 4: 21, 6: 27, 10: 36, 16: 48, 25: 62, 35: 77, 50: 93, 70: 117, 95: 138},
    },
    "B2": {  # Cables multiconductores en tubo empotrado
        "2xPVC": {1.5: 13, 2.5: 17.5, 4: 22, 6: 28, 10: 38, 16: 52, 25: 68, 35: 84, 50: 101, 70: 125, 95: 151},
        "3xPVC": {1.5: 11.5, 2.5: 15, 4: 19, 6: 24, 10: 32, 16: 44, 25: 56, 35: 70, 50: 84, 70: 107, 95: 128},
    },
    "E": {  # Cables al aire
        "2xPVC": {1.5: 18, 2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 101, 35: 125, 50: 151, 70: 192, 95: 229},
    },
}

# Caídas de tensión máximas (%)
CAIDAS_TENSION = {
    "vivienda": {"interior": 3, "di": 1, "lga": 1},
    "concurrencia": {"interior": 5, "di": 1, "lga": 0.5},
    "industrial": {"interior": 5, "di": 1, "lga": 1},
}

# Resistividad (Ω·mm²/m)
RESISTIVIDAD = {"cobre": 0.018, "aluminio": 0.028}

# Circuitos de vivienda según ITC-BT-25 COMPLETOS
CIRCUITOS_ITC25 = {
    "C1": {"nombre": "Iluminación", "potencia": 2000, "fp": 1.0, "pia": 10, "seccion": 1.5, "max": 30},
    "C2": {"nombre": "Tomas uso general", "potencia": 3450, "fp": 1.0, "pia": 16, "seccion": 2.5, "max": 20},
    "C3": {"nombre": "Cocina y horno", "potencia": 5400, "fp": 0.9, "pia": 25, "seccion": 6, "max": 1},
    "C4": {"nombre": "Lavadora/Lavaj/Termo", "potencia": 2500, "fp": 0.9, "pia": 20, "seccion": 4, "max": 1},
    "C5": {"nombre": "Tomas baños/aux.cocina", "potencia": 2500, "fp": 0.9, "pia": 20, "seccion": 4, "max": 6},
    "C6": {"nombre": "Iluminación extra", "potencia": 2000, "fp": 1.0, "pia": 10, "seccion": 1.5, "max": 30},
    "C7": {"nombre": "Tomas adicionales", "potencia": 3450, "fp": 1.0, "pia": 16, "seccion": 2.5, "max": 20},
    "C8": {"nombre": "Calefacción", "potencia": 5750, "fp": 1.0, "pia": 32, "seccion": 6, "max": 1},
    "C9": {"nombre": "Aire acondicionado", "potencia": 2500, "fp": 0.9, "pia": 20, "seccion": 4, "max": 1},
    "C10": {"nombre": "Secadora", "potencia": 3500, "fp": 0.9, "pia": 20, "seccion": 4, "max": 1},
    "C11": {"nombre": "Domótica/seguridad", "potencia": 500, "fp": 1.0, "pia": 10, "seccion": 1.5, "max": 1},
    "C12": {"nombre": "C3/C4/C5 extra", "potencia": 3450, "fp": 0.9, "pia": 20, "seccion": 4, "max": 6},
    "C13": {"nombre": "Recarga VE", "potencia": 3680, "fp": 0.95, "pia": 20, "seccion": 2.5, "max": 1},
}

# ============================================================
# CLASES DE DATOS
# ============================================================

@dataclass
class ResultadoCircuito:
    codigo: str
    nombre: str
    potencia: float
    intensidad: float
    seccion: int
    pia: int
    tubo: int
    fp: float = 0.8


@dataclass
class ResultadoDI:
    potencia: float
    intensidad: float
    seccion: int
    tubo: int
    n_conductores: int
    iga: int


@dataclass
class ResultadoLGA:
    potencia: float
    intensidad: float
    seccion: int
    tubo: int
    n_conductores: int
    fusible: int
    cdt: float


# ============================================================
# FUNCIONES DE CÁLCULO
# ============================================================

def calcular_intensidad(potencia: float, tension: float = VOLTAJE_FASE, fp: float = COS_PHI_DEFAULT) -> float:
    return potencia / (tension * fp)


def calcular_intensidad_trifasica(potencia: float, tension: float = VOLTAJE_LINEA, fp: float = COS_PHI_DEFAULT) -> float:
    return potencia / (tension * fp * math.sqrt(3))


def calcular_seccion_cdt(potencia: float, longitud: float, cdt_percent: float,
                       tension: float = VOLTAJE_FASE, fp: float = COS_PHI_DEFAULT,
                       material: str = "cobre") -> float:
    cdt = (cdt_percent / 100) * tension
    rho = RESISTIVIDAD[material]
    seccion = (2 * rho * potencia * longitud) / (cdt * tension * fp)
    return round(seccion, 2)


def calcular_seccion_por_intensidad(intensidad: float, metodo: str = "B1",
                                  aislamiento: str = "2xPVC") -> Tuple[float, int]:
    tabla = IZ_TABLES.get(metodo, IZ_TABLES["B1"]).get(aislamiento, IZ_TABLES["B1"]["2xPVC"])
    for seccion, iz in tabla.items():
        if iz >= intensidad:
            return seccion, iz
    return 120, tabla.get(120, 161)


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


def calcular_tubo(seccion: int, n_conductores: int = 3) -> int:
    tabla = {1.5: 16, 2.5: 20, 4: 20, 6: 25, 10: 32, 16: 40, 25: 40, 35: 50, 50: 63, 70: 63, 95: 75, 120: 90}
    base = tabla.get(seccion, 40)
    if n_conductores > 3:
        base = int(base * 1.5)
    return base


def normalizar_seccion(seccion: float) -> int:
    normalizadas = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120]
    for s in normalizadas:
        if s >= seccion:
            return s
    return normalizadas[-1]


# ============================================================
# CÁLCULOS DE VIVIENDA (UF0887)
# ============================================================

def determinar_electrificacion(puntos_luz: int, Tomas: int, lavadora: bool, cocina: bool,
                            aire_ac: bool = False, calefaccion: bool = False, 
                            secadora: bool = False, domotica: bool = False,
                            recarga_ve: bool = False) -> str:
    """Determina el grado de electrificación según ITC-BT-25"""
    # Si hay más de 30 puntos de luz -> elevada (C6)
    if puntos_luz > 30:
        return "elevada"
    # Si hay más de 20 tomas -> elevada (C7)
    if Tomas > 20:
        return "elevada"
    # Si hay equipos que añaden circuitos adicionales
    if cocina or aire_ac or calefaccion or secadora or domotica or recarga_ve:
        return "elevada"
    # Básica por defecto
    return "basica"


def calcular_circuitos_vivienda(puntos_luz: int, Tomas: int,
                              lavadora: bool = False, cocina: bool = False,
                              aire_ac: bool = False,
                              secadora: bool = False,
                              calefaccion: bool = False,
                              domotica: bool = False,
                              recarga_ve: bool = False,
                              longitud: float = 25,
                              tipo_instalacion: str = "vivienda") -> Dict:
    """Calcula circuitos de vivienda según ITC-BT-25 completo (C1-C13)"""
    circuitos = []
    
    # === 5 Circuitos Básicos (siempre obligatorios) ===
    
    # C1 - Iluminación (máx 30 puntos)
    puntos_c1 = min(puntos_luz, 30)
    circuitos.append({"codigo": "C1", "potencia": puntos_c1 * 100, "fp": 1.0})
    puntos_restantes = puntos_luz - 30
    if puntos_restantes > 0:
        circuitos.append({"codigo": "C6", "potencia": min(puntos_restantes, 30) * 100, "fp": 1.0})
    
    # C2 - Tomas uso general (máx 20)
    Tomas_c2 = min(Tomas, 20)
    circuitos.append({"codigo": "C2", "potencia": 3450, "fp": 1.0})
    Tomas_restantes = Tomas - 20
    
    # C3 - Cocina y horno
    if cocina:
        circuitos.append({"codigo": "C3", "potencia": 5400, "fp": 0.9})
    
    # C4 - Lavadora, lavavajillas y termo
    if lavadora:
        circuitos.append({"codigo": "C4", "potencia": 2500, "fp": 0.9})
    
    # C5 - Tomas baños y auxiliares cocina (máx 6)
    Tomas_c5 = min(Tomas_restantes, 6)
    if Tomas_c5 > 0 or True:  # Siempre incluido
        circuitos.append({"codigo": "C5", "potencia": 2500, "fp": 0.9})
    
    Tomas_restantes = max(0, Tomas_restantes - 6)
    
    # === Circuitos que disparan Electrificación Elevada ===
    
    # C6 - Iluminación extra (más de 30 puntos)
    if puntos_restantes > 0:
        pass  # Ya añadido como C6
    
    # C7 - Tomas adicionales (más de 20 = adicionales)
    Tomas_c7 = max(0, Tomas - 20)
    if Tomas_c7 > 0:
        circuitos.append({"codigo": "C7", "potencia": 3450, "fp": 1.0})
        circuitos.append({"codigo": "C7", "potencia": 3450, "fp": 1.0})
    
    # C8 - Calefacción eléctrica
    if calefaccion:
        circuitos.append({"codigo": "C8", "potencia": 5750, "fp": 1.0})
    
    # C9 - Aire acondicionado
    if aire_ac:
        circuitos.append({"codigo": "C9", "potencia": 2500, "fp": 0.9})
    
    # C10 - Secadora independiente
    if secadora:
        circuitos.append({"codigo": "C10", "potencia": 3500, "fp": 0.9})
    
    # C11 - Domótica y sistemas de seguridad
    if domotica:
        circuitos.append({"codigo": "C11", "potencia": 500, "fp": 1.0})
    
    # C12 - Circuitos adicionales de C3, C4 o C5
    # (se añade solo si hay más electrodomésticos específicos, no implementado por ahora)
    # C13 - Punto de recarga vehículo eléctrico
    if recarga_ve:
        circuitos.append({"codigo": "C13", "potencia": 3680, "fp": 0.95})
    
    # === Calcular sección y protecciones ===
    resultados = []
    pot_total = 0
    cdt_max = CAIDAS_TENSION.get(tipo_instalacion, CAIDAS_TENSION["vivienda"])["interior"]
    
    for circ in circuitos:
        intensidad = calcular_intensidad(circ["potencia"], VOLTAJE_FASE, circ["fp"])
        seccion_cdt = calcular_seccion_cdt(circ["potencia"], longitud, cdt_max, VOLTAJE_FASE, circ["fp"])
        seccion_min = CIRCUITOS_ITC25.get(circ["codigo"], {"seccion": 1.5})["seccion"]
        seccion, _ = calcular_seccion_por_intensidad(intensidad, "B1", "2xPVC")
        seccion_final = normalizar_seccion(max(seccion, seccion_cdt, seccion_min))
        
        pot_total += circ["potencia"]
        pia = CIRCUITOS_ITC25.get(circ["codigo"], {"pia": 10})["pia"]
        
        resultados.append(ResultadoCircuito(
            codigo=circ["codigo"],
            nombre=CIRCUITOS_ITC25.get(circ["codigo"], {"nombre": "Circuito"})["nombre"],
            potencia=circ["potencia"],
            intensidad=round(intensidad, 2),
            seccion=seccion_final,
            pia=pia,
            tubo=calcular_tubo(seccion_final),
            fp=circ["fp"]
        ))
    
    # IGA
    iga = calcular_pia(pot_total * 0.8 / VOLTAJE_FASE)
    
    # Electrificación
    electrificacion = determinar_electrificacion(puntos_luz, Tomas, lavadora, cocina, aire_ac, 
                                     calefaccion, secadora, domotica, recarga_ve)
    
    # Derivación Individual
    pot_di = pot_total * 0.8 * 1.5
    int_di = calcular_intensidad(pot_di, VOLTAJE_FASE)
    seccion_di_cdt = calcular_seccion_cdt(pot_di, 15, 1, VOLTAJE_FASE)
    seccion_di, _ = calcular_seccion_por_intensidad(int_di, "B1", "2xPVC")
    di_seccion = normalizar_seccion(max(seccion_di, seccion_di_cdt, 6))
    
    derivacion_individual = ResultadoDI(
        potencia=int(pot_di),
        intensidad=round(int_di, 2),
        seccion=di_seccion,
        tubo=calcular_tubo(di_seccion, 3),
        n_conductores=3,
        iga=iga
    )
    
    return {
        "electrificacion": electrificacion,
        "potencia_total": pot_total,
        "circuitos": resultados,
        "iga": iga,
        "derivacion_individual": derivacion_individual
    }


# ============================================================
# CÁLCULOS DE EDIFICIO (UF0884)
# ============================================================

def coef_simultaneidad(n_viviendas: int) -> float:
    """Coeficiente de simultaneidad según ITC-BT-10"""
    if n_viviendas <= 3:
        return 1.0
    elif n_viviendas <= 5:
        return 0.8
    elif n_viviendas <= 10:
        return 0.7
    elif n_viviendas <= 15:
        return 0.6
    elif n_viviendas <= 20:
        return 0.55
    elif n_viviendas <= 25:
        return 0.5
    else:
        return 0.45


def prevision_carga_viviendas(n_basicas: int, n_elevadas: int) -> float:
    """Previsión de carga de las viviendas"""
    potencia_basica = 5750
    potencia_elevada = 9200
    total = (n_basicas * potencia_basica) + (n_elevadas * potencia_elevada)
    return total * coef_simultaneidad(n_basicas + n_elevadas)


def calcular_servicios_generales(superficie_garaje: float, ventilacion: str = "natural") -> float:
    """Potencia de servicios generales"""
    if ventilacion == "forzada":
        return superficie_garaje * 3
    return superficie_garaje * 1


def calcular_lga(potencia: float, longitud: float, es_trifasica: bool = False,
               tipo_instalacion: str = "vivienda") -> ResultadoLGA:
    """Calcula la Línea General de Alimentación"""
    tension = 400 if es_trifasica else 230
    
    if es_trifasica:
        intensidad = calcular_intensidad_trifasica(potencia, tension)
    else:
        intensidad = calcular_intensidad(potencia, tension)
    
    cdt_max = CAIDAS_TENSION.get(tipo_instalacion, CAIDAS_TENSION["vivienda"])["lga"]
    seccion_cdt = calcular_seccion_cdt(potencia, longitud, cdt_max, tension)
    aislamiento = "3xPVC" if es_trifasica else "2xPVC"
    seccion, _ = calcular_seccion_por_intensidad(intensidad, "B1", aislamiento)
    seccion_final = normalizar_seccion(max(seccion, seccion_cdt, 6))
    
    n_conductores = 5 if es_trifasica else 3
    
    return ResultadoLGA(
        potencia=int(potencia),
        intensidad=round(intensidad, 2),
        seccion=seccion_final,
        tubo=calcular_tubo(seccion_final, n_conductores),
        n_conductores=n_conductores,
        fusible=calcular_fusible(intensidad),
        cdt=cdt_max
    )


def calcular_edificio(n_viviendas_basicas: int, n_viviendas_elevadas: int,
                   potencia_servicios: float = 0,
                   superficie_local: float = 0,
                   superficie_garaje: float = 0,
                   ventilacion_garaje: str = "natural",
                   longitud_lga: float = 10,
                   longitud_di: float = 15,
                   es_trifasica: bool = False) -> Dict:
    """Calcula instalación de enlace completa de un edificio"""
    n_total = n_viviendas_basicas + n_viviendas_elevadas
    
    # Previsión de cargas
    pot_viviendas = prevision_carga_viviendas(n_viviendas_basicas, n_viviendas_elevadas)
    pot_servicios = potencia_servicios if potencia_servicios > 0 else calcular_servicios_generales(superficie_garaje, ventilacion_garaje)
    pot_local = superficie_local * 100 if superficie_local > 0 else 0
    
    pot_total = pot_viviendas + pot_servicios + pot_local
    
    # LGA
    lga = calcular_lga(pot_total, longitud_lga, es_trifasica)
    
    # DI por vivienda
    dis = []
    for i in range(n_viviendas_basicas):
        pot = 5750 * 1.5
        intensidad = calcular_intensidad(pot, 230)
        seccion = normalizar_seccion(max(6, calcular_seccion_cdt(pot, longitud_di, 1, 230)))
        dis.append({
            "vivienda": i + 1,
            "tipo": "básica",
            "potencia": int(pot),
            "intensidad": round(intensidad, 2),
            "seccion": seccion,
            "tubo": calcular_tubo(seccion, 3)
        })
    
    for i in range(n_viviendas_elevadas):
        pot = 9200 * 1.5
        intensidad = calcular_intensidad(pot, 230)
        seccion = normalizar_seccion(max(6, calcular_seccion_cdt(pot, longitud_di, 1, 230)))
        dis.append({
            "vivienda": n_viviendas_basicas + i + 1,
            "tipo": "elevada",
            "potencia": int(pot),
            "intensidad": round(intensidad, 2),
            "seccion": seccion,
            "tubo": calcular_tubo(seccion, 3)
        })
    
    return {
        "num_viviendas": n_total,
        "potencia_viviendas": pot_viviendas,
        "potencia_servicios": pot_servicios,
        "potencia_local": pot_local,
        "potencia_total": pot_total,
        "coef_simultaneidad": coef_simultaneidad(n_total),
        "lga": lga,
        "derivaciones_individuales": dis
    }


# ============================================================
# GENERACIÓN DE ESQUEMA UNIFILAR
# ============================================================

def generar_esquema_unifilar(datos: Dict, tipo: str = "vivienda") -> str:
    """Genera esquema unifilar en texto ASCII"""
    
    if tipo == "vivienda":
        esquema = """
╔══════════════════════════════════════════════════════════════════╗
║            ESQUEMA UNIFILAR - VIVIENDA                 ║
╠══════════════════════════════════════════════════════════════════╣
║                                                          ║
║    ┌─────┐    ┌─────┐    ┌───────┐    ┌─────────────┐   ║
║    │ CGP │────│ ICP│────│ IGA  │────│ CUADRO    │   ║
║    │40A  │    │40A │    │ {iga}A │    │ INTERIOR  │   ║
║    └─────┘    └─────┘    └───────┘    └─────────────┘   ║
║        │                            │                     ║
║        │    ┌─────────────────────┴──────────────────┐   ║
║        │    │                                     │   ║
""".format(iga=datos.get("iga", 40))
        
        for i, circ in enumerate(datos.get("circuitos", [])):
            esquema += f"║        │    │ [{circ.codigo}] {circ.nombre[:15]:15s} {circ.seccion}mm² PI{a(circ.pia)}A  │   ║\n"
        
        esquema += """║        │    │                                     │   ║
║        │    └─────────────────────────────────────┘   ║
║        │                                        ║
║    ┌──┴──┐                                  ║
║    │ DI  │ S={di_seccion}mm² L={di_tubo}mm          ║
║    └─────┘                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        
    elif tipo == "edificio":
        esquema = """
╔══════════════════════════════════════════════════════════════════╗
║         ESQUEMA UNIFILAR - EDIFICIO                  ║
║         UF0884 - Instalaciones de Enlace             ║
╠══════════════════════════════════════════════════════════════════╣

       ┌────────────────────────────────────────────────────┐
       │           LÍNEA GENERAL DE ALIMENTACIÓN           │
       │      S={lga_seccion}mm²  L={lga_tubo}mm  F={lga_fusible}A    │
       └──────────────────────────┬─────────────────────┘
                                │
                    ┌──────────┴──────────┐
                    │        CGP         │
                    │    Fusible {fusible}A    │
                    └──────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴─────┐
        │ CONT 1   │   │ CONT 2   │   │ CONT {n}   │
        │ DI {d1}mm² │   │ DI {d2}mm² │   │ DI {dn}mm² │
        └───────────┘   └───────────┘   └───────────┘
""".format(
    lga_seccion=datos["lga"].seccion,
    lga_tubo=datos["lga"].tubo,
    lga_fusible=datos["lga"].fusible,
    fusible=datos["lga"].fusible,
    n=datos["num_viviendas"],
    d1=datos["derivaciones_individuales"][0]["seccion"],
    d2=datos["derivaciones_individuales"][1]["seccion"],
    dn=datos["derivaciones_individuales"][-1]["seccion"]
)
    
    return esquema


def formatear_resultados(datos: Dict, tipo: str = "vivienda") -> Dict:
    """Convierte los resultados a formato HTML"""
    
    if tipo == "vivienda":
        html = '<div class="resultados">'
        html += f'<div class="electrificacion">Electrificación: <strong>{datos["electrificacion"].upper()}</strong></div>'
        html += f'<div class="potencia">Potencia total: <strong>{datos["potencia_total"]} W</strong></div>'
        html += f'<div class="iga">IGA: <strong>{datos["iga"]} A</strong></div>'
        html += '<table class="circuitos">'
        html += '<thead><tr><th>Circuito</th><th>Nombre</th><th>P(W)</th><th>I(A)</th><th>Sección</th><th>PIA</th><th>Tubo</th></tr></thead><tbody>'
        
        for c in datos["circuitos"]:
            html += f'<tr><td>{c.codigo}</td><td>{c.nombre}</td><td>{c.potencia}</td><td>{c.intensidad}</td><td>{c.seccion} mm²</td><td>{c.pia}A</td><td>{c.tubo}mm</td></tr>'
        
        html += '</tbody></table>'
        html += '<div class="di">'
        html += '<h4>Derivación Individual</h4>'
        di = datos["derivacion_individual"]
        html += f'<p>Sección: {di.seccion} mm² | Tubo: {di.tubo}mm | IGA: {di.iga}A | Potencia: {di.potencia}W</p>'
        html += '</div></div>'
        
    return {"html": html}


def formatear_tabla(datos: Dict, tipo: str = "vivienda") -> str:
    """Formatea los datos como tabla HTML"""
    
    lines = []
    
    if tipo == "vivienda":
        lines.append("| Circuito | Descripción | P(W) | I(A) | Sección | PIA | Tubo |")
        lines.append("|----------|------------|------|------|--------|-----|------|------|")
        
        for c in datos["circuitos"]:
            lines.append(f"| {c.codigo} | {c.nombre[:15]} | {c.potencia} | {c.intensidad} | {c.seccion}mm² | {c.pia}A | {c.tubo}mm |")
        
        di = datos["derivacion_individual"]
        lines.append("")
        lines.append(f"| **DI** | | | | **{di.seccion}mm²** | | **{di.tubo}mm** |")
        lines.append(f"| IGA: {datos['iga']}A | Electrificación: {datos['electrificacion']} | Potencia: {datos['potencia_total']}W |")
    
    return "<br>".join(lines)