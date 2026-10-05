from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import mysql.connector

app = FastAPI(title="API Batak System")

# Servir la carpeta de archivos estáticos (HTML/CSS/JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/app", response_class=FileResponse)
def leer_app():
    return FileResponse("static/index.html")

# Configuración de la conexión a MySQL en Aiven.io
def get_db_connection():
    return mysql.connector.connect(
        host="mysql-3873d10f-batak.h.aivencloud.com",
        port=28819,
        user="avnadmin",
        password=os.environ.get("DB_PASSWORD"),
        database="defaultdb",
        ssl_disabled=False
        use_pure=True
    )

# Modelos de datos de entrada
class UsuarioRegistro(BaseModel):
    nombre: str
    email: str
    password: str

class UsuarioLogin(BaseModel):
    email: str
    password: str

class ValidacionQR(BaseModel):
    qr_code: str

class PartidaGuardar(BaseModel):
    usuario_id: int
    puntaje: int

# Rutas de la API
@app.post("/api/registro")
def registrar_usuario(usuario: UsuarioRegistro):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Verificar si el email ya existe
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (usuario.email,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="El email ya está registrado")
            
        # Insertar nuevo usuario
        query = "INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)"
        cursor.execute(query, (usuario.nombre, usuario.email, usuario.password))
        conn.commit()
        
        usuario_id = cursor.lastrowid
        conn.close()
        
        return {"mensaje": "Usuario registrado exitosamente", "id": usuario_id}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error en BBDD: {err}")

@app.post("/api/login")
def login_usuario(usuario: UsuarioLogin):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT id, nombre, email FROM usuarios WHERE email = %s AND password = %s"
        cursor.execute(query, (usuario.email, usuario.password))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
            
        return {"mensaje": "Inicio de sesión exitoso", "usuario": user}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error en BBDD: {err}")

@app.post("/api/validar-qr")
def validar_qr(data: ValidacionQR):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT id, nombre, email FROM usuarios WHERE email = %s"
        cursor.execute(query, (data.qr_code,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return {"valido": False, "mensaje": "Código QR no válido o usuario no existe"}
            
        return {"valido": True, "usuario": user}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error en BBDD: {err}")

@app.post("/api/guardar-partida")
def guardar_partida(partida: PartidaGuardar):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "INSERT INTO partidas (usuario_id, puntaje) VALUES (%s, %s)"
        cursor.execute(query, (partida.usuario_id, partida.puntaje))
        conn.commit()
        conn.close()
        
        return {"mensaje": "Partida guardada exitosamente"}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error en BBDD: {err}")

@app.get("/api/historial/{usuario_id}")
def obtener_historial(usuario_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT id, puntaje, fecha FROM partidas WHERE usuario_id = %s ORDER BY fecha DESC"
        cursor.execute(query, (usuario_id,))
        partidas = cursor.fetchall()
        conn.close()
        
        return {"partidas": partidas}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error en BBDD: {err}")