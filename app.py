"""
Calculadora REBT - Aplicación Flask
 UF0884: Instalaciones de Enlace
 UF0885: Puestas a tierra
 UF0887: Instalaciones Interiores en Viviendas
 UF0888: Pública Concurrencia
"""

from flask import Flask, render_template, request, jsonify, Response, stream_with_context, redirect
from datetime import datetime
import sys
import os
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from engine_rebt import (
    calcular_circuitos_vivienda,
    calcular_edificio,
    calcular_lga,
    coef_simultaneidad,
    prevision_carga_viviendas,
    calcular_intensidad,
    calcular_intensidad_trifasica,
    calcular_seccion_cdt,
    calcular_seccion_por_intensidad,
    calcular_pia,
    calcular_tubo,
    normalizar_seccion,
    ResultadoCircuito,
    ResultadoDI,
    ResultadoLGA,
    CAIDAS_TENSION
)
from calculadoras_pdf import (
    calcular_seccion_cable_completa,
    calcular_caida_tension_detallado,
    calcular_proteccion_completa,
    calcular_cortocircuito_simplificado,
    calcular_paneles_solares,
    calcular_baterias_ah,
    calcular_ley_ohm,
    calcular_seccion_potencia_distancia,
    calcular_seccion_caida_distancia,
    calcular_resistencia_conductor,
    calcular_divisor_tension,
    calcular_factor_potencia,
    calcular_resistencias_paralelo,
    calcular_potencia_electrica,
    calcular_cortocircuito_impedancias,
    calcular_electrodos_tierra,
    calcular_longitud_maxima_cable,
    calcular_numero_picas,
    calcular_codigo_colores_resistencia
)
from schemes import generar_esquema_vivienda, generar_esquema_edificio

# RAG solo en local (no en Vercel por tamaño)
RAG_AVAILABLE = False
REBT_Search = None

# Resolutor solo en local
RESOLUTOR_AVAILABLE = False
resolver_ejercicio = None
formatear_resultado = None

if os.environ.get('VERCEL') != '1':
    try:
        from ollama_client import REBT_Search
        RAG_AVAILABLE = True
    except:
        pass
    
    try:
        from resolutor import resolver_ejercicio, formatear_resultado
        RESOLUTOR_AVAILABLE = True
    except:
        pass

# Importar generador MEM
MEM_AVAILABLE = False

try:
    from mem_generator import generar_mem_txt, guardar_mem
    MEM_AVAILABLE = True
except Exception as e:
    print(f"MEM no disponible: {e}")
    generar_mem_txt = None
    guardar_mem = None

# Importar generador de proyectos
PROYECTO_AVAILABLE = False

try:
    from proyecto_generator import generar_proyecto, guardar_proyecto
    PROYECTO_AVAILABLE = True
except Exception as e:
    print(f"Proyecto no disponible: {e}")
    generar_proyecto = None
    guardar_proyecto = None

# Importar generador SVG
SVG_AVAILABLE = False

try:
    from svg_generator import generar_svg_profesional, svg_a_bytes
    SVG_AVAILABLE = True
except Exception as e:
    print(f"SVG no disponible: {e}")
    generar_svg_profesional = None

app = Flask(__name__)

# ============================================================
# RUTAS PRINCIPALES
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/vivienda')
def vivienda():
    return render_template('index_vivienda.html')


@app.route('/edificio')
def edificio():
    return render_template('index_edificio.html')


@app.route('/circuito')
def circuito():
    return render_template('index_circuito.html')


@app.route('/di')
def di_page():
    return render_template('index_di.html')


@app.route('/ejercicios')
def ejercicios():
    return render_template('index_ejercicios.html')


@app.route('/proyecto')
def proyecto():
    return render_template('index_proyecto.html')


@app.route('/buscar')
def buscar_page():
    return render_template('index_buscar.html')


@app.route('/calcular-vivienda', methods=['POST'])
def calcular_vivienda():
    """UF0887 - Circuitos de vivienda"""
    try:
        puntos_luz = int(request.form.get('puntos_luz', 10))
        Tomas = int(request.form.get('tomas', 20))
        lavadora = request.form.get('lavadora') == 'on'
        cocina = request.form.get('cocina') == 'on'
        aire_ac = request.form.get('aire_ac') == 'on'
        secadora = request.form.get('secadora') == 'on'
        calefaccion = request.form.get('calefaccion') == 'on'
        domotica = request.form.get('domotica') == 'on'
        recarga_ve = request.form.get('recarga_ve') == 'on'
        longitud = float(request.form.get('longitud', 25))
        
        datos = calcular_circuitos_vivienda(
            puntos_luz=puntos_luz,
            Tomas=Tomas,
            lavadora=lavadora,
            cocina=cocina,
            aire_ac=aire_ac,
            secadora=secadora,
            calefaccion=calefaccion,
            domotica=domotica,
            recarga_ve=recarga_ve,
            longitud=longitud
        )
        
        # Generar esquema unifilar
        esquema = generar_esquema_vivienda(datos)
        
        return render_template('index_vivienda.html', 
                         resultado_vivienda=datos,
                         esquema=esquema)
    except Exception as e:
        return render_template('index_vivienda.html', error=str(e))


