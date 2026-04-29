"""
Calculadoras basadas en PDFs - REBT Project
Integra las calculadoras de la carpeta CalculadororasBase
Reutiliza funciones de engine_rebt.py
"""

import math
from typing import Dict, Tuple, Optional

# Importar funciones existentes
from engine_rebt import (
    calcular_intensidad,
    calcular_intensidad_trifasica,
    calcular_seccion_cdt,
    calcular_seccion_por_intensidad,
    calcular_pia,
    calcular_fusible,
    normalizar_seccion,
    calcular_tubo,
    IZ_TABLES,
    RESISTIVIDAD,
    VOLTAJE_FASE,
    VOLTAJE_LINEA,
    COS_PHI_DEFAULT,
    CAIDAS_TENSION
)


# ============================================================
# 1. CALCULADORA DE SECCIÓN DE CABLE POR AMPERAJE Y POTENCIA
# ============================================================

def calcular_seccion_cable_completa(
    potencia: float,
    tension: float = VOLTAJE_FASE,
    fp: float = COS_PHI_DEFAULT,
    longitud: float = 25,
    cdt_percent: float = 3,
    metodo: str = "B1",
    aislamiento: str = "2xPVC",
    material: str = "cobre",
    es_trifasica: bool = False
) -> Dict:
    """
    Calcula la sección de cable considerando intensidad y caída de tensión
    Según ITC-BT-19 e ITC-BT-25
    """
    # Calcular intensidad
    if es_trifasica:
        intensidad = calcular_intensidad_trifasica(potencia, tension, fp)
    else:
        intensidad = calcular_intensidad(potencia, tension, fp)
    
    # Sección por intensidad (ITC-BT-19)
    seccion_iz, iz_admisible = calcular_seccion_por_intensidad(intensidad, metodo, aislamiento)
    
    # Sección por caída de tensión (ITC-BT-25)
    seccion_cdt = calcular_seccion_cdt(potencia, longitud, cdt_percent, tension, fp, material)
    
    # Sección final (la mayor de ambas)
    seccion_final = normalizar_seccion(max(seccion_iz, seccion_cdt))
    
    # Tubo
    n_conductores = 5 if es_trifasica else 3
    tubo = calcular_tubo(seccion_final, n_conductores)
    
    # Protección
    pia = calcular_pia(intensidad)
    
    # Verificar caída de tensión real
    cdt_real = calcular_caida_tension_real(potencia, longitud, seccion_final, tension, fp, material, es_trifasica)
    
    return {
        "intensidad": round(intensidad, 2),
        "seccion_iz": seccion_iz,
        "iz_admisible": iz_admisible,
        "seccion_cdt": round(seccion_cdt, 2),
        "seccion_final": seccion_final,
        "tubo": tubo,
        "pia": pia,
        "cdt_real": round(cdt_real, 2),
        "cdt_max": cdt_percent,
        "cumple_cdt": cdt_real <= cdt_percent
    }


# ============================================================
# 2. CALCULADORA DE CAÍDA DE TENSIÓN
# ============================================================

def calcular_caida_tension_real(
    potencia: float,
    longitud: float,
    seccion: float,
    tension: float = VOLTAJE_FASE,
    fp: float = COS_PHI_DEFAULT,
    material: str = "cobre",
    es_trifasica: bool = False
) -> float:
    """
    Calcula la caída de tensión real en %
    Fórmula: ΔU% = (2 × ρ × P × L) / (U² × S × cosφ) × 100 (monofásica)
              ΔU% = (√3 × ρ × P × L) / (U² × S × cosφ) × 100 (trifásica)
    """
    rho = RESISTIVIDAD.get(material, 0.018)
    
    if es_trifasica:
        cdt = (math.sqrt(3) * rho * potencia * longitud) / (tension**2 * seccion * fp)
    else:
        cdt = (2 * rho * potencia * longitud) / (tension**2 * seccion * fp)
    
    return cdt * 100


