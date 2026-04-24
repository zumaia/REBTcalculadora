def calcular_seccion_di(potencia, longitud, tension=230):
    """Calcula la sección por caída de tensión al 1% (ITC-BT-15)"""
    gamma = 56  # Conductividad del cobre
    e_adm = tension * 0.01  # 1% de caída admisible
    
    # Fórmula: S = (2 * L * P) / (gamma * e * V)
    seccion = (2 * longitud * potencia) / (gamma * e_adm * tension)
    
    # Secciones comerciales estándar
    secciones_estandar = [1.5, 2.5, 4, 6, 10, 16, 25, 35]
    for s in secciones_estandar:
        if s >= seccion:
            return s
    return "Sección superior a 35mm² (consultar tablas)"

# Prueba para un cargador de 7.4kW a 30 metros
p = 7400
l = 30
print(f"Para {p}W a {l}m, necesitas una sección de: {calcular_seccion_di(p, l)} mm²")