@app.route('/calcular-edificio', methods=['POST'])
def calcular_edificio_route():
    """UF0884 - Instalaciones de enlace"""
    try:
        n_basicas = int(request.form.get('n_viviendas_basicas', 0))
        n_elevadas = int(request.form.get('n_viviendas_elevadas', 0))
        pot_servicios = float(request.form.get('potencia_servicios', 0))
        superficie_local = float(request.form.get('superficie_local', 0))
        superficie_garaje = float(request.form.get('superficie_garaje', 0))
        ventilacion = request.form.get('ventilacion_garaje', 'natural')
        longitud_lga = float(request.form.get('longitud_lga', 10))
        longitud_di = float(request.form.get('longitud_di', 15))
        es_trifasica = request.form.get('es_trifasica') == 'on'
        
        datos = calcular_edificio(
            n_viviendas_basicas=n_basicas,
            n_viviendas_elevadas=n_elevadas,
            potencia_servicios=pot_servicios,
            superficie_local=superficie_local,
            superficie_garaje=superficie_garaje,
            ventilacion_garaje=ventilacion,
            longitud_lga=longitud_lga,
            longitud_di=longitud_di,
            es_trifasica=es_trifasica
        )
        
        return render_template('index_edificio.html',
                         resultado_edificio=datos)
    except Exception as e:
        return render_template('index_edificio.html', error=str(e))


@app.route('/calcular-circuito', methods=['POST'])
def calcular_circuito():
    """Cálculo genérico de un circuito"""
    try:
        potencia = float(request.form.get('potencia', 1000))
        longitud = float(request.form.get('longitud', 10))
        fp = float(request.form.get('fp', 0.8))
        tension = float(request.form.get('tension', 230))
        tipo_instalacion = request.form.get('tipo_instalacion', 'vivienda')
        
        intensidad = calcular_intensidad(potencia, tension, fp)
        
        # CDT según tipo REBT ITC-BT-19
        cdt_max = CAIDAS_TENSION.get(tipo_instalacion, CAIDAS_TENSION["vivienda"])["interior"]
        seccion_cdt = calcular_seccion_cdt(potencia, longitud, cdt_max, tension, fp)
        seccion, iz = calcular_seccion_por_intensidad(intensidad, "B1", "2xPVC")
        seccion_final = normalizar_seccion(max(seccion, seccion_cdt, 1.5))
        pia = calcular_pia(intensidad)
        tubo = calcular_tubo(seccion_final)
        
        return render_template('index_circuito.html',
                         resultado_circuito={
                             'potencia': potencia,
                             'intensidad': round(intensidad, 2),
                             'seccion_cdt': round(seccion_cdt, 2),
                             'seccion': seccion_final,
                             'pia': pia,
                             'tubo': tubo,
'cdt_max': cdt_max
                          })
    except Exception as e:
        return render_template('index_circuito.html', error=str(e))


@app.route('/calcular-di', methods=['POST'])
def calcular_di():
    """Cálculo de derivación individual"""
    try:
        potencia = float(request.form.get('potencia', 5000))
        longitud = float(request.form.get('longitud', 15))
        es_trifasica = request.form.get('es_trifasica') == 'on'
        
        # Tensión: 400V si trifásica, 230V si no
        tension = 400 if es_trifasica else 230
        
        if es_trifasica:
            intensidad = calcular_intensidad_trifasica(potencia, tension)
        else:
            intensidad = calcular_intensidad(potencia, tension)
        
        seccion_cdt = calcular_seccion_cdt(potencia, longitud, 1, tension)
        aislamiento = "3xPVC" if es_trifasica else "2xPVC"
        seccion, iz = calcular_seccion_por_intensidad(intensidad, "B1", aislamiento)
        seccion_final = normalizar_seccion(max(seccion, seccion_cdt, 6))
        iga = calcular_pia(intensidad)
        n_cond = 5 if es_trifasica else 3
        tubo = calcular_tubo(seccion_final, n_cond)
        
        return render_template('index_di.html',
                         resultado_di={
                             'potencia': potencia,
                             'tension': tension,
                             'intensidad': round(intensidad, 2),
                             'seccion_cdt': round(seccion_cdt, 2),
                             'seccion': seccion_final,
                             'iga': iga,
                             'tubo': tubo,
'n_conductores': n_cond
                          })
    except Exception as e:
        return render_template('index_di.html', error=str(e))