def calcular_caida_tension_detallado(
    potencia: float,
    longitud: float,
    seccion: float,
    tension: float = VOLTAJE_FASE,
    fp: float = COS_PHI_DEFAULT,
    material: str = "cobre"
) -> Dict:
    """
    Calculadora completa de caída de tensión
    Retorna valores para monofásica y trifásica
    """
    # Monofásica
    cdt_mono = calcular_caida_tension_real(potencia, longitud, seccion, tension, fp, material, False)
    intensidad_mono = calcular_intensidad(potencia, tension, fp)
    
    # Trifásica
    cdt_tri = calcular_caida_tension_real(potencia, longitud, seccion, tension, fp, material, True)
    intensidad_tri = calcular_intensidad_trifasica(potencia, tension, fp)
    
    # Caída de tensión en voltios
    cdt_v_mono = (cdt_mono / 100) * tension
    cdt_v_tri = (cdt_tri / 100) * tension if tension >= 400 else (cdt_tri / 100) * VOLTAJE_LINEA
    
    return {
        "monofasica": {
            "cdt_percent": round(cdt_mono, 2),
            "cdt_volts": round(cdt_v_mono, 2),
            "intensidad": round(intensidad_mono, 2),
            "cumple": cdt_mono <= 3  # REBT: 3% interior
        },
        "trifasica": {
            "cdt_percent": round(cdt_tri, 2),
            "cdt_volts": round(cdt_v_tri, 2),
            "intensidad": round(intensidad_tri, 2),
            "cumple": cdt_tri <= 1  # REBT: 1% DI/LGA
        },
        "seccion": seccion,
        "longitud": longitud,
        "potencia": potencia,
        "material": material
    }


# ============================================================
# 3. CALCULADORA DE PROTECCIÓN (SOBRECARGA Y CORTOCIRCUITO)
# ============================================================

def calcular_proteccion_completa(
    intensidad: float,
    seccion_cable: float,
    metodo: str = "B1",
    aislamiento: str = "2xPVC",
    tipo_curva: str = "C",
    corriente_cortocircuito: float = 0
) -> Dict:
    """
    Calcula la protección necesaria según tipo de curva (B, C, D)
    Verifica coordinación con el cable
    """
    # PIA según curva
    pia_base = calcular_pia(intensidad)
    
    # Ajustar según curva (valores aproximados para curvas B, C, D)
    # Curva B: 3-5 In, Curva C: 5-10 In, Curva D: 10-20 In
    multiplicadores = {"B": 4, "C": 7.5, "D": 15}
    inrush = intensidad * multiplicadores.get(tipo_curva, 7.5)
    
    # Verificar que el PIA coordina con la sección del cable
    tabla = IZ_TABLES.get(metodo, IZ_TABLES["B1"]).get(aislamiento, {})
    iz_cable = tabla.get(seccion_cable, 0)
    
    # PIA debe ser ≤ Iz del cable
    pia_recomendado = pia_base
    if pia_base > iz_cable and iz_cable > 0:
        # Buscar PIA más cercano que sea ≤ Iz
        pias_comerciales = [6, 10, 16, 20, 25, 32, 40, 50, 63]
        for p in pias_comerciales:
            if p <= iz_cable:
                pia_recomendado = p
    
    # Verificar cortocircuito
    cumple_cortocircuito = True
    if corriente_cortocircuito > 0:
        # El PIA debe poder cortar al menos la corriente de cortocircuito
        cumple_cortocircuito = corriente_cortocircuito <= (pia_recomendado * 10)  # Aproximado
    
    return {
        "intensidad": round(intensidad, 2),
        "pia_recomendado": pia_recomendado,
        "curva": tipo_curva,
        "inrush": round(inrush, 2),
        "iz_cable": iz_cable,
        "seccion_cable": seccion_cable,
        "cumple_coordinacion": pia_recomendado <= iz_cable if iz_cable > 0 else False,
        "corriente_cortocircuito": corriente_cortocircuito,
        "cumple_cortocircuito": cumple_cortocircuito
    }


def calcular_cortocircuito_simplificado(
    potencia_cortocircuito_mva: float,
    tension: float = VOLTAJE_LINEA,
    impedancia_red: float = 0.1
) -> float:
    """
    Calcula corriente de cortocircuito simplificada
    Icc = (Scc × 1000) / (√3 × U)
    """
    scc_va = potencia_cortocircuito_mva * 1_000_000
    icc = scc_va / (math.sqrt(3) * tension)
    return round(icc, 2)


# ============================================================
# 4. CALCULADORA DE PANELES SOLARES
# ============================================================

