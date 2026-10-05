from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import mysql.connector
import uuid

app = FastAPI(title="API Batak System")

# Servir la carpeta de archivos estáticos (HTML/CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/app", response_class=FileResponse)
def leer_app():
    return FileResponse("static/index.html")


# Configuración de la conexión a MySQL en Aiven.io
def get_db_connection():
    return mysql.connector.connect(
        host="mysql-3873d10f-batak.h.aivencloud.com", #[cite: 11]
        port=28819,                                   #[cite: 11]
        user="avnadmin",                              #[cite: 11]
        password="AVNS_slRn8ktsJbPkE7hlO-q",          #[cite: 11]
        database="defaultdb",                         #[cite: 11]
        ssl_mode="REQUIRED"                            # Requerido por Aiven[cite: 11]
    )

# Modelos de datos de entrada
class UsuarioRegistro(BaseModel):
    nombre: str
    email: str
    password: str

class UsuarioLogin(BaseModel):
    email: str
    password: str

class ValidarQRRequest(BaseModel):
    codigo_qr: str

class GuardarPartidaRequest(BaseModel):
    usuario_id: int | None = None
    nivel: int
    puntos: int
    tiempo_segundos: float


# --- ENDPOINTS DE LA API ---

@app.get("/")
def inicio():
    return {"status": "ok", "mensaje": "API Batak en ejecución"}


# 1. REGISTRO DE USUARIO
@app.post("/api/registro")
def registrar_usuario(usuario: UsuarioRegistro):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        codigo_qr = f"BATAK-{uuid.uuid4().hex[:8].upper()}"
        
        sql = "INSERT INTO usuarios (NOMBRE, EMAIL, CONTRASEÑA, CÓDIGO_QR) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (usuario.nombre, usuario.email, usuario.password, codigo_qr))
        conn.commit()
        
        usuario_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return {
            "exito": True,
            "mensaje": "Usuario registrado correctamente",
            "usuario_id": usuario_id,
            "codigo_qr": codigo_qr
        }
    except mysql.connector.Error as err:
        if err.errno == 1062:
            raise HTTPException(status_code=400, detail="El correo ya está registrado.")
        raise HTTPException(status_code=500, detail=f"Error en BBDD: {err}")


# 2. INICIO DE SESIÓN
@app.post("/api/login")
def iniciar_sesion(usuario: UsuarioLogin):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        sql = "SELECT ID, NOMBRE, EMAIL, CÓDIGO_QR FROM usuarios WHERE EMAIL = %s AND CONTRASEÑA = %s"
        cursor.execute(sql, (usuario.email, usuario.password))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if user:
            return {
                "exito": True,
                "mensaje": "Inicio de sesión correcto",
                "usuario": user
            }
        else:
            raise HTTPException(status_code=400, detail="Correo o contraseña incorrectos")
            
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error en BBDD: {err}")


# 3. VALIDACIÓN DE CÓDIGO QR (Para la consola Batak)
@app.post("/api/validar-qr")
def validar_qr(data: ValidarQRRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        sql = "SELECT ID, NOMBRE, EMAIL, CÓDIGO_QR FROM usuarios WHERE CÓDIGO_QR = %s"
        cursor.execute(sql, (data.codigo_qr,))
        usuario = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if usuario:
            return {
                "valido": True,
                "mensaje": "Usuario encontrado",
                "usuario": usuario
            }
        else:
            return {
                "valido": False,
                "mensaje": "El código QR no pertenece a ningún usuario registrado"
            }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error en BBDD: {err}")


# 4. GUARDAR RESULTADOS DE PARTIDA
@app.post("/api/guardar-partida")
def guardar_partida(partida: GuardarPartidaRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = "INSERT INTO partidas (ID_USUARIO, NIVEL, POINT, TIEMPO_SEG) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (partida.usuario_id, partida.nivel, partida.puntos, partida.tiempo_segundos))
        conn.commit()
        
        partida_id = cursor.lastrowid
        cursor.close()
        conn.close()
        
        return {
            "exito": True,
            "mensaje": "Partida registrada exitosamente",
            "partida_id": partida_id
        }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error en BBDD: {err}")


# 5. CONSULTAR HISTORIAL DE PARTIDAS DE UN USUARIO
@app.get("/api/historial/{usuario_id}")
def obtener_historial(usuario_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        sql = """
            SELECT ID, NIVEL, POINT, TIEMPO_SEG, FECHHA_PARTIDA 
            FROM partidas 
            WHERE ID_USUARIO = %s 
            ORDER BY FECHHA_PARTIDA DESC
        """
        cursor.execute(sql, (usuario_id,))
        historial = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "exito": True,
            "total": len(historial),
            "historial": historial
        }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error en BBDD: {err}")