@app.route('/api/calcular', methods=['POST'])
def api_calcular():
    """API REST universal para TODAS las calculadoras"""
    data = request.get_json()
    tipo = data.get('tipo')
    
    try:
        # === Vivienda, Edificio, Circuito (ya implementado) ===
        if tipo == 'vivienda':
            resultado = calcular_circuitos_vivienda(
                data['puntos_luz'],
                data['tomas'],
                data.get('lavadora', False),
                data.get('cocina', False),
                data.get('aire_ac', False),
                data.get('longitud', 25)
            )
        elif tipo == 'edificio':
            resultado = calcular_edificio(
                data.get('n_basicas', 0),
                data.get('n_elevadas', 0),
                data.get('pot_servicios', 0),
                data.get('superficie_local', 0),
                data.get('superficie_garaje', 0),
                data.get('ventilacion', 'natural'),
                data.get('longitud_lga', 10),
                data.get('longitud_di', 15),
                data.get('es_trifasica', False)
            )
        elif tipo == 'circuito':
            intensidad = calcular_intensidad(data['potencia'], data.get('tension', 230), data.get('fp', 0.8))
            cdt = data.get('cdt', 3)
            seccion_cdt = calcular_seccion_cdt(data['potencia'], data['longitud'], cdt, data.get('tension', 230), data.get('fp', 0.8))
            seccion, iz = calcular_seccion_por_intensidad(intensidad)
            resultado = {
                'intensidad': round(intensidad, 2),
                'seccion_cdt': round(seccion_cdt, 2),
                'seccion': normalizar_seccion(max(seccion, seccion_cdt)),
                'pia': calcular_pia(intensidad),
                'tubo': calcular_tubo(normalizar_seccion(max(seccion, seccion_cdt)))
            }
        
        # === Calculadoras de Cable ===
        elif tipo == 'seccion':
            resultado = calcular_seccion_cable_completa(
                data['potencia'],
                data.get('tension', 230),
                data.get('fp', 0.8),
                data.get('longitud', 25),
                data.get('cdt', 3),
                data.get('metodo', 'B1'),
                data.get('aislamiento', '2xPVC'),
                data.get('material', 'cobre'),
                data.get('trifasica', False)
            )
        elif tipo == 'caida':
            resultado = calcular_caida_tension_detallado(
                data['potencia'],
                data.get('longitud', 25),
                data.get('seccion', 2.5),
                data.get('tension', 230),
                data.get('fp', 0.8),
                data.get('material', 'cobre')
            )
        elif tipo == 'proteccion':
            resultado = calcular_proteccion_completa(
                data['intensidad'],
                data.get('seccion', 2.5),
                data.get('metodo', 'B1'),
                data.get('aislamiento', '2xPVC'),
                data.get('tipo_curva', 'C'),
                data.get('corriente_cc', 0)
            )
        
        # === Solar y Baterías ===
        elif tipo == 'solar':
            resultado = calcular_paneles_solares(
                data.get('consumo_diario', 10),
                data.get('irradiacion', 4.5),
                data.get('perdidas', 25),
                data.get('autonomia_horas', 24),
                data.get('tension_sistema', 24)
            )
        elif tipo == 'baterias':
            resultado = calcular_baterias_ah(
                data.get('consumo', 10),
                data.get('tension', 24),
                data.get('dias', 1),
                data.get('profundidad', 50)
            )
        
        # === Cálculos Eléctricos ===
        elif tipo == 'consumo_diario':
            consumo_kwh = data.get('consumo_kwh', 10)
            tension = data.get('tension', 24)
            resultado = {
                'consumo_kwh': consumo_kwh,
                'consumo_wh': consumo_kwh * 1000,
                'consumo_ah': (consumo_kwh * 1000) / tension,
                'tension_v': tension
            }
        elif tipo == 'divisor':
            resultado = calcular_divisor_tension(
                data.get('v_in', 12),
                data.get('r1', 1000),
                data.get('r2', 1000),
                data.get('r_load', 0)
            )
        elif tipo == 'fp':
            resultado = calcular_factor_potencia(
                data.get('p_activa', 1000),
                data.get('s_aparente', 0),
                data.get('q_reactiva', 0),
                data.get('tension', 230)
            )
        elif tipo == 'rparalelo':
            resistencias = data.get('resistencias', [100, 100])
            voltaje = data.get('voltaje', 0)
            if voltaje > 0:
                resultado = calcular_resistencias_paralelo_voltaje(resistencias, voltaje)
            else:
                resultado = calcular_resistencias_paralelo(resistencias)
        elif tipo == 'potencia_elec':
            resultado = calcular_potencia_electrica(
                data.get('tension', 230),
                data.get('corriente', 10),
                data.get('fp', 0.8),
                data.get('trifasica', False)
            )
        elif tipo == 'ohm':
            resultado = calcular_ley_ohm(
                data.get('voltaje', 0),
                data.get('corriente', 0),
                data.get('resistencia', 0),
                data.get('potencia', 0)
            )
        elif tipo == 'rconductor':
            resultado = calcular_resistencia_conductor(
                data.get('longitud', 100),
                data.get('seccion', 2.5),
                data.get('material', 'cobre'),
                data.get('temperatura', 20)
            )
        
        # === Cortocircuito ===
        elif tipo == 'icc_simplificado':
            resultado = {'icc_a': calcular_cortocircuito_simplificado(
                data.get('scc_mva', 100),
                data.get('tension', 400)
            )}
        elif tipo == 'icc_impedancias':
            resultado = calcular_cortocircuito_impedancias(
                data.get('tension', 400),
                data.get('z_linea', 0.01),
                data.get('z_trafo', 0.05),
                data.get('z_red', 0.1),
                data.get('trifasica', False)
            )
        
        # === Tierra ===
        elif tipo == 'tierra':
            resultado = calcular_electrodos_tierra(
                data.get('resistividad', 100),
                data.get('tipo', 'pica'),
                data.get('longitud', 1.5),
                data.get('n_picas', 1),
                data.get('separacion', 3),
                data.get('suelo', 'medio')
            )
        elif tipo == 'longitud_max':
            resultado = calcular_longitud_maxima_cable(
                data.get('potencia', 2000),
                data.get('seccion', 2.5),
                data.get('cdt', 3),
                data.get('tension', 230),
                data.get('fp', 0.8),
                data.get('material', 'cobre')
            )
        elif tipo == 'picas':
            resultado = calcular_numero_picas(
                data.get('resistencia_obj', 30),
                data.get('resistividad', 100),
                data.get('longitud', 1.5),
                data.get('separacion', 3)
            )
        
        # === Sección por Distancia ===
        elif tipo == 'seccion_pot_dist':
            resultado = calcular_seccion_potencia_distancia(
                data.get('potencia', 2000),
                data.get('distancia', 25),
                data.get('tension', 230),
                data.get('cdt', 3)
            )
        elif tipo == 'seccion_caida_dist':
            resultado = calcular_seccion_caida_distancia(
                data.get('potencia', 2000),
                data.get('distancia', 25),
                data.get('cdt', 3),
                data.get('tension', 230),
                data.get('material', 'cobre')
            )
        
        # === Código Colores ===
        elif tipo == 'codigo_colores':
            resultado = calcular_codigo_colores_resistencia(
                data.get('valor_ohm', 1000),
                data.get('tolerancia', 'oro')
            )
        
        else:
            return jsonify({'error': f'Tipo no válido: {tipo}'}), 400
            
        return jsonify({'ok': True, 'resultado': resultado})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/buscar', methods=['POST'])
