"""
UF0887 - Instalaciones Interiores en Viviendas
Cálculo de circuitos C1-C13 según ITC-BT-25
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
    "basica": {"interior": 3, "di": 1},
    "elevada": {"interior": 3, "di": 1},
}

RESISTIVIDAD = {"cobre": 0.018, "aluminio": 0.028}


def calcular_intensidad(potencia: float, tension: float = VOLTAJE_FASE, fp: float = COS_PHI_DEFAULT) -> float:
    return potencia / (tension * fp)


def calcular_seccion_cdt(potencia: float, longitud: float, cdt_percent: float,
                       tension: float = VOLTAJE_FASE, fp: float = COS_PHI_DEFAULT,
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
    comerciales = [6, 10, 16, 20, 25, 32, 40, 50, 63]
    for calibres in comerciales:
        if calibres >= intensidad:
            return calibres
    return comerciales[-1]


def get_tubo_diametro(seccion: int, n_conductores: int = 3) -> int:
    tabla_tubos = {1.5: 16, 2.5: 20, 4: 20, 6: 25, 10: 32, 16: 40, 25: 40, 35: 50}
    base = tabla_tubos.get(seccion, 40)
    if n_conductores > 3:
        base = int(base * 1.5)
    return base


def normalizar_seccion(seccion: float) -> int:
    normalizadas = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95]
    for s in normalizadas:
        if s >= seccion:
            return s
    return normalizadas[-1]


CIRCUITOS_VIVIENDA = {
    "C1": {"nombre": "Iluminación", "potencia": 2000, "fp": 1.0, "max_puntos": 30, "pia": 10, "seccion_min": 1.5},
    "C2": {"nombre": "Tomas uso general", "potencia": 3450, "fp": 1.0, "max_tomas": 20, "pia": 16, "seccion_min": 2.5},
    "C3": {"nombre": "Cocina eléctrica", "potencia": 5400, "fp": 0.9, "pia": 25, "seccion_min": 6},
    "C4": {"nombre": "Lavadora", "potencia": 2500, "fp": 0.9, "pia": 20, "seccion_min": 4},
    "C5": {"nombre": "Baño y aux. cocina", "potencia": 2500, "fp": 0.9, "pia": 20, "seccion_min": 4},
    "C6": {"nombre": "Calefacción", "potencia": 5750, "fp": 1.0, "pia": 32, "seccion_min": 6},
    "C7": {"nombre": "Tomas adicionales", "potencia": 3450, "fp": 1.0, "max_tomas": 20, "pia": 16, "seccion_min": 2.5},
    "C8": {"nombre": "Secadora", "potencia": 3500, "fp": 0.9, "pia": 20, "seccion_min": 4},
    "C9": {"nombre": "Aire acondicionado", "potencia": 2500, "fp": 0.9, "pia": 20, "seccion_min": 4},
    "C10": {"nombre": "Elevador", "potencia": 735, "fp": 0.85, "pia": 10, "seccion_min": 2.5},
    "C11": {"nombre": "Tomas außer", "potencia": 2300, "fp": 1.0, "pia": 16, "seccion_min": 2.5},
    "C12": {"nombre": "Toldos", "potencia": 3450, "fp": 1.0, "pia": 20, "seccion_min": 4},
}


def determinar_electrificacion(puntos_luz: int, Tomas: int, lavadora: bool, cocina: bool, 
                            aire_ac: bool = False, calefaccion: bool = False) -> str:
    """Determina si es electrificación básica o elevada"""
    tiene_mas_de_un_circuito_extra = False
    
    if Tomas > 20:
        tiene_mas_de_un_circuito_extra = True
    if cocina or aire_ac or calefaccion:
        tiene_mas_de_un_circuito_extra = True
    
    if tiene_mas_de_un_circuito_extra:
        return "elevada"
    return "basica"


def calcular_circuitos_vivienda(puntos_luz: int, Tomas: int, lavadora: bool = False, 
                             cocina: bool = False, aire_ac: bool = False,
                             longitud_circuito: float = 25) -> Dict:
    """
    Calcula los circuitos de una vivienda según ITC-BT-25
    Retorna: circuitos, electrificación, IGA, derivación individual
    """
    circuitos = []
    
    # C1 - Iluminación (siempre)
    circuitos.append({
        "codigo": "C1",
        "nombre": "Iluminación",
        "potencia": puntos_luz * 100,
        "fp": 1.0,
        "puntos": puntos_luz
    })
    
    # C2 y C7 - Tomas de corriente
    if Tomas <= 20:
        circuitos.append({
            "codigo": "C2",
            "nombre": "Tomas uso general",
            "potencia": 3450,
            "fp": 1.0,
            "tomas": Tomas
        })
    else:
        circuitos.append({
            "codigo": "C2",
            "nombre": "Tomas principales",
            "potencia": 3450,
            "fp": 1.0,
            "tomas": 20
        })
        circuitos.append({
            "codigo": "C7", 
            "nombre": "Tomas adicionales",
            "potencia": 3450,
            "fp": 1.0,
            "tomas": Tomas - 20
        })
    
    # C3 - Cocina eléctrica
    if cocina:
        circuitos.append({
            "codigo": "C3",
            "nombre": "Cocina eléctrica",
            "potencia": 5400,
            "fp": 0.9
        })
    
    # C4 - Lavadora
    if lavadora:
        circuitos.append({
            "codigo": "C4",
            "nombre": "Lavadora",
            "potencia": 2500,
            "fp": 0.9
        })
    
    # C5 - Baño y auxiliares de cocina
    circuitos.append({
        "codigo": "C5",
        "nombre": "Baño y aux. cocina",
        "potencia": 2500,
        "fp": 0.9
    })
    
    # C9 - Aire acondicionado
    if aire_ac:
        circuitos.append({
            "codigo": "C9",
            "nombre": "Aire acondicionado",
            "potencia": 2500,
            "fp": 0.9
        })
    
    # Calcular sección y PIA para cada circuito
    resultados = []
    potencia_total = 0
    
    for circ in circuitos:
        intensidad = calcular_intensidad(circ["potencia"], VOLTAJE_FASE, circ["fp"])
        seccion_cdt = calcular_seccion_cdt(circ["potencia"], longitud_circuito, 3, VOLTAJE_FASE, circ["fp"])
        seccion, iz = calcular_seccion_por_intensidad(intensidad, "B1", "2xPVC")
        seccion_final = normalizar_seccion(max(seccion, seccion_cdt, CIRCUITOS_VIVIENDA[circ["codigo"]]["seccion_min"]))
        pia = CIRCUITOS_VIVIENDA[circ["codigo"]]["pia"]
        tubo = get_tubo_diametro(seccion_final)
        
        potencia_total += circ["potencia"]
        
        resultados.append({
            "codigo": circ["codigo"],
            "nombre": circ["nombre"],
            "potencia": circ["potencia"],
            "intensidad": round(intensidad, 2),
            "seccion": seccion_final,
            "pia": pia,
            "tubo": tubo,
            "fp": circ["fp"]
        })
    
    # IGA (80% de la potencia total con factor de simultaneidad)
    iga = calcular_pia(potencia_total * 0.8 / VOLTAJE_FASE)
    
    # Electrificación
    electrificacion = determinar_electrificacion(puntos_luz, Tomas, lavadora, cocina, aire_ac)
    
    # Derivación Individual
    pot_total_con_coef = potencia_total * 0.8 * 1.5
    int_di = calcular_intensidad(pot_total_con_coef, VOLTAJE_FASE)
    seccion_di_cdt = calcular_seccion_cdt(pot_total_con_coef, 15, 1, VOLTAJE_FASE)
    seccion_di, _ = calcular_seccion_por_intensidad(int_di, "B1", "2xPVC")
    seccion_di_final = normalizar_seccion(max(seccion_di, seccion_di_cdt, 6))
    tubo_di = get_tubo_diametro(seccion_di_final, 3)
    
    return {
        "electrificacion": electrificacion,
        "potencia_total": potencia_total,
        "num_circuitos": len(resultados),
        "circuitos": resultados,
        "iga": iga,
        "derivacion_individual": {
            "seccion": seccion_di_final,
            "tubo": tubo_di,
            "intensidad": round(int_di, 2),
            "potencia": int(pot_total_con_coef)
        }
    }


def generar_tabla_circuitos(datos_vivienda: Dict) -> str:
    """Genera una tabla HTML con los circuitos"""
    html = '<table class="tabla-circuitos">'
    html += '<thead><tr>'
    html += '<th>Circuito</th><th>Descripción</th><th>P(W)</th><th>I(A)</th>'
    html += '<th>Sección</th><th>PIA</th><th>Tubo</th>'
    html += '</tr></thead><tbody>'
    
    for c in datos_vivienda["circuitos"]:
        html += f'<tr>'
        html += f'<td>{c["codigo"]}</td>'
        html += f'<td>{c["nombre"]}</td>'
        html += f'<td>{c["potencia"]}</td>'
        html += f'<td>{c["intensidad"]}</td>'
        html += f'<td>{c["seccion"]} mm²</td>'
        html += f'<td>{c["pia"]}A</td>'
        html += f'<td>{c["tubo"]}mm</td>'
        html += f'</tr>'
    
    html += '</tbody></table>'
    return html