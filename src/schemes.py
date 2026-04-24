"""
Generador de Esquemas Unifilares REBT
Utiliza schemdraw para generar esquemas técnicos
"""

import io
import base64
from typing import Dict, List
import math

# Tentative import - we'll handle if not available
SCHEMDRAW_AVAILABLE = False
try:
    import schemdraw
    import schemdraw.elements as elm
    SCHEMDRAW_AVAILABLE = True
except ImportError:
    pass


def generar_esquema_vivienda(datos: Dict) -> str:
    """Genera esquema unifilar para vivienda"""
    
    circuitos = datos.get('circuitos', [])
    iga = datos.get('iga', 40)
    di = datos.get('derivacion_individual')
    electrificacion = datos.get('electrificacion', 'básica')
    
    # Esquema ASCII
    esquema = f"""
╔════════════════════════════════════════════════════════════════════════╗
║              ESQUEMA UNIFILAR - VIVIENDA ({electrificacion.upper()})               ║
║                     ITC-BT-25                                    ║
╠════════════════════════════════════════════════════════════════════════╣
║                                                                 ║
║    ┌────────┐    ┌────────┐    ┌──────────┐    ┌─────────────────┐   ║
║    │  CGP   │───▶│  ICP   │───▶│   IGA    │───▶│   CUADRO DE     │   ║
║    │ 40A   │    │ 40A   │    │   {iga:>2}A   │    │   PROTECCIÓN    │   ║
║    └────────┘    └────────┘    └──────────┘    └─────────────────┘   ║
║        │                                            │                ║
║        │                ┌──────────────────────────────┴─────────┐   ║
║        │                │                                    │    ║
║        ▼                ▼                                    ▼    ║
"""
    
    # Circuitos del cuadro
    cols = 2
    for i, circ in enumerate(circuitos):
        if i % cols == 0:
            esquema += "║                  "
        esquema += f"│ [{circ.codigo}] {circ.nombre[:12]:12s} S={circ.seccion}mm² {circ.pia}A │"
        if i % cols == cols - 1 or i == len(circuitos) - 1:
            esquema += "   ║\n"
        else:
            esquema += "\n"
    
    if len(circuitos) % cols != 0:
        esquema += " " * 61 + "║\n"
    
    esquema += f"""║                  └──────────────────────────────────────────────────┘   ║
║                              │                              ║
║                              ▼                              ║
║    ┌─────────────────────────────────────────────────────────┐   ║
║    │              DERIVACIÓN INDIVIDUAL                     │   ║
║    │   S = {di.seccion if di else '?':>2}mm²  │  Tubo = {di.tubo if di else '?':>2}mm  │  IGA = {iga:>2}A   │   ║
║    └────────────────────────────��────────────────────────────┘   ║
╚════════════════════════════════════════════════════════════════════════╝
"""
    
    return esquema


def generar_esquema_edificio(datos: Dict) -> str:
    """Genera esquema unifilar para edificio"""
    
    num_viviendas = datos.get('num_viviendas', 0)
    lga = datos.get('lga')
    dis = datos.get('derivaciones_individuales', [])
    
    esquema = f"""
╔════════════════════════════════════════════════════════════════════════╗
║              ESQUEMA UNIFILAR - EDIFICIO                         ║
║                  UF0884 - Instalaciones de Enlace               ║
╠════════════════════════════════════════════════════════════════════════╣
║                                                                 ║
║         ┌──────────────────────────────────────────────────┐     ║
║         │         LÍNEA GENERAL DE ALIMENTACIÓN (LGA)      │     ║
║         │   S = {lga.seccion:>2}mm²  │  Tubo = {lga.tubo:>2}mm  │  F = {lga.fusible:>3}A   │     ║
║         └──────────────────────────┬───────────────────────┘     ║
║                                   │                             ║
║                    ┌──────────────┴──────────────┐                ║
║                    │          CGP                │                ║
║                    │      Fusible {lga.fusible:>3}A          │                ║
║                    └──────────────┬──────────────┘                ║
║                                 │                             ║
║         ┌────────────────────────┼────────────────────────┐       ║
║         │                        │                        │       ║
║         ▼                        ▼                        ▼       ║
║    ┌─────────┐            ┌─────────┐            ┌─────────┐    ║
║    │CONTADOR │            │CONTADOR │            │CONTADOR │    ║
║    │   1    │            │   2    │            │   {num_viviendas:>2}    │    ║
║    │DI S={dis[0]['seccion'] if dis else '?'}mm²│DI S={dis[1]['seccion'] if len(dis)>1 else '?'}mm²│DI S={dis[-1]['seccion'] if dis else '?'}mm²│    ║
║    └─────────┘            └─────────┘            └─────────┘    ║
║                                                                 ║
║              (Centralización de Contadores)                         ║
╚════════════════════════════════════════════════════════════════════════╝
"""
    
    return esquema


def generar_tabla_resultados(datos: Dict, tipo: str = "vivienda") -> str:
    """Genera tabla HTML con resultados"""
    
    if tipo == "vivienda":
        html = '<table class="tabla-resultados">'
        html += '<thead><tr>'
        html += '<th>Circuito</th><th>Descripción</th><th>P(W)</th><th>I(A)</th>'
        html += '<th>Sección</th><th>PIA</th><th>Tubo</th>'
        html += '</tr></thead><tbody>'
        
        for c in datos.get('circuitos', []):
            html += f'<tr>'
            html += f'<td><strong>{c.codigo}</strong></td>'
            html += f'<td>{c.nombre}</td>'
            html += f'<td>{c.potencia}</td>'
            html += f'<td>{c.intensidad}</td>'
            html += f'<td><strong>{c.seccion}</strong> mm²</td>'
            html += f'<td>{c.pia}A</td>'
            html += f'<td>{c.tubo}mm</td>'
            html += f'</tr>'
        
        html += '</tbody></table>'
        
        # DI
        di = datos.get('derivacion_individual')
        html += f'''
        <div class="di-result">
            <h4>Derivación Individual</h4>
            <p>Sección: <strong>{di.seccion} mm²</strong> | Tubo: <strong>{di.tubo} mm</strong> | IGA: <strong>{di.iga} A</strong></p>
        </div>
        '''
        
    elif tipo == "edificio":
        html = '<h3>Resultados</h3>'
        lga = datos.get('lga')
        html += f'''
        <div class="result-grid">
            <div class="result-item">
                <span class="label">LGA - Sección</span>
                <span class="value">{lga.seccion} mm²</span>
            </div>
            <div class="result-item">
                <span class="label">LGA - Tubo</span>
                <span class="value">{lga.tubo} mm</span>
            </div>
            <div class="result-item">
                <span class="label">LGA - Fusible</span>
                <span class="value">{lga.fusible} A</span>
            </div>
            <div class="result-item">
                <span class="label">LGA - Intensidad</span>
                <span class="value">{lga.intensidad} A</span>
            </div>
        </div>
        '''
        
        html += '<h4>Derivaciones Individuales</h4>'
        html += '<table class="tabla-resultados">'
        html += '<thead><tr><th>Vivienda</th><th>Tipo</th><th>P(W)</th><th>I(A)</th><th>Sección</th><th>Tubo</th></tr></thead><tbody>'
        
        for di in datos.get('derivaciones_individuales', []):
            html += f'''<tr>
                <td>{di['vivienda']}</td>
                <td>{di['tipo']}</td>
                <td>{di['potencia']}</td>
                <td>{di['intensidad']}</td>
                <td>{di['seccion']} mm²</td>
                <td>{di['tubo']}mm</td>
            </tr>'''
        
        html += '</tbody></table>'
    
    return html