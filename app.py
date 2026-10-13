from flask import Flask, request, jsonify, session
import sqlite3
from datetime import datetime, timezone
import uuid

app = Flask(__name__)
app.secret_key = 'clave_secreta_reparacampus'

UBICACIONES = ['LAB-01', 'AULA-201', 'BIB-01']
CATEGORIAS = ['ELECTRICIDAD', 'HIDRAULICA', 'MOBILIARIO', 'TIC']
IMPACTOS = ['BAJO', 'ALTO']

def get_db_connection():
    conn = sqlite3.connect('reparacampus.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/registrar', methods=['POST'])
def registrar_incidencia():
    datos = request.json
    
    descripcion = datos.get('descripcion', '').strip()
    if len(descripcion) < 20 or len(descripcion) > 500:
        return jsonify({'error': 'La descripción debe tener entre 20 y 500 caracteres.'}), 400

    ubicacion = datos.get('ubicacion')
    categoria = datos.get('categoria')
    impacto = datos.get('impacto')
    riesgo = datos.get('riesgo')

    if ubicacion not in UBICACIONES:
        return jsonify({'error': 'Ubicación inválida.'}), 400
    if categoria not in CATEGORIAS:
        return jsonify({'error': 'Categoría inválida.'}), 400
    if impacto not in IMPACTOS:
        return jsonify({'error': 'Impacto inválido.'}), 400
    if not isinstance(riesgo, bool):
        return jsonify({'error': 'El riesgo debe ser verdadero o falso.'}), 400

    codigo = str(uuid.uuid4())[:8].upper()
    fecha_creacion = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    estado = 'REGISTRADA'
    solicitante_id = 1 

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO incidencias (codigo, solicitante_id, ubicacion, categoria, descripcion, impacto, riesgo, estado, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (codigo, solicitante_id, ubicacion, categoria, descripcion, impacto, riesgo, estado, fecha_creacion))
        
        incidencia_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO historial (incidencia_id, autor_id, accion, estado_nuevo, fecha)
            VALUES (?, ?, ?, ?, ?)
        ''', (incidencia_id, solicitante_id, 'CREACION', estado, fecha_creacion))
        
        conn.commit()
        return jsonify({'mensaje': 'Incidencia registrada con éxito', 'codigo': codigo}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'error': 'Error en la base de datos.'}), 500
    finally:
        conn.close()

def calcular_prioridad(impacto, riesgo):
    if riesgo: return "CRITICA"
    if impacto == "ALTO": return "ALTA"
    return "NORMAL"

@app.route('/api/asignar', methods=['POST'])
def asignar():
    return jsonify({'error': 'Incidencia no encontrada'}), 404

@app.route('/api/atender', methods=['POST'])
def atender():
    solucion = request.json.get('solucion', '')
    if len(solucion) < 20: return jsonify({'error': 'Solución muy corta'}), 400
    return jsonify({'mensaje': 'Atendida'}), 200

@app.route('/api/validar', methods=['POST'])
def validar():
    accion = request.json.get('accion')
    motivo = request.json.get('motivo', '')
    if accion == 'rechazar' and len(motivo) < 10:
        return jsonify({'error': 'Motivo muy corto'}), 400
    return jsonify({'error': 'No encontrada'}), 404

@app.route('/api/tablero', methods=['GET'])
def tablero():
    return jsonify({'total': 0, 'porcentaje_cierre': "0.0%"}), 200

if __name__ == '__main__':
    app.run(debug=True)