"""
Calculadora REBT - Aplicación Flask
 UF0884: Instalaciones de Enlace
 UF0885: Puestas a tierra
 UF0887: Instalaciones Interiores en Viviendas
 UF0888: Pública Concurrencia
"""

from flask import Flask, render_template, request, jsonify
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from engine_rebt import (
    calcular_circuitos_vivienda,
    calcular_edificio,
    calcular_lga,
    coef_simultaneidad,
    prevision_carga_viviendas,
    calcular_intensidad,
    calcular_seccion_cdt,
    calcular_seccion_por_intensidad,
    calcular_pia,
    calcular_tubo,
    normalizar_seccion,
    ResultadoCircuito,
    ResultadoDI,
    ResultadoLGA
)
from schemes import generar_esquema_vivienda, generar_esquema_edificio

app = Flask(__name__)

# ============================================================
# RUTAS PRINCIPALES
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')


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
        cdt = 3 if tipo_instalacion == 'vivienda' else 5
        seccion_cdt = calcular_seccion_cdt(potencia, longitud, cdt, tension, fp)
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
                             'cdt_max': cdt
                         })
    except Exception as e:
        return render_template('index.html', error=str(e))


@app.route('/calcular-di', methods=['POST'])
def calcular_di():
    """Cálculo de derivación individual"""
    try:
        potencia = float(request.form.get('potencia', 5000))
        longitud = float(request.form.get('longitud', 15))
        tension = float(request.form.get('tension', 230))
        es_trifasica = request.form.get('es_trifasica') == 'on'
        
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)