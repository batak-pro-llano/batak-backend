import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import mysql.connector

app = FastAPI(title="API Batak System")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/app", response_class=FileResponse)
def leer_app():
    return FileResponse("static/index.html")

def get_db_connection():
    return mysql.connector.connect(
        host="mysql-3873d10f-batak.h.aivencloud.com",
        port=28819,
        user="avnadmin",
        password=os.environ.get("DB_PASSWORD", "AVNS_slRn8ktsJbpkE7hlO-q"),
        database="defaultdb",
        ssl_disabled=False,
        use_pure=True
    )

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
    nivel: int = 1
    tiempo: str = "0s"

@app.post("/api/registro")
def registrar_usuario(usuario: UsuarioRegistro):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (usuario.email,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="El email ya está registrado")
            
        codigo_qr_unico = f"BATAK-{uuid.uuid4().hex[:8].upper()}"
            
        query = "INSERT INTO usuarios (nombre, email, password, CODIGO_QR) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (usuario.nombre, usuario.email, usuario.password, codigo_qr_unico))
        conn.commit()
        
        usuario_id = cursor.lastrowid
        conn.close()
        
        return {
            "mensaje": "Usuario registrado exitosamente", 
            "id": usuario_id,
            "nombre": usuario.nombre,
            "email": usuario.email,
            "qr_code": codigo_qr_unico
        }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error en BBDD: {err}")

@app.post("/api/login")
def login_usuario(usuario: UsuarioLogin):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT id, nombre, email, CODIGO_QR FROM usuarios WHERE email = %s AND password = %s"
        cursor.execute(query, (usuario.email, usuario.password))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")
            
        return {
            "mensaje": "Inicio de sesión exitoso", 
            "id": user["id"],
            "nombre": user["nombre"],
            "email": user["email"],
            "qr_code": user["CODIGO_QR"]
        }
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error en BBDD: {err}")

@app.post("/api/validar-qr")
def validar_qr(data: ValidacionQR):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = "SELECT id, nombre, email FROM usuarios WHERE CODIGO_QR = %s OR email = %s"
        cursor.execute(query, (data.qr_code, data.qr_code))
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
        
        query = "INSERT INTO partidas (ID_USUARIO, POINT, NIVEL, TIEMPO_SEG) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (partida.usuario_id, partida.puntaje, partida.nivel, partida.tiempo))
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
        
        query = "SELECT ID, POINT, NIVEL, TIEMPO_SEG, FECHA_PARTIDA FROM partidas WHERE ID_USUARIO = %s ORDER BY FECHA_PARTIDA DESC"
        cursor.execute(query, (usuario_id,))
        partidas = cursor.fetchall()
        conn.close()
        
        return {"partidas": partidas}
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Error en BBDD: {err}")