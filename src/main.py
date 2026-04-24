#!/usr/bin/env python3
"""
Calculadora genérica de instalaciones eléctricas según REBT
ITC-BT: 12, 13, 14, 15, 19, 25, 28, 44, 52
"""

import math
from typing import Dict, List, Tuple, Optional

VOLTAJE_FASE = 230
VOLTAJE_LINEA = 400
COS_PHI_DEFAULT = 0.8
FP_MIN = 0.8

IZ_TABLES = {
    "B1": {
        "2xPVC": {1.5: 14.5, 2.5: 18.5, 4: 24, 6: 31, 10: 42, 16: 56, 25: 73, 35: 89},
        "3xPVC": {1.5: 13, 2.5: 16.5, 4: 21, 6: 27, 10: 36, 16: 48, 25: 62, 35: 77},
        "2xXLPE": {1.5: 18, 2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 101, 35: 125},
    },
    "B2": {
        "2xPVC": {1.5: 13, 2.5: 17.5, 4: 22, 6: 28, 10: 38, 16: 52, 25: 68, 35: 84},
        "3xPVC": {1.5: 11.5, 2.5: 15, 4: 19, 6: 24, 10: 32, 16: 44, 25: 56, 35: 70},
    },
}

DT_MAX = {
    "vivienda": {"interior": 3, "di": 1},
    "concurrencia": {"interior": 5, "di": 1},
    "industrial": {"interior": 5, "di": 1},
    "comercio": {"interior": 5, "di": 1},
}

RESISTIVIDAD = {"cobre": 0.018, "aluminio": 0.028}


def calcular_intensidad(potencia: float, tension: float = VOLTAJE_FASE, fp: float = COS_PHI_DEFAULT) -> float:
    return potencia / (tension * fp)


def calcular_intensidad_trifasica(potencia: float, tension: float = VOLTAJE_LINEA, fp: float = COS_PHI_DEFAULT) -> float:
    return potencia / (tension * fp * math.sqrt(3))


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
    return 25, tabla.get(25, 73)


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


class CalculadoraREBT:
    def __init__(self):
        self.tipo_instalacion = "vivienda"
        self.metodo = "B1"
        self.aislamiento = "2xPVC"
    
    def set_tipo_instalacion(self, tipo: str):
        self.tipo_instalacion = tipo
    
    def calcular_circuito(self, potencia: float, longitud: float, fp: float = COS_PHI_DEFAULT,
                    es_trifasico: bool = False, tension: float = None) -> Dict:
        tension = tension or (VOLTAJE_LINEA if es_trifasico else VOLTAJE_FASE)
        
        if es_trifasico:
            intensidad = calcular_intensidad_trifasica(potencia, tension, fp)
        else:
            intensidad = calcular_intensidad(potencia, tension, fp)
        
        cdt_max = DT_MAX.get(self.tipo_instalacion, DT_MAX["vivienda"])["interior"]
        seccion_cdt = calcular_seccion_cdt(potencia, longitud, cdt_max, tension, fp)
        seccion, iz = calcular_seccion_por_intensidad(intensidad, self.metodo, self.aislamiento)
        
        seccion_final = normalizar_seccion(max(seccion, seccion_cdt, 1.5))
        pia = calcular_pia(intensidad)
        tubo = get_tubo_diametro(seccion_final)
        
        return {
            "potencia": potencia,
            "intensidad": round(intensidad, 2),
            "seccion_cdt": round(seccion_cdt, 2),
            "seccion_min": seccion,
            "seccion_final": seccion_final,
            "pia": pia,
            "tubo": tubo,
            "cdt_max": cdt_max
        }
    
    def calcular_di(self, potencia: float, longitud: float, es_trifasico: bool = False,
               tension: float = None) -> Dict:
        tension = tension or (VOLTAJE_LINEA if es_trifasico else VOLTAJE_FASE)
        
        if es_trifasico:
            intensidad = calcular_intensidad_trifasica(potencia, tension)
        else:
            intensidad = calcular_intensidad(potencia, tension)
        
        cdt_max = DT_MAX.get(self.tipo_instalacion, DT_MAX["vivienda"])["di"]
        seccion_cdt = calcular_seccion_cdt(potencia, longitud, cdt_max, tension)
        
        aislamiento = "3xPVC" if es_trifasico else "2xPVC"
        seccion, iz = calcular_seccion_por_intensidad(intensidad, self.metodo, aislamiento)
        
        seccion_final = normalizar_seccion(max(seccion, seccion_cdt, 6))
        
        n_conductores = 5 if es_trifasico else 3
        tubo = get_tubo_diametro(seccion_final, n_conductores)
        iga = calcular_pia(intensidad)
        
        return {
            "potencia": potencia,
            "intensidad": round(intensidad, 2),
            "seccion_cdt": round(seccion_cdt, 2),
            "seccion": seccion_final,
            "iga": iga,
            "tubo": tubo,
            "n_conductores": n_conductores,
            "cdt_max": cdt_max
        }