def calcular_paneles_solares(
    consumo_diario_kwh: float,
    irradiacion_kwh_m2_dia: float = 4.5,  # Promedio España
    perdidas_sistema: float = 0.25,  # 25% pérdidas
    capacidad_bateria_horas: float = 24,  # Autonomía en horas
    tension_sistema: float = 24,  # V
    eficiencia_inversor: float = 0.93
) -> Dict:
    """
    Calcula dimensionado de sistema solar fotovoltaico
    """
    # 1. Energía necesaria considerando pérdidas
    energia_necesaria = consumo_diario_kwh / (1 - perdidas_sistema)
    
    # 2. Potencia pico necesaria
    potencia_pico = energia_necesaria / irradiacion_kwh_m2_dia
    
    # 3. Número de paneles (asumiendo panel 400W)
    potencia_panel_w = 400
    num_paneles = math.ceil((potencia_pico * 1000) / potencia_panel_w)
    potencia_total_paneles = num_paneles * potencia_panel_w / 1000  # kW
    
    # 4. Dimensionado del regulador/inversor
    corriente_regulador = (potencia_pico * 1000) / tension_sistema
    
    # 5. Baterías (capacidad en Ah)
    energia_bateria_kwh = consumo_diario_kwh * (capacidad_bateria_horas / 24)
    capacidad_ah = (energia_bateria_kwh * 1000) / tension_sistema
    
    # 6. Autonomía real
    energia_almacenada_kwh = (capacidad_ah * tension_sistema) / 1000
    autonomia_real_horas = (energia_almacenada_kwh / consumo_diario_kwh) * 24
    
    # 7. Inversor
    potencia_maxima_carga = consumo_diario_kwh * 1000 / 24  # Potencia media diaria
    potencia_inversor = math.ceil(potencia_maxima_carga / 1000) * 1000  # Redondear a próximo 1000W
    
    # Verificar eficiencia
    potencia_inversor_real = potencia_inversor * eficiencia_inversor
    
    return {
        "consumo_diario_kwh": consumo_diario_kwh,
        "energia_necesaria_kwh": round(energia_necesaria, 2),
        "irradiacion_kwh_m2_dia": irradiacion_kwh_m2_dia,
        "potencia_pico_kw": round(potencia_pico, 2),
        "num_paneles": num_paneles,
        "potencia_total_paneles_kw": round(potencia_total_paneles, 2),
        "tension_sistema_v": tension_sistema,
        "corriente_regulador_a": round(corriente_regulador, 2),
        "capacidad_bateria_kwh": round(energia_bateria_kwh, 2),
        "capacidad_bateria_ah": round(capacidad_ah, 2),
        "autonomia_horas": round(autonomia_real_horas, 1),
        "potencia_inversor_w": potencia_inversor,
        "potencia_inversor_real_w": round(potencia_inversor_real, 2),
        "perdidas_sistema": perdidas_sistema * 100
    }


def calcular_baterias_ah(
    consumo_diario_kwh: float,
    tension_sistema: float = 24,
    dias_autonomia: float = 1,
    profundidad_descarga: float = 0.5
) -> Dict:
    """
    Calcula la capacidad de baterías en Ah
    """
    energia_diaria = consumo_diario_kwh * 1000  # Wh
    energia_requerida = energia_diaria * dias_autonomia / profundidad_descarga
    capacidad_ah = energia_requerida / tension_sistema
    
    # Baterías en serie/paralelo (asumiendo baterías 100Ah)
    capacidad_bateria_individual = 100
    num_baterias_ah = math.ceil(capacidad_ah / capacidad_bateria_individual)
    
    # Configuración serie-paralelo
    num_serie = tension_sistema // 12  # Baterías de 12V
    num_paralelo = math.ceil(num_baterias_ah / num_serie)
    total_baterias = num_serie * num_paralelo
    
    return {
        "energia_diaria_wh": energia_diaria,
        "capacidad_requerida_ah": round(capacidad_ah, 2),
        "profundidad_descarga": profundidad_descarga * 100,
        "dias_autonomia": dias_autonomia,
        "tension_sistema_v": tension_sistema,
        "num_baterias_total": total_baterias,
        "configuracion": f"{num_paralelo}S{num_serie}P",
        "capacidad_instalada_ah": round(num_paralelo * capacidad_bateria_individual, 2)
    }


# ============================================================
# 5. CALCULADORA DIVISOR DE TENSIÓN (CON Y SIN CARGA)
# ============================================================