def buscar():
    """Búsqueda RAG en documentos con Ollama"""
    try:
        query = request.form.get('q', '')
        tipo = request.form.get('tipo', 'todos')
        usar_ia = request.form.get('usar_ia') == 'on'
        
        if not RAG_AVAILABLE:
            return render_template('index_buscar.html', error='RAG no disponible')
        
        search = REBT_Search()
        
        if usar_ia:
            # Usar Ollama para generar respuesta con contexto
            resultado = search.responder_con_fuentes(query)
            return render_template('index_buscar.html',
                               query=query,
                               respuesta_ia=resultado['respuesta'],
                               resultados=resultado['fuentes'],
                               usar_ia=True)
        else:
            # Búsqueda tradicional sin IA
            if tipo == 'normativa':
                results = search.buscar_normativa(query)
            elif tipo == 'ejercicios':
                results = search.buscar_ejercicios(query)
            elif tipo == 'proyectos':
                results = search.buscar_proyectos(query)
            else:
                results = search.buscar(query)
            
            return render_template('index_buscar.html',
                               query=query,
                               resultados=results,
                               usar_ia=False)
    except Exception as e:
        return render_template('index_buscar.html', error=str(e))


@app.route('/ver-resultados', methods=['POST'])
def ver_resultados():
    """Ver todos los resultados en nueva página"""
    try:
        query = request.form.get('query', '')
        tipo = request.form.get('tipo', 'todos')
        usar_ia = request.form.get('usar_ia') == 'on'
        
        if not RAG_AVAILABLE:
            return "RAG no disponible"
        
        search = REBT_Search()
        
        if usar_ia:
            # Respuesta generada con Ollama
            resultado = search.responder_con_fuentes(query, n_resultados=20)
            html = f"<html><head><title>Resultados IA: {query}</title></head><body style='font-family: sans-serif; padding: 20px; background: #0f172a; color: #e2e8f0;'>"
            html += f"<h1>🤖 Respuesta IA para: '{query}'</h1>"
            html += f"<div style='background: #1e293b; padding: 20px; margin: 20px 0; border-radius: 8px; border-left: 4px solid #22d3ee;'>"
            html += f"<p style='color: #cbd5e1; white-space: pre-wrap;'>{resultado['respuesta']}</p>"
            html += "</div>"
            html += f"<h2 style='color: #22d3ee;'>📚 Fuentes consultadas</h2>"
            
            for i, r in enumerate(resultado['fuentes'], 1):
                similitud = int(r.get('similitud', 0) * 100)
                html += f"<div style='background: #1e293b; padding: 16px; margin: 12px 0; border-radius: 8px;'>"
                html += f"<h3 style='color: #22d3ee; margin: 0;'>{i}. {r['fuente']} ({r['tipo']})</h3>"
                html += f"<p style='color: #94a3b8; font-size: 12px;'>Relevancia: {similitud}%</p>"
                html += f"<p style='color: #cbd5e1;'>{r['texto']}</p>"
                html += "</div>"
        else:
            # Búsqueda tradicional
            if tipo == 'normativa':
                results = search.buscar_normativa(query, n_resultados=20)
            elif tipo == 'ejercicios':
                results = search.buscar_ejercicios(query, n_resultados=20)
            elif tipo == 'proyectos':
                results = search.buscar_proyectos(query, n_resultados=20)
            else:
                results = search.buscar(query, n_resultados=20)
            
            html = f"<html><head><title>Resultados: {query}</title></head><body style='font-family: sans-serif; padding: 20px; background: #0f172a; color: #e2e8f0;'>"
            html += f"<h1>Resultados para: '{query}'</h1>"
            html += f"<p style='color: #94a3b8;'>{len(results)} encontrados</p><hr>"
            
            for i, r in enumerate(results, 1):
                similitud = int(r.get('similitud', 0) * 100)
                html += f"<div style='background: #1e293b; padding: 16px; margin: 12px 0; border-radius: 8px;'>"
                html += f"<h3 style='color: #22d3ee; margin: 0;'>{i}. {r['fuente']} ({r['tipo']})</h3>"
                html += f"<p style='color: #94a3b8; font-size: 12px;'>Relevancia: {similitud}%</p>"
                html += f"<p style='color: #cbd5e1;'>{r['texto']}</p>"
                html += "</div><hr>"
        
        html += "<a href='/' style='color: #22d3ee;'>← Volver</a></body></html>"
        return html
    except Exception as e:
        return f"Error: {e}"