def menu_circuito():
    print("\n" + "="*60)
    print("CÁLCULO DE CIRCUITO")
    print("="*60)
    
    print("\nTipo de instalación:")
    print("  1 - Vivienda")
    print("  2 - Local de pública concurrencia")
    print("  3 - Comercio/Oficina")
    print("  4 - Industrial")
    
    op = input("Opción [1]: ").strip() or "1"
    tipos = {"1": "vivienda", "2": "concurrencia", "3": "comercio", "4": "industrial"}
    tipo = tipos.get(op, "vivienda")
    
    print("\nDatos del circuito:")
    pot = float(input("Potencia (W): ").strip())
    long = float(input("Longitud (m): ").strip())
    fp_input = input("Factor de potencia [0.8]: ").strip()
    fp = float(fp_input) if fp_input else 0.8
    
    es_tri = input("Es trifásico? (s/N): ").strip().lower() == 's'
    
    calc = CalculadoraREBT()
    calc.set_tipo_instalacion(tipo)
    
    resultado = calc.calcular_circuito(pot, long, fp, es_tri)
    
    print("\n" + "-"*50)
    print("RESULTADOS:")
    print("-"*50)
    print(f"Intensidad:        {resultado['intensidad']} A")
    print(f"Sección CDT:      {resultado['seccion_cdt']} mm²")
    print(f"Sección mínima:  {resultado['seccion_min']} mm²")
    print(f"Sección final:   {resultado['seccion_final']} mm²")
    print(f"PIA protección: {resultado['pia']} A")
    print(f"Diámetro tubo:  {resultado['tubo']} mm")
    print(f"C.D.T. máx:     {resultado['cdt_max']}%")


def menu_di():
    print("\n" + "="*60)
    print("CÁLCULO DE DERIVACIÓN INDIVIDUAL")
    print("="*60)
    
    print("\nTipo de instalación:")
    print("  1 - Vivienda")
    print("  2 - Local de pública concurrencia")
    print("  3 - Comercio/Oficina")
    print("  4 - Industrial")
    
    op = input("Opción [1]: ").strip() or "1"
    tipos = {"1": "vivienda", "2": "concurrencia", "3": "comercio", "4": "industrial"}
    tipo = tipos.get(op, "vivienda")
    
    print("\nDatos de la DI:")
    pot = float(input("Potencia (W): ").strip())
    long = float(input("Longitud (m): ").strip())
    es_tri = input("Es trifásico? (s/N): ").strip().lower() == 's'
    
    calc = CalculadoraREBT()
    calc.set_tipo_instalacion(tipo)
    
    resultado = calc.calcular_di(pot, long, es_tri)
    
    print("\n" + "-"*50)
    print("RESULTADOS:")
    print("-"*50)
    print(f"Intensidad:        {resultado['intensidad']} A")
    print(f"Sección CDT:      {resultado['seccion_cdt']} mm²")
    print(f"Sección final:    {resultado['seccion']} mm²")
    print(f"IGA:            {resultado['iga']} A")
    print(f"Diámetro tubo:   {resultado['tubo']} mm")
    print(f"C Conductores:    {resultado['n_conductores']}")
    print(f"C.D.T. máx:    {resultado['cdt_max']}%")