def calcular_divisor_tension(
    v_in: float,
    r1: float,
    r2: float,
    r_load: float = 0
) -> Dict:
    """
    Calcula divisor de tensión con y sin carga
    V_out = V_in * (R2 / (R1 + R2)) sin carga
    Con carga: Resistencia paralelo R2 || R_load
    """
    # Sin carga
    v_out_sin_carga = v_in * (r2 / (r1 + r2))
    
    resultado = {
        "v_in": v_in,
        "r1": r1,
        "r2": r2,
        "v_out_sin_carga": round(v_out_sin_carga, 2),
        "corriente_sin_carga": round(v_in / (r1 + r2), 4)
    }
    
    # Con carga
    if r_load > 0:
        r2_paralelo = (r2 * r_load) / (r2 + r_load)
        v_out_con_carga = v_in * (r2_paralelo / (r1 + r2_paralelo))
        corriente_carga = v_out_con_carga / r_load
        corriente_total = v_in / (r1 + r2_paralelo)
        
        resultado.update({
            "r_load": r_load,
            "r2_paralelo": round(r2_paralelo, 2),
            "v_out_con_carga": round(v_out_con_carga, 2),
            "corriente_carga": round(corriente_carga, 4),
            "corriente_total": round(corriente_total, 4),
            "potencia_r1": round((corriente_total**2) * r1, 3),
            "potencia_r2": round(((corriente_total - corriente_carga)**2) * r2, 3)
        })
    
    return resultado


# ============================================================
# 6. CALCULADORA FACTOR DE POTENCIA
# ============================================================

def calcular_factor_potencia(
    p_activa: float,
    s_aparente: float = 0,
    q_reactiva: float = 0,
    v_nominal: float = VOLTAJE_FASE
) -> Dict:
    """
    Calcula factor de potencia y corrección
    cos φ = P / S, S = √(P² + Q²)
    """
    if s_aparente == 0 and q_reactiva > 0:
        s_aparente = math.sqrt(p_activa**2 + q_reactiva**2)
    
    if s_aparente <= 0:
        return {"error": "Potencia aparente debe ser > 0"}
    
    cos_phi = p_activa / s_aparente
    q_actual = math.sqrt(s_aparente**2 - p_activa**2) if s_aparente > p_activa else 0
    
    # Corriente actual
    i_actual = s_aparente / v_nominal
    
    resultado = {
        "p_activa_w": p_activa,
        "s_aparente_va": round(s_aparente, 2),
        "q_reactiva_var": round(q_actual, 2),
        "cos_phi": round(cos_phi, 3),
        "corriente_actual_a": round(i_actual, 2)
    }
    
    # Capacitor para corrección a cos_phi = 1
    if cos_phi < 1:
        q_capacitor = q_actual
        c_uf = (q_capacitor * 1_000_000) / (2 * math.pi * 50 * v_nominal**2)
        
        resultado.update({
            "q_capacitor_var": round(q_capacitor, 2),
            "c_correccion_uf": round(c_uf, 2),
            "s_nueva_va": p_activa,
            "cos_phi_nuevo": 1.0,
            "ahorro_corriente_pct": round((1 - p_activa/s_aparente) * 100, 1)
        })
    
    return resultado


# ============================================================
# 7. CALCULADORA RESISTENCIAS EN PARALELO
# ============================================================

def calcular_resistencias_paralelo(resistencias: list) -> Dict:
    """
    Calcula resistencia equivalente en paralelo
    1/Req = 1/R1 + 1/R2 + ... + 1/Rn
    """
    if not resistencias or len(resistencias) < 2:
        return {"error": "Se necesitan al menos 2 resistencias"}
    
    # Resistencia equivalente
    inv_req = sum(1/r for r in resistencias if r > 0)
    if inv_req == 0:
        return {"error": "Resistencia equivalente infinita"}
    
    req = 1 / inv_req
    
    # Potencia disipada si hay voltaje
    resultado = {
        "resistencias": resistencias,
        "resistencia_equivalente": round(req, 2),
        "n_resistencias": len(resistencias)
    }
    
    return resultado


