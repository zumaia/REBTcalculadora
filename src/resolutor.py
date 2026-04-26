"""
Resolutor de Ejercicios REBT
Identifica el tipo de problema y aplica los cálculos correspondientes
"""

import re
from typing import Dict, Optional, Tuple
from src.engine_rebt import (
    calcular_intensidad,
    calcular_intensidad_trifasica,
    calcular_seccion_cdt,
    calcular_seccion_por_intensidad,
    calcular_pia,
    calcular_tubo,
    normalizar_seccion,
    calcular_circuitos_vivienda,
    calcular_edificio,
    calcular_lga,
)


TIPOS_EJERCICIO = {
    "vivienda": ["vivienda", "c1", "c2", "c3", "c4", "c5", "c6", "c7", "circuito"],
    "edificio": ["edificio", "lga", "cgp", "centralización", "derivación"],
    "acometida": ["acometida", "línea", "trifásica", "400v"],
    "potencia": ["potencia", "w", "kw"],
}


def detectar_tipo(pregunta: str) -> str:
    """Detecta el tipo de ejercicio"""
    pregunta_lower = pregunta.lower()
    
    if any(p in pregunta_lower for p in ["acometida", "línea trifásica", "400v"]):
        return "acometida"
    elif any(p in pregunta_lower for p in ["vivienda", "c1", "c2", "c3", "c4", "c5"]):
        return "vivienda"
    elif any(p in pregunta_lower for p in ["edificio", "lga", "cgp", "centralización"]):
        return "edificio"
    elif any(p in pregunta_lower for p in ["derivación individual", "di"]):
        return "di"
    
    return "general"


def extraer_datos(pregunta: str) -> Dict:
    """Extrae datos numéricos del texto"""
    datos = {}
    
    # Potencia
    match = re.search(r'(\d+[\d,]*)\s*[kK][wW]', pregunta)
    if match:
        valor = match.group(1).replace(',', '.')
        datos['potencia'] = float(valor) * 1000 if 'k' in match.group(0).lower() else float(valor)
    
    # Intensidad
    match = re.search(r'(\d+[\d,]*)\s*[aA](?!utores)', pregunta)
    if match:
        datos['intensidad'] = float(match.group(1).replace(',', '.'))
    
    # Longitud
    match = re.search(r'(\d+[\d,]*)\s*m', pregunta)
    if match:
        datos['longitud'] = float(match.group(1).replace(',', '.'))
    
    # Tensión
    match = re.search(r'(\d+)\s*[vV]', pregunta)
    if match:
        datos['tension'] = float(match.group(1))
    
    # Factor de potencia
    match = re.search(r'[cf]p[=]?\s*0[,\.]?\d+', pregunta)
    if match:
        datos['fp'] = float(match.group(0).replace(',', '.').replace('fp', '').replace('cp', '').replace('=', ''))
    
    # Puntos de luz
    match = re.search(r'(\d+)\s*punto', pregunta)
    if match:
        datos['puntos_luz'] = int(match.group(1))
    
    # Tomas
    match = re.search(r'(\d+)\s*toma', pregunta)
    if match:
        datos['tomas'] = int(match.group(1))
    
    return datos


def resolver_acometida(datos: Dict) -> Dict:
    """Resuelve ejercicio de acometida"""
    potencia = datos.get('potencia', 45000)
    longitud = datos.get('longitud', 15)
    tension = datos.get('tension', 400)
    fp = datos.get('fp', 0.9)
    
    # Cálculo de intensidad
    if tension >= 400:
        intensidad = calcular_intensidad_trifasica(potencia, tension, fp)
    else:
        intensidad = calcular_intensidad(potencia, tension, fp)
    
    # Sección por CDT
    cdt = 1  # Acometida = 1%
    seccion_cdt = calcular_seccion_cdt(potencia, longitud, cdt, tension, fp)
    
    # Sección por intensidad
    seccion, iz = calcular_seccion_por_intensidad(intensidad, "E", "2xPVC")
    seccion_final = normalizar_seccion(max(seccion, seccion_cdt, 6))
    
    # Protección
    proteccion = calcular_pia(intensidad)
    
    # Tubo
    tubo = calcular_tubo(seccion_final, 5 if tension >= 400 else 3)
    
    return {
        "tipo": "Acometida",
        "pasos": [
            f"1. Datos: P={potencia/1000}kW, L={longitud}m, U={tension}V, fp={fp}",
            f"2. Intensidad: I = {potencia}/{tension}×{fp}×√3 = {intensidad:.2f}A" if tension >= 400 else f"2. Intensidad: I = {potencia}/{tension}×{fp} = {intensidad:.2f}A",
            f"3. Sección por CDT: S = {seccion_cdt:.2f}mm²",
            f"4. Sección por intensidad: {seccion}mm² (Iz={iz}A)",
            f"5. Sección final: {seccion_final}mm²",
            f"6. Protección: {proteccion}A",
            f"7. Tubo: {tubo}mm",
        ],
        "resultado": {
            "intensidad": round(intensidad, 2),
            "seccion": seccion_final,
            "proteccion": proteccion,
            "tubo": tubo,
        }
    }


