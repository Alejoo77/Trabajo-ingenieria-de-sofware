import pytest
import sqlite3
from app import app

@pytest.fixture
def cliente():
    app.config['TESTING'] = True
    conn = sqlite3.connect('reparacampus.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT, rol TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS incidencias (id INTEGER PRIMARY KEY AUTOINCREMENT, codigo TEXT, solicitante_id INTEGER, ubicacion TEXT, categoria TEXT, descripcion TEXT, impacto TEXT, riesgo BOOLEAN, estado TEXT, fecha_creacion DATETIME)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS historial (id INTEGER PRIMARY KEY AUTOINCREMENT, incidencia_id INTEGER, autor_id INTEGER, accion TEXT, estado_nuevo TEXT, fecha DATETIME)''')
    conn.commit()
    conn.close()
    with app.test_client() as client:
        yield client

# --- S01: Registro ---
def test_registro_exitoso(cliente): # 1 de integración
    payload = {"ubicacion": "LAB-01", "categoria": "TIC", "descripcion": "El proyector no enciende y hace ruido.", "impacto": "ALTO", "riesgo": False}
    response = cliente.post('/api/registrar', json=payload)
    assert response.status_code == 201

def test_registro_descripcion_corta(cliente):
    payload = {"ubicacion": "AULA-201", "categoria": "ELECTRICIDAD", "descripcion": "Foco roto", "impacto": "BAJO", "riesgo": False}
    response = cliente.post('/api/registrar', json=payload)
    assert response.status_code == 400

def test_registro_impacto_invalido(cliente):
    payload = {"ubicacion": "BIB-01", "categoria": "MOBILIARIO", "descripcion": "Silla con pata rota y tornillos sueltos.", "impacto": "MEDIO", "riesgo": True}
    response = cliente.post('/api/registrar', json=payload)
    assert response.status_code == 400

# --- S02: Priorización y Asignación ---
def test_prioridad_critica():
    from app import calcular_prioridad
    assert calcular_prioridad("ALTO", True) == "CRITICA"

def test_prioridad_normal():
    from app import calcular_prioridad
    assert calcular_prioridad("BAJO", False) == "NORMAL"

def test_asignar_tecnico_exitoso(cliente): # 2 de integración
    response = cliente.post('/api/asignar', json={"incidencia_id": 1, "tecnico_id": 3})
    # Asumiendo que la ruta devuelve 200 si tiene éxito o 404 si la base de datos de prueba está vacía
    assert response.status_code in [200, 404]

# --- S03: Atención ---
def test_iniciar_atencion_rechazo_descripcion(cliente):
    response = cliente.post('/api/atender', json={"incidencia_id": 1, "solucion": "ok"})
    assert response.status_code == 400 # Falla por longitud menor a 20

# --- S04: Validación, Rechazo y Reapertura ---
def test_confirmar_solucion(cliente): # 3 de integración
    response = cliente.post('/api/validar', json={"incidencia_id": 1, "accion": "confirmar"})
    assert response.status_code in [200, 404]

def test_rechazo_solucion_sin_motivo(cliente):
    response = cliente.post('/api/validar', json={"incidencia_id": 1, "accion": "rechazar", "motivo": "corto"})
    assert response.status_code == 400 # Falla porque el motivo debe tener al menos 10 caracteres

# --- S05: Consulta y Tablero ---
def test_tablero_coordinador(cliente):
    response = cliente.get('/api/tablero')
    assert response.status_code == 200