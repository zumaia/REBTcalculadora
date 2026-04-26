"""
Generador de Diagramas Unifilares Estilo Profesional
Similar a los ejemplos de ejercicios
"""

from typing import List, Dict
from src.engine_rebt import ResultadoCircuito


def generar_svg_profesional(datos: Dict, width: int = 900, tipo: str = "vivienda") -> str:
    """Genera diagrama unifilar estilo profesional"""
    
    circuitos = datos.get('circuitos', [])
    di = datos.get('derivacion_individual')
    iga = datos.get('iga', 40)
    electrificacion = datos.get('electrificacion', 'básica').upper()
    
    n_circs = len(circuitos)
    height = 280 + n_circs * 35
    
    # Colores estilo profesional
    bg = "#003366"  # Azul oscuro
    box_fill = "#004080"  # Azul medio
    box_stroke = "#ffffff"
    line_color = "#ffffff"
    text_color = "#ffffff"
    itc_color = "#87CEEB"  # Azul claro
    
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <!-- Fondo -->
  <rect width="{width}" height="{height}" fill="{bg}"/>
  
  <!-- Título -->
  <text x="50" y="30" fill="{text_color}" font-size="16" font-weight="bold">ESQUEMA UNIFILAR</text>
  <text x="300" y="30" fill="{itc_color}" font-size="14">{tipo.upper()}</text>
  <text x="420" y="30" fill="{itc_color}" font-size="14">Grado Electrificación: {electrificacion}</text>
  <line x1="50" y1="40" x2="{width-50}" y2="40" stroke="{line_color}" stroke-width="1"/>
  
  <!-- CGP -->
  <rect x="60" y="60" width="100" height="50" fill="{box_fill}" stroke="{box_stroke}" stroke-width="2" rx="2"/>
  <text x="110" y="80" text-anchor="middle" fill="{text_color}" font-size="14" font-weight="bold">CGP</text>
  <text x="110" y="100" text-anchor="middle" fill="{itc_color}" font-size="11">ITC-BT-12</text>
  
  <!-- Flecha CGP -->
  <polygon points="160,75 175,85 160,95" fill="{line_color}"/>
  <line x1="160" y1="85" x2="175" y2="85" stroke="{line_color}" stroke-width="2"/>
  
  <!-- ICP -->
  <rect x="180" y="60" width="80" height="50" fill="{box_fill}" stroke="{box_stroke}" stroke-width="2" rx="2"/>
  <text x="220" y="80" text-anchor="middle" fill="{text_color}" font-size="14" font-weight="bold">ICP</text>
  <text x="220" y="100" text-anchor="middle" fill="{itc_color}" font-size="11">ITC-BT-13</text>
  
  <!-- Flecha ICP -->
  <polygon points="260,75 275,85 260,95" fill="{line_color}"/>
  <line x1="260" y1="85" x2="275" y2="85" stroke="{line_color}" stroke-width="2"/>
  
  <!-- IGA -->
  <rect x="280" y="60" width="80" height="50" fill="{box_fill}" stroke="{box_stroke}" stroke-width="2" rx="2"/>
  <text x="320" y="80" text-anchor="middle" fill="{text_color}" font-size="14" font-weight="bold">IGA</text>
  <text x="320" y="100" text-anchor="middle" fill="{itc_color}" font-size="11">{iga}A</text>
  
  <!-- Flecha IGA -->
  <polygon points="360,75 375,85 360,95" fill="{line_color}"/>
  <line x1="360" y1="85" x2="375" y2="85" stroke="{line_color}" stroke-width="2"/>
  
  <!-- Diferencial -->
  <rect x="380" y="60" width="100" height="50" fill="{box_fill}" stroke="{box_stroke}" stroke-width="2" rx="2"/>
  <text x="430" y="80" text-anchor="middle" fill="{text_color}" font-size="14" font-weight="bold">ID</text>
  <text x="430" y="100" text-anchor="middle" fill="{itc_color}" font-size="11">30mA</text>
  
  <!-- Cuadro de distribución -->
  <rect x="500" y="55" width="{80 + n_circs * 50}" height="{n_circs * 32 + 30}" fill="{box_fill}" stroke="{box_stroke}" stroke-width="2" rx="2"/>
  <text x="{540 + n_circs * 25}" y="75" text-anchor="middle" fill="{text_color}" font-size="10" font-weight="bold">CUADRO</text>
  <line x1="510" y1="80" x2="{570 + n_circs * 50}" y2="80" stroke="{box_stroke}" stroke-width="1"/>