def resolver_vivienda(datos: Dict) -> Dict:
    """Resuelve ejercicio de vivienda"""
    puntos_luz = datos.get('puntos_luz', 20)
    Tomas = datos.get('tomas', 20)
    longitud = datos.get('longitud', 25)
    
    resultado = calcular_circuitos_vivienda(
        puntos_luz=puntos_luz,
        Tomas=Tomas,
        longitud=longitud
    )
    
    pasos = [
        f"1. Datos: {puntos_luz} puntos de luz, {Tomas} Tomas",
        f"2. Electrificación: {resultado['electrificacion']}",
        f"3. Potencia total: {resultado['potencia_total']}W",
    ]
    
    for circ in resultado['circuitos']:
        pasos.append(f"   {circ.codigo}: {circ.nombre} - {circ.seccion}mm², PIA {circ.pia}A")
    
    pasos.extend([
        f"4. IGA: {resultado['iga']}A",
        f"5. Derivación Individual: {resultado['derivacion_individual'].seccion}mm²",
    ])
    
    return {
        "tipo": "Vivienda",
        "pasos": pasos,
        "resultado": resultado,
    }


def resolver_edificio(datos: Dict) -> Dict:
    """Resuelve ejercicio de edificio"""
    n_basicas = datos.get('viviendas_basicas', 4)
    n_elevadas = datos.get('viviendas_elevadas', 6)
    
    resultado = calcular_edificio(
        n_viviendas_basicas=n_basicas,
        n_viviendas_elevadas=n_elevadas,
    )
    
    pasos = [
        f"1. Datos: {n_basicas} básicas, {n_elevadas} elevadas",
        f"2. Coeficiente simultaneidad: {resultado['coef_simultaneidad']}",
        f"3. Potencia total: {resultado['potencia_total']}W",
        f"4. LGA: {resultado['lga'].seccion}mm², fusible {resultado['lga'].fusible}A",
    ]
    
    return {
        "tipo": "Edificio",
        "pasos": pasos,
        "resultado": resultado,
    }


def resolver_ejercicio(pregunta: str, datos_extra: Dict = None) -> Dict:
    """Resuelve un ejercicio REBT"""
    # Extraer datos del texto
    datos = extraer_datos(pregunta)
    if datos_extra:
        datos.update(datos_extra)
    
    # Detectar tipo
    tipo = detectar_tipo(pregunta)
    
    # Resolver según tipo
    if tipo == "acometida":
        return resolver_acometida(datos)
    elif tipo == "vivienda":
        return resolver_vivienda(datos)
    elif tipo == "edificio":
        return resolver_edificio(datos)
    else:
        # Intentar resolver como vivienda por defecto
        return resolver_vivienda(datos)


def formatear_resultado(resultado: Dict) -> str:
    """Formatea el resultado para mostrar"""
    output = []
    
    if "pasos" in resultado:
        output.append("## Pasos:")
        for paso in resultado["pasos"]:
            output.append(f"- {paso}")
    
    output.append("\n## Resultado:")
    res = resultado.get("resultado", resultado.get("resultado", {}))
    
    if isinstance(res, dict):
        if "seccion" in res:
            output.append(f"- Sección: {res.get('seccion', 'N/A')}mm²")
        if "proteccion" in res or "pia" in res or "iga" in res:
            protec = res.get('proteccion') or res.get('pia') or res.get('iga') or 'N/A'
            output.append(f"- Protección: {protec}A")
        if "tubo" in res:
            output.append(f"- Tubo: {res.get('tubo', 'N/A')}mm")
        if "intensidad" in res:
            output.append(f"- Intensidad: {res.get('intensidad', 'N/A')}A")
    else:
        output.append(str(res))
    
    return "\n".join(output)


if __name__ == "__main__":
    # Ejemplo
    ejercicio = "Calcular una acometida trifásica de 45kW, longitud 15m, 400V, fp=0.9"
    resultado = resolver_ejercicio(ejercicio)
    print(formatear_resultado(resultado))