def calcular_resistencias_paralelo_voltaje(resistencias: list, voltaje: float) -> Dict:
    """Calcula con voltaje aplicado"""
    resultado = calcular_resistencias_paralelo(resistencias)
    
    if "error" not in resultado:
        req = resultado["resistencia_equivalente"]
        corriente_total = voltaje / req
        potencia_total = voltaje**2 / req
        
        corrientes = [voltaje / r for r in resistencias]
        potencias = [voltaje**2 / r for r in resistencias]
        
        resultado.update({
            "voltaje": voltaje,
            "corriente_total": round(corriente_total, 4),
            "potencia_total": round(potencia_total, 2),
            "corrientes": [round(i, 4) for i in corrientes],
            "potencias": [round(p, 2) for p in potencias]
        })
    
    return resultado


# ============================================================
# 8. CALCULADORA CONSUMO ELÉCTRICO (kWh A COSTO)
# ============================================================

def calcular_costo_consumo(
    consumo_kwh: float,
    precio_kwh: float = 0.15,
    potencia_contratada_kw: float = 3.45,
    precio_potencia_euros_dia: float = 0.12
) -> Dict:
    """
    Calcula costo de consumo eléctrico
    """
    # Costo por energía
    costo_energia = consumo_kwh * precio_kwh
    
    # Costo por potencia (mensual)
    costo_potencia_mes = potencia_contratada_kw * precio_potencia_euros_dia * 30
    
    # Impuestos (IVA 21% en España)
    subtotal = costo_energia + costo_potencia_mes
    iva = subtotal * 0.21
    total = subtotal + iva
    
    return {
        "consumo_kwh": consumo_kwh,
        "precio_kwh": precio_kwh,
        "costo_energia": round(costo_energia, 2),
        "potencia_contratada_kw": potencia_contratada_kw,
        "costo_potencia_mes": round(costo_potencia_mes, 2),
        "subtotal": round(subtotal, 2),
        "iva_pct": 21,
        "iva": round(iva, 2),
        "total_mensual": round(total, 2),
        "costo_por_dia": round(total / 30, 2)
    }


# ============================================================
# 9. CALCULADORA CORTOCIRCUITO POR IMPEDANCIAS
# ============================================================

def calcular_cortocircuito_impedancias(
    tension: float,
    z_linea: float = 0,
    z_transformador: float = 0,
    z_red: float = 0,
    es_trifasica: bool = True
) -> Dict:
    """
    Calcula cortocircuito con datos de impedancia
    Icc = U / (√3 × Z) para trifásica
    Icc = U / Z para monofásica
    """
    z_total = z_red + z_transformador + z_linea
    
    if z_total == 0:
        return {"error": "Impedancia total debe ser > 0"}
    
    if es_trifasica:
        icc = tension / (math.sqrt(3) * z_total)
    else:
        icc = tension / z_total
    
    # Potencia de cortocircuito
    if es_trifasica:
        scc = math.sqrt(3) * tension * icc / 1_000_000  # MVA
    else:
        scc = tension * icc / 1_000_000  # MVA
    
    return {
        "tension_v": tension,
        "z_red": z_red,
        "z_transformador": z_transformador,
        "z_linea": z_linea,
        "z_total": round(z_total, 4),
        "icc_a": round(icc, 2),
        "scc_mva": round(scc, 2),
        "es_trifasica": es_trifasica
    }


# ============================================================
# 10. CALCULADORA ELECTRODOS DE TIERRA
# ============================================================

def calcular_electrodos_tierra(
    resistividad: float = 100,  # Ω·m
    tipo_electrodo: str = "pica",
    longitud_pica: float = 1.5,  # m
    n_picass: int = 1,
    separacion_picass: float = 3.0,  # m
    tipo_suelo: str = "medio"
) -> Dict:
    """
    Calcula resistencia de puesta a tierra según ITC-BT-18
    """
    # Resistividad según tipo de suelo
    resistividades = {
        "seco": resistividad * 2,
        "medio": resistividad,
        "humedo": resistividad * 0.5
    }
    rho = resistividades.get(tipo_suelo, resistividad)
    
    if tipo_electrodo == "pica":
        # Fórmula pica: R = ρ / (2πL) * ln(4L/d)
        # Asumimos diámetro típico 14mm
        d = 0.014
        if n_picass == 1:
            r_una = (rho / (2 * math.pi * longitud_pica)) * math.log((4 * longitud_pica) / d)
        else:
            # Picas en paralelo con factor de corrección por separación
            r_una = (rho / (2 * math.pi * longitud_pica)) * math.log((4 * longitud_pica) / d)
            factor_mutua = 1 + (0.5 / (separacion_picass / longitud_pica))
            r_una = r_una * factor_mutua
            r_total = r_una / n_picass
    else:
        return {"error": "Tipo de electrodo no implementado"}
    
    r_total = r_una if n_picass == 1 else r_una / n_picass
    
    # Verificar si cumple REBT (< 30Ω para viviendas)
    cumple_rebt = r_total <= 30
    
    return {
        "tipo_electrodo": tipo_electrodo,
        "resistividad_omega_m": rho,
        "longitud_pica_m": longitud_pica,
        "n_picass": n_picass,
        "separacion_m": separacion_picass,
        "resistencia_una_pica": round(r_una, 2) if n_picass > 1 else round(r_total, 2),
        "resistencia_total": round(r_total, 2),
        "cumple_rebt": cumple_rebt,
        "limite_rebt": 30
    }