@app.route('/resolver', methods=['POST'])
def resolver():
    """Resolver ejercicio REBT"""
    try:
        pregunta = request.form.get('pregunta', '')
        ayuda = request.form.get('ayuda', 'no') == 'si'
        
        if not RESOLUTOR_AVAILABLE:
            return render_template('index_ejercicios.html', error='Resolutor no disponible')
        
        resultado = resolver_ejercicio(pregunta)
        
        ayuda_rag = []
        if ayuda and RAG_AVAILABLE:
            search = REBT_Search()
            ayuda_rag = search.buscar_ejercicios(pregunta)[:3]
        
        return render_template('index_ejercicios.html',
                           pregunta=pregunta,
                           resultado=resultado,
                           ayuda_rag=ayuda_rag)
    except Exception as e:
        return render_template('index_ejercicios.html', error=str(e))


@app.route('/download/mem', methods=['POST'])
def download_mem():
    """Descargar MEM"""
    try:
        tipo = request.form.get('tipo', 'vivienda')
        datos = {
            'puntos_luz': int(request.form.get('puntos_luz', 20)),
            'tomas': int(request.form.get('tomas', 20)),
            'cocina': request.form.get('cocina') == 'si',
            'longitud': int(request.form.get('longitud', 25)),
            'n_viviendas_basicas': int(request.form.get('n_basicas', 4)),
            'n_viviendas_elevadas': int(request.form.get('n_elevadas', 6)),
            'potencia_servicios': int(request.form.get('potencia_servicios', 0)),
        }
        
        mem = generar_mem_txt(datos, tipo)
        filename = f"mem_{tipo}_{datetime.now().strftime('%Y%m%d')}.txt"
        guardar_mem(mem, filename)
        
        return Response(
            mem,
            mimetype='text/plain',
            headers={'Content-disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/generar-proyecto', methods=['POST'])
def generar_proyecto_route():
    """Generar proyecto"""
    try:
        datos = {
            'tipo': request.form.get('tipo', 'vivienda'),
            'nombre': request.form.get('nombre', 'Proyecto'),
            'direccion': request.form.get('direccion', ''),
            'superficie': int(request.form.get('superficie', 100)),
            'potencia': int(request.form.get('potencia', 5000)),
            'puntos_luz': int(request.form.get('puntos_luz', 20)),
            'tomas': int(request.form.get('tomas', 20)),
            'cocina': request.form.get('cocina') == 'si',
            'longitud': int(request.form.get('longitud', 25)),
        }
        
        proyecto = generar_proyecto(datos)
        filename = f"proyecto_{datos['tipo']}_{datetime.now().strftime('%Y%m%d')}.txt"
        guardar_proyecto(proyecto, filename)
        
        return Response(
            proyecto,
            mimetype='text/plain',
            headers={'Content-disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/download/svg', methods=['POST'])
def download_svg():
    """Descargar diagrama unifilar SVG"""
    try:
        tipo = request.form.get('tipo', 'vivienda')
        
        if tipo == 'vivienda':
            puntos_luz = int(request.form.get('puntos_luz', 20))
            Tomas = int(request.form.get('tomas', 20))
            datos = calcular_circuitos_vivienda(puntos_luz, Tomas)
            svg = generar_svg_profesional(datos, tipo="EB")
        else:
            n_basicas = int(request.form.get('n_basicas', 2))
            n_elevadas = int(request.form.get('n_elevadas', 2))
            datos = calcular_edificio(n_basicas, n_elevadas)
            svg = generar_svg_profesional(datos, tipo="EE")
        
        return Response(
            svg_a_bytes(svg),
            mimetype='image/svg+xml',
            headers={'Content-disposition': 'attachment; filename=esquema_unifilar.svg'}
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400


# ============================================================
# RUTAS PARA CALCULADORAS PDF
# ============================================================

@app.route('/calc_seccion', methods=['GET', 'POST'])
def calc_seccion():
    """Calculadora de Sección de Cable por Amperaje y Potencia"""
    resultado = None
    if request.method == 'POST':
        try:
            potencia = float(request.form.get('potencia', 1000))
            tension = float(request.form.get('tension', 230))
            fp = float(request.form.get('fp', 0.8))
            longitud = float(request.form.get('longitud', 25))
            cdt_percent = float(request.form.get('cdt', 3))
            metodo = request.form.get('metodo', 'B1')
            aislamiento = request.form.get('aislamiento', '2xPVC')
            material = request.form.get('material', 'cobre')
            es_trifasica = request.form.get('trifasica') == 'on'
            
            resultado = calcular_seccion_cable_completa(
                potencia, tension, fp, longitud, cdt_percent,
                metodo, aislamiento, material, es_trifasica
            )
        except Exception as e:
            resultado = {'error': str(e)}
    
    return render_template('calc_seccion.html', resultado=resultado)


@app.route('/calc_caida', methods=['GET', 'POST'])
def calc_caida():
    """Calculadora de Caída de Tensión"""
    resultado = None
    if request.method == 'POST':
        try:
            potencia = float(request.form.get('potencia', 1000))
            longitud = float(request.form.get('longitud', 25))
            seccion = float(request.form.get('seccion', 2.5))
            tension = float(request.form.get('tension', 230))
            fp = float(request.form.get('fp', 0.8))
            material = request.form.get('material', 'cobre')
            
            resultado = calcular_caida_tension_detallado(
                potencia, longitud, seccion, tension, fp, material
            )
        except Exception as e:
            resultado = {'error': str(e)}
    
    return render_template('calc_caida.html', resultado=resultado)


@app.route('/calc_proteccion', methods=['GET', 'POST'])
def calc_proteccion():
    """Calculadora de Protección (Sobrecarga y Cortocircuito)"""
    resultado = None
    if request.method == 'POST':
        try:
            intensidad = float(request.form.get('intensidad', 10))
            seccion_cable = float(request.form.get('seccion', 2.5))
            metodo = request.form.get('metodo', 'B1')
            aislamiento = request.form.get('aislamiento', '2xPVC')
            tipo_curva = request.form.get('curva', 'C')
            corriente_cc = float(request.form.get('corriente_cc', 0))
            
            resultado = calcular_proteccion_completa(
                intensidad, seccion_cable, metodo, aislamiento,
                tipo_curva, corriente_cc
            )
        except Exception as e:
            resultado = {'error': str(e)}
    
    return render_template('calc_proteccion.html', resultado=resultado)


@app.route('/calc_solar', methods=['GET', 'POST'])
def calc_solar():
    """Calculadora de Paneles Solares"""
    resultado = None
    if request.method == 'POST':
        try:
            consumo_diario = float(request.form.get('consumo_diario', 10))
            irradiacion = float(request.form.get('irradiacion', 4.5))
            perdidas = float(request.form.get('perdidas', 25)) / 100
            autonomia_horas = float(request.form.get('autonomia', 24))
            tension_sistema = float(request.form.get('tension', 24))
            
            resultado = calcular_paneles_solares(
                consumo_diario, irradiacion, perdidas,
                autonomia_horas, tension_sistema
            )
            
            # Calcular también baterías
            if request.form.get('calcular_baterias') == 'on':
                profundidad = float(request.form.get('profundidad', 50)) / 100
                dias = autonomia_horas / 24
                resultado['baterias'] = calcular_baterias_ah(
                    consumo_diario, tension_sistema, dias, profundidad
                )
        except Exception as e:
            resultado = {'error': str(e)}
    
    return render_template('calc_solar.html', resultado=resultado)


# ============================================================
# RUTAS PARA EL RESTO DE CALCULADORAS PDF
# ============================================================

@app.route('/calc_baterias_solares', methods=['GET', 'POST'])
def calc_baterias_solares():
    """Calculadora Baterías Solares - Capacidad (Ah) y Autonomía"""
    resultado = None
    if request.method == 'POST':
        try:
            consumo = float(request.form.get('consumo_diario', 10))
            tension = float(request.form.get('tension', 24))
            dias = float(request.form.get('dias', 1))
            profundidad = float(request.form.get('profundidad', 50)) / 100
            resultado = calcular_baterias_ah(consumo, tension, dias, profundidad)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_baterias_solares.html', resultado=resultado)


@app.route('/calc_consumo_diario', methods=['GET', 'POST'])
def calc_consumo_diario():
    """Calculadora Consumo Diario Solar - Wh/Ah para Dimensionado"""
    resultado = None
    if request.method == 'POST':
        try:
            consumo_kwh = float(request.form.get('consumo_kwh', 10))
            tension = float(request.form.get('tension', 24))
            resultado = {
                "consumo_kwh": consumo_kwh,
                "consumo_wh": consumo_kwh * 1000,
                "consumo_ah": (consumo_kwh * 1000) / tension,
                "tension_v": tension
            }
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_consumo_diario.html', resultado=resultado)


@app.route('/calc_divisor', methods=['GET', 'POST'])
def calc_divisor():
    """Calculadora Divisor de Tensión - Con y Sin Carga"""
    resultado = None
    if request.method == 'POST':
        try:
            v_in = float(request.form.get('v_in', 12))
            r1 = float(request.form.get('r1', 1000))
            r2 = float(request.form.get('r2', 1000))
            r_load = float(request.form.get('r_load', 0))
            resultado = calcular_divisor_tension(v_in, r1, r2, r_load)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_divisor.html', resultado=resultado)


@app.route('/calc_fp', methods=['GET', 'POST'])
def calc_fp():
    """Calculadora Factor de Potencia - Corrección y Coseno Fi"""
    resultado = None
    if request.method == 'POST':
        try:
            p = float(request.form.get('p_activa', 1000))
            s = float(request.form.get('s_aparente', 0))
            q = float(request.form.get('q_reactiva', 0))
            v = float(request.form.get('tension', 230))
            resultado = calcular_factor_potencia(p, s, q, v)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_fp.html', resultado=resultado)


@app.route('/calc_rparalelo', methods=['GET', 'POST'])
def calc_rparalelo():
    """Calculadora Resistencias en Paralelo"""
    resultado = None
    if request.method == 'POST':
        try:
            resistencias = [float(r) for r in request.form.getlist('resistencia') if r]
            voltaje = float(request.form.get('voltaje', 0))
            if voltaje > 0:
                resultado = calcular_resistencias_paralelo_voltaje(resistencias, voltaje)
            else:
                resultado = calcular_resistencias_paralelo(resistencias)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_rparalelo.html', resultado=resultado)


@app.route('/calc_costo', methods=['GET', 'POST'])
def calc_costo():
    """Calculadora Consumo Eléctrico - Convierte kWh a Costo"""
    resultado = None
    if request.method == 'POST':
        try:
            consumo = float(request.form.get('consumo_kwh', 300))
            precio_kwh = float(request.form.get('precio_kwh', 0.15))
            potencia_kw = float(request.form.get('potencia_kw', 3.45))
            precio_pot = float(request.form.get('precio_pot', 0.12))
            resultado = calcular_costo_consumo(consumo, precio_kwh, potencia_kw, precio_pot)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_costo.html', resultado=resultado)


@app.route('/calc_icc_simplificado', methods=['GET', 'POST'])
def calc_icc_simplificado():
    """Calculadora Cortocircuito Simplificada - Icc sin Datos de Red"""
    resultado = None
    if request.method == 'POST':
        try:
            scc_mva = float(request.form.get('scc_mva', 100))
            tension = float(request.form.get('tension', 400))
            resultado = {"icc_a": calcular_cortocircuito_simplificado(scc_mva, tension)}
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_icc_simplificado.html', resultado=resultado)


@app.route('/calc_icc_impedancias', methods=['GET', 'POST'])
def calc_icc_impedancias():
    """Calculadora Cortocircuito por Impedancias"""
    resultado = None
    if request.method == 'POST':
        try:
            tension = float(request.form.get('tension', 400))
            z_red = float(request.form.get('z_red', 0.1))
            z_trafo = float(request.form.get('z_trafo', 0.05))
            z_linea = float(request.form.get('z_linea', 0.01))
            es_trifasica = request.form.get('trifasica') == 'on'
            resultado = calcular_cortocircuito_impedancias(tension, z_linea, z_trafo, z_red, es_trifasica)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_icc_impedancias.html', resultado=resultado)


@app.route('/calc_tierra', methods=['GET', 'POST'])
def calc_tierra():
    """Calculadora Electrodos de Tierra"""
    resultado = None
    if request.method == 'POST':
        try:
            resistividad = float(request.form.get('resistividad', 100))
            tipo = request.form.get('tipo', 'pica')
            longitud = float(request.form.get('longitud', 1.5))
            n_picass = int(request.form.get('n_picas', 1))
            separacion = float(request.form.get('separacion', 3))
            suelo = request.form.get('suelo', 'medio')
            resultado = calcular_electrodos_tierra(resistividad, tipo, longitud, n_picass, separacion, suelo)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_tierra.html', resultado=resultado)


@app.route('/calc_longitud_max', methods=['GET', 'POST'])
def calc_longitud_max():
    """Calculadora Longitud Máxima de Cable"""
    resultado = None
    if request.method == 'POST':
        try:
            potencia = float(request.form.get('potencia', 2000))
            seccion = float(request.form.get('seccion', 2.5))
            cdt = float(request.form.get('cdt', 3))
            tension = float(request.form.get('tension', 230))
            fp = float(request.form.get('fp', 0.8))
            material = request.form.get('material', 'cobre')
            resultado = calcular_longitud_maxima_cable(potencia, seccion, cdt, tension, fp, material)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_longitud_max.html', resultado=resultado)


@app.route('/calc_picas', methods=['GET', 'POST'])
def calc_picas():
    """Calculadora Picas de Tierra - ¿Cuántas Jabalinas necesitas?"""
    resultado = None
    if request.method == 'POST':
        try:
            resistencia_obj = float(request.form.get('resistencia_obj', 30))
            resistividad = float(request.form.get('resistividad', 100))
            longitud = float(request.form.get('longitud', 1.5))
            separacion = float(request.form.get('separacion', 3))
            resultado = calcular_numero_picas(resistencia_obj, resistividad, longitud, separacion)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_picas.html', resultado=resultado)


@app.route('/calc_potencia_elec', methods=['GET', 'POST'])
def calc_potencia_elec():
    """Calculadora Potencia Eléctrica - Monofásica y Trifásica"""
    resultado = None
    if request.method == 'POST':
        try:
            tension = float(request.form.get('tension', 230))
            corriente = float(request.form.get('corriente', 10))
            fp = float(request.form.get('fp', 0.8))
            es_trifasica = request.form.get('trifasica') == 'on'
            resultado = calcular_potencia_electrica(tension, corriente, fp, es_trifasica)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_potencia_elec.html', resultado=resultado)


@app.route('/calc_rconductor', methods=['GET', 'POST'])
def calc_rconductor():
    """Calculadora Resistencia de un Conductor y Resistividad"""
    resultado = None
    if request.method == 'POST':
        try:
            longitud = float(request.form.get('longitud', 100))
            seccion = float(request.form.get('seccion', 2.5))
            material = request.form.get('material', 'cobre')
            temperatura = float(request.form.get('temperatura', 20))
            resultado = calcular_resistencia_conductor(longitud, seccion, material, temperatura)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_rconductor.html', resultado=resultado)


@app.route('/calc_seccion_pot_dist', methods=['GET', 'POST'])
def calc_seccion_pot_dist():
    """Calculadora Sección de Cables - Potencia y Distancia"""
    resultado = None
    if request.method == 'POST':
        try:
            potencia = float(request.form.get('potencia', 2000))
            distancia = float(request.form.get('distancia', 25))
            tension = float(request.form.get('tension', 230))
            cdt = float(request.form.get('cdt', 3))
            resultado = calcular_seccion_potencia_distancia(potencia, distancia, tension, cdt)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_seccion_pot_dist.html', resultado=resultado)


@app.route('/calc_seccion_caida_dist', methods=['GET', 'POST'])
def calc_seccion_caida_dist():
    """Calculadora Sección por Caída de Tensión - Distancia"""
    resultado = None
    if request.method == 'POST':
        try:
            potencia = float(request.form.get('potencia', 2000))
            distancia = float(request.form.get('distancia', 25))
            cdt = float(request.form.get('cdt', 3))
            tension = float(request.form.get('tension', 230))
            material = request.form.get('material', 'cobre')
            resultado = calcular_seccion_caida_distancia(potencia, distancia, cdt, tension, material)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_seccion_caida_dist.html', resultado=resultado)


@app.route('/calc_ohm', methods=['GET', 'POST'])
def calc_ohm():
    """Calculadora Ley de Ohm y Potencia"""
    resultado = None
    if request.method == 'POST':
        try:
            voltaje = float(request.form.get('voltaje', 0))
            corriente = float(request.form.get('corriente', 0))
            resistencia = float(request.form.get('resistencia', 0))
            potencia = float(request.form.get('potencia', 0))
            resultado = calcular_ley_ohm(voltaje=voltaje, corriente=corriente, resistencia=resistencia, potencia=potencia)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_ohm.html', resultado=resultado)


@app.route('/calc_codigo_colores', methods=['GET', 'POST'])
def calc_codigo_colores():
    """Código de Colores de Resistencias - 4 y 5 Bandas"""
    resultado = None
    if request.method == 'POST':
        try:
            valor = float(request.form.get('valor_ohm', 1000))
            tolerancia = request.form.get('tolerancia', 'oro')
            resultado = calcular_codigo_colores_resistencia(valor, tolerancia)
        except Exception as e:
            resultado = {'error': str(e)}
    return render_template('calc_codigo_colores.html', resultado=resultado)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)