def menu_vivienda():
    print("\n" + "="*60)
    print("CIRCUITOS DE VIVIENDA (ITC-BT-25)")
    print("="*60)
    
    print("\nDatos de la vivienda:")
    puntos_luz = int(input("Número de puntos de luz: ").strip())
    Tomas = int(input("Número de tomas de corriente: ").strip())
    lavadora = input("Tiene lavadora? (s/N): ").strip().lower() == 's'
    cocina = input("Tiene cocina eléctrica? (s/N): ").strip().lower() == 's'
    aire = input("Tiene aire acondicionado? (s/N): ").strip().lower() == 's'
    
    circuitos = []
    
    circuitos.append({"nombre": "C1", "desc": "Iluminación", "potencia": puntos_luz * 100, "fp": 1.0})
    
    if Tomas <= 20:
        circuitos.append({"nombre": "C2", "desc": "Tomas generales", "potencia": 3450, "fp": 1.0})
    else:
        circuitos.append({"nombre": "C2", "desc": "Tomas principales", "potencia": 3450, "fp": 1.0})
        circuitos.append({"nombre": "C7", "desc": "Tomas adicionales", "potencia": 3450, "fp": 1.0})
    
    if lavadora:
        circuitos.append({"nombre": "C4", "desc": "Lavadora", "potencia": 2500, "fp": 0.9})
    
    if cocina:
        circuitos.append({"nombre": "C3", "desc": "Cocina eléctrica", "potencia": 5400, "fp": 0.9})
    
    circuitos.append({"nombre": "C5", "desc": "Baño/auxiliares", "potencia": 2500, "fp": 0.9})
    
    if aire:
        circuitos.append({"nombre": "C9", "desc": "Aire acondicionado", "potencia": 2500, "fp": 0.9})
    
    long_promedio = float(input("Longitud media al punto más lejano (m) [25]: ").strip() or "25")
    
    calc = CalculadoraREBT()
    calc.set_tipo_instalacion("vivienda")
    
    print("\n" + "-"*70)
    print(f"{'Circuito':<10} {'Descripción':<25} {'P(W)':<10} {'I(A)':<8} {'Sección':<10} {'PIA':<8}")
    print("-"*70)
    
    total_intensidad = 0
    for circ in circuitos:
        resultado = calc.calcular_circuito(circ["potencia"], long_promedio, circ["fp"])
        total_intensidad += resultado["intensidad"]
        print(f"{circ['nombre']:<10} {circ['desc']:<25} {circ['potencia']:<10} "
              f"{resultado['intensidad']:<8} {resultado['seccion_final']} mm²{'':<5} {resultado['pia']}A")
    
    iga = calcular_pia(total_intensidad * 0.8)
    long_di = float(input("\nLongitud de la DI (m) [15]: ").strip() or "15")
    pot_total = sum(c["potencia"] for c in circuitos) * 0.8
    resultado_di = calc.calcular_di(pot_total * 1.5, long_di)
    
    print(f"\nIGA: {iga}A")
    print(f"Derivación Individual: {resultado_di['seccion']} mm², Tubo: {resultado_di['tubo']}mm")


def menu_principal():
    print("\n" + "="*60)
    print("   CALCULADORA DE INSTALACIONES ELÉCTRICAS - REBT")
    print("   ITC-BT: 12, 13, 14, 15, 19, 25, 28, 44, 52")
    print("="*60)
    print("\nSelecciona tipo de cálculo:")
    print("  1 - Calcular un circuito")
    print("  2 - Calcular derivación individual")
    print("  3 - Circuitos de vivienda (ITC-BT-25)")
    print("  0 - Salir")
    print("-"*40)


def main():
    while True:
        menu_principal()
        opcion = input("\nOpción: ").strip()
        
        if opcion == "1":
            menu_circuito()
        elif opcion == "2":
            menu_di()
        elif opcion == "3":
            menu_vivienda()
        elif opcion == "0":
            print("\n¡Hasta luego!")
            break
        else:
            print("\nOpción no válida")
        
        input("\nPresiona Enter para continuar...")


if __name__ == "__main__":
    main()