# ============================================================
# 11. CALCULADORA LONGITUD MÁXIMA DE CABLE
# ============================================================

def calcular_longitud_maxima_cable(
    potencia: float,
    seccion: float,
    cdt_max: float = 3,  # %
    tension: float = VOLTAJE_FASE,
    fp: float = COS_PHI_DEFAULT,
    material: str = "cobre"
) -> Dict:
    """
    Calcula la longitud máxima de un cable para una caída de tensión dada
    L_max = (U × ΔU × S × cosφ) / (2 × ρ × P) para monofásica
    """
    rho = RESISTIVIDAD.get(material, 0.018)
    delta_u = (cdt_max / 100) * tension
    
    # Longitud máxima
    if material == "cobre":
        l_max = (tension * delta_u * seccion * fp) / (2 * rho * potencia)
    else:
        l_max = (tension * delta_u * seccion * fp) / (2 * 0.028 * potencia)
    
    return {
        "potencia_w": potencia,
        "seccion_mm2": seccion,
        "cdt_max": cdt_max,
        "tension_v": tension,
        "fp": fp,
        "material": material,
        "longitud_maxima_m": round(l_max, 2),
        "cdt_por_metro": round(cdt_max / l_max, 4) if l_max > 0 else 0
    }


# ============================================================
# 12. CALCULADORA PICAS DE TIERRA (JABALINAS)
# ============================================================

def calcular_numero_picas(
    resistencia_objetivo: float = 30,  # Ω (REBT máximo viviendas)
    resistividad: float = 100,  # Ω·m
    longitud_pica: float = 1.5,  # m
    separacion: float = 3.0  # m
) -> Dict:
    """
    Calcula cuántas picas (jabalinas) se necesitan para una resistencia objetivo
    """
    # Resistencia de una pica
    d = 0.014  # diámetro 14mm
    r_una = (resistividad / (2 * math.pi * longitud_pica)) * math.log((4 * longitud_pica) / d)
    
    # Número teórico sin factor de mutua
    n_teorico = r_una / resistencia_objetivo
    
    # Ajuste por factor de mutua (picas separadas 2-3 veces su longitud)
    factor_mutua = 1 + (0.5 / (separacion / longitud_pica))
    n_real = n_teorico * factor_mutua
    
    n_picas = math.ceil(n_real)
    
    # Resistencia final con n_picas
    r_final = r_una / (n_picas / factor_mutua)
    
    return {
        "resistencia_objetivo": resistencia_objetivo,
        "resistividad": resistividad,
        "longitud_pica": longitud_pica,
        "separacion": separacion,
        "resistencia_una_pica": round(r_una, 2),
        "n_picas_teorico": round(n_teorico, 2),
        "n_picas_recomendado": n_picas,
        "resistencia_final": round(r_final, 2),
        "cumple_rebt": r_final <= 30
    }


# ============================================================
# 13. CALCULADORA POTENCIA ELÉCTRICA (MONO/TRIFÁSICA)
# ============================================================

def calcular_potencia_electrica(
    tension: float,
    corriente: float,
    fp: float = COS_PHI_DEFAULT,
    es_trifasica: bool = False
) -> Dict:
    """
    Calcula potencias P, Q, S
    Monofásica: P = U × I × cosφ
    Trifásica: P = √3 × U × I × cosφ
    """
    if es_trifasica:
        p = math.sqrt(3) * tension * corriente * fp
        s = math.sqrt(3) * tension * corriente
    else:
        p = tension * corriente * fp
        s = tension * corriente
    
    q = math.sqrt(s**2 - p**2) if s > p else 0
    
    return {
        "tension_v": tension,
        "corriente_a": corriente,
        "fp": fp,
        "p_activa_w": round(p, 2),
        "p_activa_kw": round(p / 1000, 2),
        "s_aparente_va": round(s, 2),
        "s_aparente_kva": round(s / 1000, 2),
        "q_reactiva_var": round(q, 2),
        "es_trifasica": es_trifasica
    }


