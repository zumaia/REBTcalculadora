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
    return redirect('/vivienda')


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
def di():
    return render_template('index_di.html')


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
        
        return render_template('index.html', 
                         opcion='vivienda',
                         resultado_vivienda=datos,
                         esquema=esquema)
    except Exception as e:
        return render_template('index.html', error=str(e))


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
        
        return render_template('index.html',
                         opcion='edificio',
                         resultado_edificio=datos)
    except Exception as e:
        return render_template('index.html', error=str(e))


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
        
        return render_template('index.html',
                         opcion='circuito',
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
        return render_template('index.html', error=str(e))


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
        
        return render_template('index.html',
                         opcion='di',
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
        return render_template('index.html', error=str(e))


@app.route('/api/calcular', methods=['POST'])
def api_calcular():
    """API REST para cálculos"""
    data = request.get_json()
    tipo = data.get('tipo')
    
    try:
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
        else:
            return jsonify({'error': 'Tipo no válido'}), 400
            
        return jsonify({'ok': True, 'resultado': resultado})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/buscar', methods=['POST'])
def buscar():
    """Búsqueda RAG en documentos"""
    try:
        query = request.form.get('q', '')
        tipo = request.form.get('tipo', 'todos')
        
        if not RAG_AVAILABLE:
            return render_template('index.html', error='RAG no disponible')
        
        search = REBT_Search()
        
        if tipo == 'normativa':
            results = search.buscar_normativa(query)
        elif tipo == 'ejercicios':
            results = search.buscar_ejercicios(query)
        elif tipo == 'proyectos':
            results = search.buscar_proyectos(query)
        else:
            results = search.buscar(query)
        
        return render_template('index.html',
                           opcion='buscar',
                           query=query,
                           resultados_busqueda=results)
    except Exception as e:
        return render_template('index.html', error=str(e))


@app.route('/ver-resultados', methods=['POST'])
def ver_resultados():
    """Ver todos los resultados en nueva página"""
    try:
        query = request.form.get('query', '')
        tipo = request.form.get('tipo', 'todos')
        
        if not RAG_AVAILABLE:
            return "RAG no disponible"
        
        search = REBT_Search()
        
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
            return render_template('index.html', error='Resolutor no disponible')
        
        resultado = resolver_ejercicio(pregunta)
        
        ayuda_rag = []
        if ayuda and RAG_AVAILABLE:
            search = REBT_Search()
            ayuda_rag = search.buscar_ejercicios(pregunta)[:3]
        
        return render_template('index.html',
                           opcion='resolver',
                           pregunta=pregunta,
                           resultado_ejercicio=resultado,
                           ayuda_rag=ayuda_rag)
    except Exception as e:
        return render_template('index.html', error=str(e))


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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)