'''
    
    # Circuitos
    y = 90
    for circ in circuitos:
        code = getattr(circ, 'codigo', 'C1')
        name = getattr(circ, 'nombre', 'Circuito')[:12]
        seccion = getattr(circ, 'seccion', 1.5)
        pia = getattr(circ, 'pia', 10)
        
        # PIA individual
        px = 515 + (y - 90) // 35 * 50
        svg += f'''
  <rect x="{px}" y="{y}" width="45" height="22" fill="{box_fill}" stroke="{box_stroke}" stroke-width="1" rx="1"/>
  <text x="{px+22}" y="{y+15}" text-anchor="middle" fill="{text_color}" font-size="9">{code}</text>
  <text x="{px+48}" y="{y+15}" text-anchor="end" fill="{itc_color}" font-size="8">{pia}A</text>
'''
        y += 32
    
    # Derivación Individual
    if di:
        di_seccion = di.seccion
        di_tubo = di.tubo
        di_pot = di.potencia
        
        svg += f'''
  <!-- Derivación Individual -->
  <polygon points="110,130 160,145 110,160" fill="{line_color}"/>
  <text x="110" y="175" text-anchor="middle" fill="{text_color}" font-size="10" font-weight="bold">D.I.</text>
  <text x="110" y="188" text-anchor="middle" fill="{itc_color}" font-size="9">{di_seccion}mm²</text>
  <text x="110" y="200" text-anchor="middle" fill="{itc_color}" font-size="8">Ø{di_tubo}</text>
  <text x="110" y="212" text-anchor="middle" fill="{itc_color}" font-size="8">{di_pot}W</text>
  <line x1="160" y1="145" x2="180" y2="145" stroke="{line_color}" stroke-width="2"/>
'''
    
    # Leyenda ITC
    svg += f'''
  <!-- Leyenda -->
  <text x="50" y="{height-40}" fill="{itc_color}" font-size="10">ITC-BT-12: CGP</text>
  <text x="150" y="{height-40}" fill="{itc_color}" font-size="10">ITC-BT-13: ICP</text>
  <text x="250" y="{height-40}" fill="{itc_color}" font-size="10">ITC-BT-14: IGA</text>
  <text x="380" y="{height-40}" fill="{itc_color}" font-size="10">ITC-BT-17: ID</text>
  <text x="500" y="{height-40}" fill="{itc_color}" font-size="10">ITC-BT-25: Circuitos</text>
  
  <!-- Tabla-circuitos -->
  <text x="600" y="{height-70}" fill="{text_color}" font-size="11" font-weight="bold">CIRCUITOS</text>
  <line x1="600" y1="{height-65}" x2="750" y2="{height-65}" stroke="{box_stroke}"/>
'''
    
    y_tabla = height - 55
    for circ in circuitos[:5]:
        code = getattr(circ, 'codigo', 'C')
        name = getattr(circ, 'nombre', '')[:10]
        seccion = getattr(circ, 'seccion', 1.5)
        pia = getattr(circ, 'pia', 10)
        
        svg += f'''
  <text x="600" y="{y_tabla}" fill="{text_color}" font-size="9">{code}</text>
  <text x="630" y="{y_tabla}" fill="{itc_color}" font-size="9">{name}</text>
  <text x="700" y="{y_tabla}" fill="{itc_color}" font-size="9">{seccion}mm²</text>
  <text x="750" y="{y_tabla}" fill="{itc_color}" font-size="9">{pia}A</text>
'''
        y_tabla += 12
    
    svg += '\n</svg>'
    return svg


def svg_a_bytes(svg: str) -> bytes:
    return svg.encode('utf-8')


if __name__ == "__main__":
    from engine_rebt import calcular_circuitos_vivienda
    
    datos = calcular_circuitos_vivienda(15, 15)
    svg = generar_svg_profesional(datos, tipo="EB")
    
    with open('diagrama_profesional.svg', 'w') as f:
        f.write(svg)
    print("✅ Generado: diagrama_profesional.svg")