# ============================================================
# 14. CALCULADORA RESISTENCIA DE CONDUCTOR
# ============================================================

def calcular_resistencia_conductor(
    longitud: float,
    seccion: float,
    material: str = "cobre",
    temperatura: float = 20
) -> Dict:
    """
    Calcula resistencia de un conductor
    R = ρ × L / S
    Con corrección por temperatura: Rt = R20 × [1 + α × (t - 20)]
    """
    rho_20 = RESISTIVIDAD.get(material, 0.018)
    
    # Coeficiente de temperatura
    alpha = 0.00393 if material == "cobre" else 0.00403
    
    # Resistencia a 20°C
    r_20 = (rho_20 * longitud) / seccion
    
    # Resistencia a la temperatura dada
    r_t = r_20 * (1 + alpha * (temperatura - 20))
    
    # Caída de tensión a diferentes corrientes
    corrientes_prueba = [1, 5, 10, 16, 20, 25]
    caidas = {}
    for i in corrientes_prueba:
        caidas[f"{i}A"] = round(i * r_t, 3)
    
    return {
        "longitud_m": longitud,
        "seccion_mm2": seccion,
        "material": material,
        "temperatura_c": temperatura,
        "resistividad_20": rho_20,
        "resistencia_20_ohm": round(r_20, 4),
        "resistencia_t_ohm": round(r_t, 4),
        "caidas_tension": caidas
    }


# ============================================================
# 15. CALCULADORA SECCIÓN POR POTENCIA Y DISTANCIA
# ============================================================

def calcular_seccion_potencia_distancia(
    potencia: float,
    distancia: float,
    tension: float = VOLTAJE_FASE,
    cdt_max: float = 3
) -> Dict:
    """
    Calcula sección mínima basada en potencia y distancia
    Considera caída de tensión y intensidad
    """
    # Intensidad
    intensidad = calcular_intensidad(potencia, tension)
    
    # Sección por intensidad (tabla ITC-BT-19)
    seccion_iz, iz = calcular_seccion_por_intensidad(intensidad)
    
    # Sección por caída de tensión
    seccion_cdt = calcular_seccion_cdt(potencia, distancia, cdt_max, tension)
    
    # Sección final
    seccion_final = normalizar_seccion(max(seccion_iz, seccion_cdt))
    
    return {
        "potencia_w": potencia,
        "distancia_m": distancia,
        "tension_v": tension,
        "intensidad_a": round(intensidad, 2),
        "seccion_iz": seccion_iz,
        "iz_admisible": iz,
        "seccion_cdt": round(seccion_cdt, 2),
        "seccion_final": seccion_final,
        "cdt_max": cdt_max
    }


# ============================================================
# 16. CALCULADORA SECCIÓN POR CAÍDA DE TENSIÓN Y DISTANCIA
# ============================================================

def calcular_seccion_caida_distancia(
    potencia: float,
    distancia: float,
    cdt_max: float = 3,
    tension: float = VOLTAJE_FASE,
    material: str = "cobre"
) -> Dict:
    """
    Calcula sección necesaria solo por criterio de caída de tensión
    """
    seccion = calcular_seccion_cdt(potencia, distancia, cdt_max, tension, COS_PHI_DEFAULT, material)
    seccion_final = normalizar_seccion(seccion)
    
    # Verificar caída real
    cdt_real = calcular_caida_tension_real(potencia, distancia, seccion_final, tension)
    
    return {
        "potencia_w": potencia,
        "distancia_m": distancia,
        "cdt_max": cdt_max,
        "tension_v": tension,
        "seccion_calculada": round(seccion, 2),
        "seccion_normalizada": seccion_final,
        "cdt_real": round(cdt_real, 2),
        "cumple": cdt_real <= cdt_max
    }


# ============================================================
# 17. CALCULADORA LEY DE OHM Y POTENCIA
# ============================================================

def calcular_ley_ohm(
    voltaje: float = 0,
    corriente: float = 0,
    resistencia: float = 0,
    potencia: float = 0
) -> Dict:
    """
    Calculadora completa Ley de Ohm y Potencia
    V = I × R
    P = V × I = I² × R = V² / R
    """
    # Determinar qué valor falta y calcularlo
    valores = {"v": voltaje, "i": corriente, "r": resistencia, "p": potencia}
    no_cero = [k for k, v in valores.items() if v > 0]
    
    if len(no_cero) < 2:
        return {"error": "Se necesitan al menos 2 valores"}
    
    # Calcular valores faltantes
    if voltaje > 0 and corriente > 0:
        resistencia = voltaje / corriente
        potencia = voltaje * corriente
    elif voltaje > 0 and resistencia > 0:
        corriente = voltaje / resistencia
        potencia = voltaje**2 / resistencia
    elif voltaje > 0 and potencia > 0:
        corriente = potencia / voltaje
        resistencia = voltaje / corriente
    elif corriente > 0 and resistencia > 0:
        voltaje = corriente * resistencia
        potencia = corriente**2 * resistencia
    elif corriente > 0 and potencia > 0:
        voltaje = potencia / corriente
        resistencia = voltaje / corriente
    elif resistencia > 0 and potencia > 0:
        voltaje = math.sqrt(potencia * resistencia)
        corriente = voltaje / resistencia
    
    return {
        "voltaje_v": round(voltaje, 2),
        "corriente_a": round(corriente, 4),
        "resistencia_ohm": round(resistencia, 2),
        "potencia_w": round(potencia, 2),
        "potencia_kw": round(potencia / 1000, 3)
    }


# ============================================================
# 18. CÓDIGO DE COLORES DE RESISTENCIAS
# ============================================================

def calcular_codigo_colores_resistencia(
    valor_ohm: float = 0,
    tolerancia: str = "oro"  # oro = 5%, plata = 10%
) -> Dict:
    """
    Calcula código de colores para resistencias de 4 y 5 bandas
    """
    # Colores y valores
    colores = {
        "negro": 0, "marron": 1, "rojo": 2, "naranja": 3, "amarillo": 4,
        "verde": 5, "azul": 6, "violeta": 7, "gris": 8, "blanco": 9,
        "oro": -1, "plata": -2
    }
    
    tolerancias = {
        "oro": 5, "plata": 10, "marron": 1, "rojo": 2, "verde": 0.5,
        "azul": 0.25, "violeta": 0.1, "gris": 0.05
    }
    
    if valor_ohm <= 0:
        return {"error": "Valor debe ser > 0"}
    
    # Determinar multiplicador para 2 dígitos significativos
    valor_str = str(int(valor_ohm))
    
    if len(valor_str) >= 2:
        # 4 bandas: 2 dígitos + multiplicador
        d1 = int(valor_str[0])
        d2 = int(valor_str[1]) if len(valor_str) > 1 else 0
        multiplicador = len(valor_str) - 2
        
        # Colores 4 bandas
        colores_4 = []
        for valor, nombre in colores.items():
            if nombre == d1:
                colores_4.append(valor)
                break
        for valor, nombre in colores.items():
            if nombre == d2:
                colores_4.append(valor)
                break
        # Multiplicador
        for valor, nombre in colores.items():
            if nombre == multiplicador:
                colores_4.append(valor)
                break
        # Tolerancia
        colores_4.append(tolerancia)
        
        # 5 bandas: 3 dígitos + multiplicador
        d3 = int(valor_str[2]) if len(valor_str) > 2 else 0
        multiplicador_5 = len(valor_str) - 3
        
        colores_5 = []
        for valor, nombre in colores.items():
            if nombre == d1:
                colores_5.append(valor)
                break
        for valor, nombre in colores.items():
            if nombre == d2:
                colores_5.append(valor)
                break
        for valor, nombre in colores.items():
            if nombre == d3:
                colores_5.append(valor)
                break
        for valor, nombre in colores.items():
            if nombre == multiplicador_5:
                colores_5.append(valor)
                break
        colores_5.append(tolerancia)
        
        return {
            "valor_ohm": valor_ohm,
            "valor_kohm": round(valor_ohm / 1000, 2),
            "tolerancia_pct": tolerancias.get(tolerancia, 5),
            "colores_4_bandas": colores_4,
            "colores_5_bandas": colores_5
        }
    
    return {"error": "Valor muy pequeño para código de colores"}
