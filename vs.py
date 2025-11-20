# Segundo proyecto de introducción a la programación - Escapa del Laberinto
# Isaac Orozco y Daniel Araya
#

# Imports estándar de Python
import random
import time
import json
import os
import datetime
from collections import deque, namedtuple

# Imports de tkinter 
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

FILAS = 12
COLUMNAS = 18

NUM_ENEMIGOS = 3
TIEMPO_REAPARICION_ENEMIGO = 10  # segundos
COOLDOWN_TRAMPA = 5  # segundos entre colocaciones
MAX_TRAMPAS_ACTIVAS = 3

COSTO_CORRER_POR_MOVIMIENTO = 10
RECUPERACION_ENERGIA_POR_TURNO = 5
ENERGIA_MAXIMA = 100

ARCHIVO_PUNTAJES_ESCAPA = "puntajes_escapa.txt"
ARCHIVO_PUNTAJES_CAZADOR = "puntajes_cazador.txt"

Punto = namedtuple("Punto", ["r", "c"])


def dentro(r, c):  # Verifica si una posición está dentro del mapa
    return 0 <= r < FILAS and 0 <= c < COLUMNAS


# CLASES DE CASILLAS

class Casilla:  # CLASE BASE

    simbolo = "?"

    def accesible_por_jugador(self):
        return False

    def accesible_por_enemigo(self):
        return False

    def __str__(self):
        return self.simbolo


class Camino(Casilla):
    simbolo = "."

    def accesible_por_jugador(self): return True

    def accesible_por_enemigo(self): return True


class Liana(Casilla):
    simbolo = "L"

    def accesible_por_jugador(self): return False

    def accesible_por_enemigo(self): return True


class Tunel(Casilla):
    simbolo = "T"

    def accesible_por_jugador(self): return True

    def accesible_por_enemigo(self): return False


class Muro(Casilla):
    simbolo = "#"

    def accesible_por_jugador(self): return False

    def accesible_por_enemigo(self): return False


class Salida(Casilla):
    simbolo = "S"

    def accesible_por_jugador(self): return True

    def accesible_por_enemigo(self): return False  # Los cazadores no pueden usar las salidas


class Trampa(Casilla):
    def __init__(self):
        self.activa = True
        self.tiempo_colocacion = time.time()

    simbolo = "X"

    def accesible_por_jugador(self): return True

    def accesible_por_enemigo(self): return True

    def activar_trampa(self):
        """Activa la trampa cuando un enemigo la toca"""
        self.activa = False
        return True  # Indica que el enemigo debe ser eliminado


# ----------------- GENERADOR DE MAPA -----------------
class GeneradorMapa:
    def __init__(self, filas=FILAS, columnas=COLUMNAS):
        self.filas = filas
        self.columnas = columnas
        self.mapa = []
        self.posicion_jugador = None
        self.salidas = []

    def generar_mapa_aleatorio(self):
        """Genera un mapa aleatorio con camino garantizado a la salida"""
        # Inicializar mapa con muros
        self.mapa = [[Muro() for _ in range(self.columnas)] for _ in range(self.filas)]

        # Generar caminos usando algoritmo de laberinto
        self._generar_laberinto()

        # Agregar elementos especiales
        self._agregar_lianas()
        self._agregar_tuneles()
        self._colocar_salidas()
        self._colocar_jugador()

        return self.mapa

    def _generar_laberinto(self):
        """Genera caminos usando algoritmo de búsqueda en profundidad"""
        # Stack para DFS
        stack = []
        visitados = set()

        # Empezar desde una posición aleatoria (debe ser impar para el algoritmo)
        inicio_r = random.randrange(1, self.filas - 1, 2)
        inicio_c = random.randrange(1, self.columnas - 1, 2)

        stack.append((inicio_r, inicio_c))
        self.mapa[inicio_r][inicio_c] = Camino()
        visitados.add((inicio_r, inicio_c))

        direcciones = [(0, 2), (2, 0), (0, -2), (-2, 0)]  # Derecha, Abajo, Izquierda, Arriba

        while stack:
            actual_r, actual_c = stack[-1]

            # Buscar vecinos no visitados
            vecinos = []
            for dr, dc in direcciones:
                nuevo_r, nuevo_c = actual_r + dr, actual_c + dc
                if (0 < nuevo_r < self.filas - 1 and
                        0 < nuevo_c < self.columnas - 1 and
                        (nuevo_r, nuevo_c) not in visitados):
                    vecinos.append((nuevo_r, nuevo_c))

            if vecinos:
                # Elegir vecino aleatorio
                siguiente_r, siguiente_c = random.choice(vecinos)

                # Crear camino entre actual y siguiente
                pared_r = actual_r + (siguiente_r - actual_r) // 2
                pared_c = actual_c + (siguiente_c - actual_c) // 2

                self.mapa[pared_r][pared_c] = Camino()
                self.mapa[siguiente_r][siguiente_c] = Camino()

                visitados.add((siguiente_r, siguiente_c))
                stack.append((siguiente_r, siguiente_c))
            else:
                stack.pop()

        # Agregar caminos adicionales para hacer el laberinto menos lineal
        self._agregar_caminos_adicionales()

    def _agregar_caminos_adicionales(self):
        """Agrega caminos adicionales para hacer el mapa más interesante"""
        num_caminos_extra = random.randint(5, 15)

        for _ in range(num_caminos_extra):
            r = random.randint(1, self.filas - 2)
            c = random.randint(1, self.columnas - 2)

            # Solo convertir muros que tengan al menos un camino adyacente
            if isinstance(self.mapa[r][c], Muro):
                caminos_adyacentes = 0
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if (dentro(nr, nc) and
                            isinstance(self.mapa[nr][nc], Camino)):
                        caminos_adyacentes += 1

                if caminos_adyacentes >= 1:
                    self.mapa[r][c] = Camino()

    def _agregar_lianas(self):
        """Agrega lianas en posiciones estratégicas"""
        num_lianas = random.randint(8, 15)

        for _ in range(num_lianas):
            r = random.randint(0, self.filas - 1)
            c = random.randint(0, self.columnas - 1)

            if isinstance(self.mapa[r][c], Muro):
                # Verificar que tenga al menos un camino cercano
                tiene_camino_cercano = False
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        nr, nc = r + dr, c + dc
                        if (dentro(nr, nc) and
                                isinstance(self.mapa[nr][nc], Camino)):
                            tiene_camino_cercano = True
                            break
                    if tiene_camino_cercano:
                        break

                if tiene_camino_cercano:
                    self.mapa[r][c] = Liana()

    def _agregar_tuneles(self):
        """Agrega túneles para dar ventaja al jugador"""
        num_tuneles = random.randint(5, 10)

        for _ in range(num_tuneles):
            r = random.randint(0, self.filas - 1)
            c = random.randint(0, self.columnas - 1)

            if isinstance(self.mapa[r][c], Muro):
                self.mapa[r][c] = Tunel()

    def _colocar_salidas(self):
        """Coloca salidas en los bordes del mapa asegurando que tengan acceso"""
        self.salidas = []
        num_salidas = random.randint(2, 4)

        # Posibles posiciones de salida (bordes)
        posiciones_validas = []

        # Borde superior e inferior
        for c in range(1, self.columnas - 1):  # Evitar esquinas
            # Borde superior - verificar si hay camino adyacente
            if isinstance(self.mapa[1][c], Camino):
                posiciones_validas.append((0, c))
            # Borde inferior - verificar si hay camino adyacente
            if isinstance(self.mapa[self.filas - 2][c], Camino):
                posiciones_validas.append((self.filas - 1, c))

        # Borde izquierdo y derecho
        for r in range(1, self.filas - 1):
            # Borde izquierdo - verificar si hay camino adyacente
            if isinstance(self.mapa[r][1], Camino):
                posiciones_validas.append((r, 0))
            # Borde derecho - verificar si hay camino adyacente
            if isinstance(self.mapa[r][self.columnas - 2], Camino):
                posiciones_validas.append((r, self.columnas - 1))

        # Si no hay suficientes posiciones válidas, crear caminos hacia el borde
        if len(posiciones_validas) < num_salidas:
            self._crear_caminos_hacia_bordes()
            # Volver a evaluar posiciones válidas
            posiciones_validas = []
            for c in range(1, self.columnas - 1):
                if isinstance(self.mapa[1][c], Camino):
                    posiciones_validas.append((0, c))
                if isinstance(self.mapa[self.filas - 2][c], Camino):
                    posiciones_validas.append((self.filas - 1, c))
            for r in range(1, self.filas - 1):
                if isinstance(self.mapa[r][1], Camino):
                    posiciones_validas.append((r, 0))
                if isinstance(self.mapa[r][self.columnas - 2], Camino):
                    posiciones_validas.append((r, self.columnas - 1))

        # Elegir posiciones aleatorias para las salidas
        num_salidas_real = min(num_salidas, len(posiciones_validas))
        if num_salidas_real > 0:
            salidas_elegidas = random.sample(posiciones_validas, num_salidas_real)
            for r, c in salidas_elegidas:
                self.mapa[r][c] = Salida()
                self.salidas.append(Punto(r, c))

    def _crear_caminos_hacia_bordes(self):
        """Crea caminos desde el interior hacia los bordes para asegurar salidas accesibles"""
        # Encontrar caminos en el interior
        caminos_interiores = []
        for r in range(2, self.filas - 2):
            for c in range(2, self.columnas - 2):
                if isinstance(self.mapa[r][c], Camino):
                    caminos_interiores.append((r, c))
        
        # Crear algunos caminos hacia los bordes
        if caminos_interiores:
            for _ in range(3):  # Crear hasta 3 caminos hacia bordes
                r, c = random.choice(caminos_interiores)
                
                # Elegir dirección hacia un borde
                direcciones = []
                if r > self.filas // 2:  # Más cerca del borde inferior
                    direcciones.append((1, 0))  # Hacia abajo
                else:  # Más cerca del borde superior
                    direcciones.append((-1, 0))  # Hacia arriba
                    
                if c > self.columnas // 2:  # Más cerca del borde derecho
                    direcciones.append((0, 1))  # Hacia derecha
                else:  # Más cerca del borde izquierdo
                    direcciones.append((0, -1))  # Hacia izquierda
                
                # Crear camino en la dirección elegida
                if direcciones:
                    dr, dc = random.choice(direcciones)
                    actual_r, actual_c = r, c
                    
                    # Crear camino hasta llegar cerca del borde
                    while (1 < actual_r < self.filas - 2 and 
                           1 < actual_c < self.columnas - 2):
                        actual_r += dr
                        actual_c += dc
                        if isinstance(self.mapa[actual_r][actual_c], Muro):
                            self.mapa[actual_r][actual_c] = Camino()

    def _colocar_jugador(self):
        """Encuentra una posición válida para el jugador"""
        # Buscar una posición de camino que no esté muy cerca de las salidas
        intentos = 0
        max_intentos = 100

        while intentos < max_intentos:
            r = random.randint(1, self.filas - 2)
            c = random.randint(1, self.columnas - 2)

            if isinstance(self.mapa[r][c], Camino):
                # Verificar que no esté muy cerca de una salida
                muy_cerca_salida = False
                for salida in self.salidas:
                    distancia = abs(r - salida.r) + abs(c - salida.c)
                    if distancia < 3:  # Mínimo 3 casillas de distancia
                        muy_cerca_salida = True
                        break

                if not muy_cerca_salida:
                    self.posicion_jugador = Punto(r, c)
                    return

            intentos += 1

        # Si no se encuentra una buena posición, usar cualquier camino
        for r in range(self.filas):
            for c in range(self.columnas):
                if isinstance(self.mapa[r][c], Camino):
                    self.posicion_jugador = Punto(r, c)
                    return

    def verificar_camino_valido(self):
        """Verifica que existe al menos un camino válido desde el jugador hasta una salida"""
        if not self.posicion_jugador or not self.salidas:
            return False

        # BFS para encontrar camino
        queue = deque([self.posicion_jugador])
        visitados = {self.posicion_jugador}

        direcciones = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        while queue:
            actual = queue.popleft()

            # Verificar si llegamos a una salida
            if actual in self.salidas:
                return True

            # Explorar vecinos
            for dr, dc in direcciones:
                nr, nc = actual.r + dr, actual.c + dc
                nuevo_punto = Punto(nr, nc)

                if (dentro(nr, nc) and
                        nuevo_punto not in visitados and
                        self.mapa[nr][nc].accesible_por_jugador()):
                    visitados.add(nuevo_punto)
                    queue.append(nuevo_punto)

        return False

    def mostrar_mapa(self):
        """Muestra el mapa en consola para depuración"""
        for r in range(self.filas):
            fila = ""
            for c in range(self.columnas):
                if self.posicion_jugador and r == self.posicion_jugador.r and c == self.posicion_jugador.c:
                    fila += "J "
                else:
                    fila += self.mapa[r][c].simbolo + " "
            print(fila)
        print()


# ----------------- FUNCIÓN PRINCIPAL DE GENERACIÓN -----------------
def generar_mapa_juego():
    """Genera un mapa válido para el juego"""
    max_intentos = 10

    for intento in range(max_intentos):
        generador = GeneradorMapa()
        mapa = generador.generar_mapa_aleatorio()

        # Verificar que el mapa es válido
        if generador.verificar_camino_valido():
            print(f"Mapa generado exitosamente en el intento {intento + 1}")
            return generador
        else:
            print(f"Intento {intento + 1} falló - regenerando mapa...")

    # Si no se pudo generar un mapa válido, crear uno simple
    print("Generando mapa simple como respaldo...")
    return _generar_mapa_simple()


def _generar_mapa_simple():
    """Genera un mapa simple garantizado como respaldo"""
    generador = GeneradorMapa()

    # Crear mapa simple con caminos en forma de cruz
    for r in range(generador.filas):
        for c in range(generador.columnas):
            if r == generador.filas // 2 or c == generador.columnas // 2:
                generador.mapa[r][c] = Camino()
            else:
                generador.mapa[r][c] = Muro()

    # Colocar salidas en las esquinas
    generador.mapa[0][0] = Salida()
    generador.mapa[0][generador.columnas - 1] = Salida()
    generador.salidas = [Punto(0, 0), Punto(0, generador.columnas - 1)]

    # Colocar jugador en el centro
    generador.posicion_jugador = Punto(generador.filas // 2, generador.columnas // 2)

    return generador


# ----------------- UTILIDADES DEL MAPA -----------------
def obtener_posiciones_libres(mapa, tipo_casilla=None):
    """Obtiene todas las posiciones libres del mapa"""
    posiciones = []
    for r in range(len(mapa)):
        for c in range(len(mapa[0])):
            if tipo_casilla is None:
                if mapa[r][c].accesible_por_jugador():
                    posiciones.append(Punto(r, c))
            else:
                if isinstance(mapa[r][c], tipo_casilla):
                    posiciones.append(Punto(r, c))
    return posiciones


def obtener_posiciones_enemigos(mapa, num_enemigos=NUM_ENEMIGOS, posicion_jugador=None):
    """Obtiene posiciones aleatorias válidas para colocar enemigos, evitando la posición del jugador"""
    posiciones_libres = obtener_posiciones_libres(mapa, Camino)
    
    # Si se proporciona posición del jugador, filtrar posiciones muy cercanas
    if posicion_jugador:
        posiciones_validas = []
        for pos in posiciones_libres:
            # Calcular distancia Manhattan
            distancia = abs(pos.r - posicion_jugador.r) + abs(pos.c - posicion_jugador.c)
            if distancia >= 4:  # Mínimo 4 casillas de distancia del jugador
                posiciones_validas.append(pos)
        posiciones_libres = posiciones_validas if posiciones_validas else posiciones_libres

    if len(posiciones_libres) < num_enemigos:
        return posiciones_libres  # Devolver todas las disponibles

    return random.sample(posiciones_libres, num_enemigos)


def es_posicion_valida(mapa, r, c, es_jugador=True):
    """Verifica si una posición es válida para movimiento"""
    if not dentro(r, c):
        return False

    if es_jugador:
        return mapa[r][c].accesible_por_jugador()
    else:
        return mapa[r][c].accesible_por_enemigo()


def colocar_trampa(mapa, r, c):
    """Coloca una trampa en la posición especificada"""
    if (dentro(r, c) and
            isinstance(mapa[r][c], Camino)):
        mapa[r][c] = Trampa()
        return True
    return False


def remover_trampa(mapa, r, c):
    """Remueve una trampa y la convierte de vuelta en camino"""
    if (dentro(r, c) and
            isinstance(mapa[r][c], Trampa)):
        mapa[r][c] = Camino()
        return True
    return False


# ----------------- CLASE JUGADOR -----------------
class Jugador:
    def __init__(self, posicion):
        self.posicion = posicion
        self.energia = ENERGIA_MAXIMA
        self.trampas_activas = 0
        self.ultimo_uso_trampa = 0
        self.puntaje = 0
        self.vivo = True

    def mover(self, mapa, nueva_r, nueva_c, corriendo=False):
        """Mueve el jugador a una nueva posición"""
        if not es_posicion_valida(mapa, nueva_r, nueva_c, es_jugador=True):
            return False

        if corriendo:
            if self.energia >= COSTO_CORRER_POR_MOVIMIENTO:
                self.energia -= COSTO_CORRER_POR_MOVIMIENTO
            else:
                return False  # No hay suficiente energía para correr

        self.posicion = Punto(nueva_r, nueva_c)
        return True

    def recuperar_energia(self):
        """Recupera energía por turno"""
        self.energia = min(self.energia + RECUPERACION_ENERGIA_POR_TURNO, ENERGIA_MAXIMA)

    def puede_colocar_trampa(self):
        """Verifica si puede colocar una trampa"""
        tiempo_actual = time.time()
        return (self.trampas_activas < MAX_TRAMPAS_ACTIVAS and
                tiempo_actual - self.ultimo_uso_trampa >= COOLDOWN_TRAMPA)

    def colocar_trampa_en_mapa(self, mapa):
        """Coloca una trampa en la posición actual del jugador"""
        if self.puede_colocar_trampa():
            if colocar_trampa(mapa, self.posicion.r, self.posicion.c):
                self.trampas_activas += 1
                self.ultimo_uso_trampa = time.time()
                return True
        return False


# ----------------- CLASE ENEMIGO -----------------
class Enemigo:
    def __init__(self, posicion):
        self.posicion = posicion
        self.vivo = True
        self.tiempo_muerte = 0
        self.escapo = False   # 👈 Nuevo flag


    def mover_hacia_objetivo(self, mapa, objetivo, huir=False):
        """Mueve el enemigo hacia o lejos del objetivo usando pathfinding simple"""
        if not self.vivo:
            return False

        mejor_movimiento = None
        # Si huye: iniciar con -inf para buscar la mayor distancia
        # Si persigue: iniciar con inf para buscar la menor distancia
        mejor_distancia = float('-inf') if huir else float('inf')

        direcciones = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        for dr, dc in direcciones:
            nueva_r = self.posicion.r + dr
            nueva_c = self.posicion.c + dc

            if es_posicion_valida(mapa, nueva_r, nueva_c, es_jugador=False):
                # Calcular distancia Manhattan al objetivo
                distancia = abs(nueva_r - objetivo.r) + abs(nueva_c - objetivo.c)

                if huir:
                    # Si está huyendo, prefiere mayor distancia
                    if distancia > mejor_distancia:
                        mejor_distancia = distancia
                        mejor_movimiento = Punto(nueva_r, nueva_c)
                else:
                    # Si está persiguiendo, prefiere menor distancia
                    if distancia < mejor_distancia:
                        mejor_distancia = distancia
                        mejor_movimiento = Punto(nueva_r, nueva_c)

        if mejor_movimiento:
            self.posicion = mejor_movimiento
            return True

        return False

    def morir(self):
        """Marca al enemigo como muerto"""
        self.vivo = False
        self.tiempo_muerte = time.time()

    def puede_reaparecer(self):
        """Verifica si el enemigo puede reaparecer"""
        return (not self.vivo and
                time.time() - self.tiempo_muerte >= TIEMPO_REAPARICION_ENEMIGO)


# ----------------- FUNCIÓN DE PRUEBA -----------------
def probar_generacion_mapa():
    """Función para probar la generación del mapa"""
    print("=== PRUEBA DE GENERACIÓN DE MAPA ===")

    generador = generar_mapa_juego()

    print(f"Posición del jugador: {generador.posicion_jugador}")
    print(f"Salidas: {generador.salidas}")
    print(f"Camino válido encontrado: {generador.verificar_camino_valido()}")
    print("\nMapa generado:")
    generador.mostrar_mapa()

    # Probar colocación de enemigos
    posiciones_enemigos = obtener_posiciones_enemigos(generador.mapa)
    print(f"Posiciones para enemigos: {posiciones_enemigos}")

    # Crear jugador y enemigos de prueba
    jugador = Jugador(generador.posicion_jugador)
    enemigos = [Enemigo(pos) for pos in posiciones_enemigos]

    print(f"\nJugador creado en: {jugador.posicion}")
    print(f"Energía inicial: {jugador.energia}")
    print(f"Enemigos creados: {len(enemigos)}")


# ----------------- SISTEMA DE PUNTAJES -----------------
class SistemaPuntajes:
    def __init__(self):
        self.archivo_escapa = ARCHIVO_PUNTAJES_ESCAPA
        self.archivo_cazador = ARCHIVO_PUNTAJES_CAZADOR

    def cargar_puntajes(self, modo):
        """Carga los puntajes desde el archivo TXT correspondiente"""
        archivo = self.archivo_escapa if modo == "escapa" else self.archivo_cazador
        puntajes = []
        
        if os.path.exists(archivo):
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    for linea in f:
                        linea = linea.strip()
                        if linea and '|' in linea:
                            partes = linea.split('|')
                            if len(partes) >= 3:
                                nombre = partes[0].strip()
                                puntaje_str = partes[1].strip()
                                fecha = partes[2].strip()
                                
                                # Filtrar líneas de encabezado y separadores
                                if (nombre.lower() != 'nombre' and 
                                    not nombre.startswith('=') and 
                                    not nombre.startswith('-') and
                                    puntaje_str.isdigit()):
                                    try:
                                        puntaje = int(puntaje_str)
                                        puntajes.append({
                                            "nombre": nombre, 
                                            "puntaje": puntaje,
                                            "fecha": fecha
                                        })
                                    except ValueError:
                                        continue  # Saltar líneas con puntajes inválidos
            except Exception as e:
                print(f"Error cargando puntajes: {e}")
        
        return puntajes

    def guardar_puntajes(self, modo, puntajes):
        """Guarda los puntajes en el archivo TXT correspondiente"""
        archivo = self.archivo_escapa if modo == "escapa" else self.archivo_cazador
        
        try:
            with open(archivo, 'w', encoding='utf-8') as f:
                f.write(f"=== TOP 5 - MODO {modo.upper()} ===\n")
                f.write("Nombre | Puntaje | Fecha\n")
                f.write("-" * 40 + "\n")
                
                for puntaje_info in puntajes:
                    f.write(f"{puntaje_info['nombre']} | {puntaje_info['puntaje']} | {puntaje_info['fecha']}\n")
                    
        except Exception as e:
            print(f"Error guardando puntajes: {e}")

    def agregar_puntaje(self, nombre, puntaje, modo):
        """Agrega un nuevo puntaje y mantiene solo el top 5"""
        # Cargar puntajes existentes
        puntajes = self.cargar_puntajes(modo)
        
        # Agregar nuevo puntaje con fecha actual
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        nuevo_puntaje = {
            "nombre": nombre, 
            "puntaje": puntaje,
            "fecha": fecha_actual
        }
        
        puntajes.append(nuevo_puntaje)
        
        # Ordenar por puntaje (mayor a menor) y mantener solo top 5
        puntajes.sort(key=lambda x: x["puntaje"], reverse=True)
        puntajes = puntajes[:5]
        
        # Guardar de vuelta al archivo
        self.guardar_puntajes(modo, puntajes)

    def obtener_top5(self, modo):
        """Obtiene el top 5 de un modo específico"""
        return self.cargar_puntajes(modo)


# ----------------- INTERFAZ GRÁFICA -----------------
class JuegoLaberinto:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Escapa del Laberinto")
        self.root.geometry("1200x800")
        self.root.resizable(False, False)

        # Configuración del juego
        self.generador = None
        self.jugador = None
        self.enemigos = []
        self.modo_juego = None  # "escapa" o "cazador"
        self.nombre_jugador = ""
        self.tiempo_inicio = 0
        self.juego_activo = False
        self.juego_pausado = False
        self.contador_frames = 0  # Para controlar velocidad de enemigos

        # Sistema de puntajes
        self.sistema_puntajes = SistemaPuntajes()

        # Configuración visual
        self.TAMANO_CASILLA = 30
        self.colores = {
            "#": "#8B4513",  # Muro - Marron
            ".": "#90EE90",  # Camino - Verde claro
            "L": "#228B22",  # Liana - Verde oscuro
            "T": "#4169E1",  # Tunel - Azul
            "S": "#FFD700",  # Salida - Dorado
            "X": "#DC143C",  # Trampa - Rojo carmesi 
            "J": "#FF1493",  # Jugador - Rosa fuerte
            "E": "#8B0000",  # Enemigo - Rojo oscuro
        }

        self.crear_interfaz()
        self.mostrar_menu_principal()

    def crear_interfaz(self):
        """Crea la interfaz principal del juego"""
        # Frame principal
        self.frame_principal = tk.Frame(self.root)
        self.frame_principal.pack(fill=tk.BOTH, expand=True)

        # Frame del juego (izquierda)
        self.frame_juego = tk.Frame(self.frame_principal)
        self.frame_juego.pack(side=tk.LEFT, padx=10, pady=10)

        # Canvas para el mapa
        self.canvas = tk.Canvas(
            self.frame_juego,
            width=COLUMNAS * self.TAMANO_CASILLA,
            height=FILAS * self.TAMANO_CASILLA,
            bg="white",
            bd=2,
            relief="solid"
        )
        self.canvas.pack()

        # Frame de información (derecha)
        self.frame_info = tk.Frame(self.frame_principal, width=300)
        self.frame_info.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        self.frame_info.pack_propagate(False)

        # Información del jugador
        self.label_nombre = tk.Label(self.frame_info, text="Jugador: ", font=("Arial", 12, "bold"))
        self.label_nombre.pack(anchor="w", pady=5)

        self.label_modo = tk.Label(self.frame_info, text="Modo: ", font=("Arial", 10))
        self.label_modo.pack(anchor="w", pady=2)

        self.label_puntaje = tk.Label(self.frame_info, text="Puntaje: 0", font=("Arial", 10))
        self.label_puntaje.pack(anchor="w", pady=2)

        self.label_tiempo = tk.Label(self.frame_info, text="Tiempo: 0s", font=("Arial", 10))
        self.label_tiempo.pack(anchor="w", pady=2)

        # Barra de energía
        tk.Label(self.frame_info, text="Energía:", font=("Arial", 10)).pack(anchor="w", pady=(10, 2))
        self.barra_energia = ttk.Progressbar(
            self.frame_info, length=200, maximum=ENERGIA_MAXIMA, value=ENERGIA_MAXIMA
        )
        self.barra_energia.pack(anchor="w", pady=2)
        self.label_energia = tk.Label(self.frame_info, text=f"{ENERGIA_MAXIMA}/{ENERGIA_MAXIMA}", font=("Arial", 9))
        self.label_energia.pack(anchor="w")

        # Información de trampas (solo modo escapa)
        self.frame_trampas = tk.Frame(self.frame_info)
        self.frame_trampas.pack(anchor="w", pady=10)

        # Controles
        tk.Label(self.frame_info, text="Controles:", font=("Arial", 12, "bold")).pack(anchor="w", pady=(20, 5))
        controles_text = """
        WASD o Flechas: Mover
        Shift + Mover: Correr
        ESPACIO: Colocar trampa (Escapa)
        P: Pausar/Reanudar
        R: Reiniciar juego
        ESC: Menú principal
        """
        tk.Label(self.frame_info, text=controles_text, font=("Arial", 9), justify="left").pack(anchor="w")

        # Botones
        self.btn_pausar = tk.Button(
            self.frame_info, text="Pausar", command=self.pausar_juego,
            font=("Arial", 10), width=15
        )
        self.btn_pausar.pack(pady=5)

        self.btn_reiniciar = tk.Button(
            self.frame_info, text="Reiniciar Juego", command=self.reiniciar_juego,
            font=("Arial", 10), width=15
        )
        self.btn_reiniciar.pack(pady=5)

        self.btn_menu = tk.Button(
            self.frame_info, text="Menú Principal", command=self.mostrar_menu_principal,
            font=("Arial", 10), width=15
        )
        self.btn_menu.pack(pady=5)

        # Puntajes
        self.frame_puntajes = tk.Frame(self.frame_info)
        self.frame_puntajes.pack(fill=tk.BOTH, expand=True, pady=10)

        # Configurar eventos de teclado
        self.root.bind("<KeyPress>", self.manejar_tecla)
        self.root.focus_set()

    def mostrar_menu_principal(self):
        """Muestra el menú principal"""
        self.juego_activo = False
        self.canvas.delete("all")

        # Limpiar información
        self.label_nombre.config(text="Jugador: ")
        self.label_modo.config(text="Modo: ")
        self.label_puntaje.config(text="Puntaje: 0")
        self.label_tiempo.config(text="Tiempo: 0s")
        self.barra_energia.config(value=ENERGIA_MAXIMA)
        self.label_energia.config(text=f"{ENERGIA_MAXIMA}/{ENERGIA_MAXIMA}")

        # Dibujar menú en el canvas - ajustar posiciones para que todo sea visible
        canvas_width = COLUMNAS * self.TAMANO_CASILLA
        canvas_height = FILAS * self.TAMANO_CASILLA
        
        self.canvas.create_text(
            canvas_width // 2, 60,
            text="ESCAPA DEL LABERINTO",
            font=("Arial", 20, "bold"),
            fill="darkblue"
        )

        # Crear botones del menú - ajustar espaciado y posición
        btn_y = 120
        btn_spacing = 50
        btn_width = 140
        btn_height = 35
        btn_x = canvas_width // 2

        # Botón MODO ESCAPA
        self.canvas.create_rectangle(btn_x - btn_width//2, btn_y - btn_height//2, 
                                   btn_x + btn_width//2, btn_y + btn_height//2, 
                                   fill="lightblue", outline="darkblue", width=2)
        self.canvas.create_text(btn_x, btn_y, text="MODO ESCAPA", font=("Arial", 11, "bold"))
        self.canvas.tag_bind("modo_escapa", "<Button-1>", lambda e: self.iniciar_juego("escapa"))
        self.canvas.create_rectangle(btn_x - btn_width//2, btn_y - btn_height//2, 
                                   btn_x + btn_width//2, btn_y + btn_height//2, 
                                   tags="modo_escapa", fill="", outline="")

        btn_y += btn_spacing
        # Botón MODO CAZADOR
        self.canvas.create_rectangle(btn_x - btn_width//2, btn_y - btn_height//2, 
                                   btn_x + btn_width//2, btn_y + btn_height//2, 
                                   fill="lightcoral", outline="darkred", width=2)
        self.canvas.create_text(btn_x, btn_y, text="MODO CAZADOR", font=("Arial", 11, "bold"))
        self.canvas.tag_bind("modo_cazador", "<Button-1>", lambda e: self.iniciar_juego("cazador"))
        self.canvas.create_rectangle(btn_x - btn_width//2, btn_y - btn_height//2, 
                                   btn_x + btn_width//2, btn_y + btn_height//2, 
                                   tags="modo_cazador", fill="", outline="")

        btn_y += btn_spacing
        # Botón PUNTAJES
        self.canvas.create_rectangle(btn_x - btn_width//2, btn_y - btn_height//2, 
                                   btn_x + btn_width//2, btn_y + btn_height//2, 
                                   fill="lightgreen", outline="darkgreen", width=2)
        self.canvas.create_text(btn_x, btn_y, text="PUNTAJES", font=("Arial", 11, "bold"))
        self.canvas.tag_bind("puntajes", "<Button-1>", lambda e: self.mostrar_puntajes())
        self.canvas.create_rectangle(btn_x - btn_width//2, btn_y - btn_height//2, 
                                   btn_x + btn_width//2, btn_y + btn_height//2, 
                                   tags="puntajes", fill="", outline="")

        btn_y += btn_spacing
        # Botón SALIR - Asegurar que esté visible
        self.canvas.create_rectangle(btn_x - btn_width//2, btn_y - btn_height//2, 
                                   btn_x + btn_width//2, btn_y + btn_height//2, 
                                   fill="lightgray", outline="black", width=2)
        self.canvas.create_text(btn_x, btn_y, text="SALIR", font=("Arial", 11, "bold"))
        self.canvas.tag_bind("salir", "<Button-1>", lambda e: self.root.quit())
        self.canvas.create_rectangle(btn_x - btn_width//2, btn_y - btn_height//2, 
                                   btn_x + btn_width//2, btn_y + btn_height//2, 
                                   tags="salir", fill="", outline="")

    def iniciar_juego(self, modo):
        """Inicia un nuevo juego"""
        # Pedir nombre del jugador
        self.nombre_jugador = simpledialog.askstring(
            "Nombre del Jugador",
            "Introduce tu nombre:"
        )

        if not self.nombre_jugador or self.nombre_jugador.strip() == "":
            messagebox.showwarning("Nombre requerido", "El registro es obligatorio. Debes introducir un nombre para jugar.")
            return

        # Limpiar el nombre (quitar espacios extra)
        self.nombre_jugador = self.nombre_jugador.strip()

        self.modo_juego = modo
        self.juego_activo = True
        self.juego_pausado = False
        self.tiempo_inicio = time.time()
        self.contador_frames = 0

        # Generar mapa
        self.generador = generar_mapa_juego()

        # Crear jugador
        self.jugador = Jugador(self.generador.posicion_jugador)

        # Crear enemigos
        posiciones_enemigos = obtener_posiciones_enemigos(self.generador.mapa, NUM_ENEMIGOS, self.jugador.posicion)
        self.enemigos = [Enemigo(pos) for pos in posiciones_enemigos]

        # Actualizar interfaz
        self.actualizar_interfaz()
        self.dibujar_mapa()

        # Iniciar loop del juego
        self.loop_juego()

    def dibujar_mapa(self):
        """Dibuja el mapa en el canvas"""
        self.canvas.delete("all")

        # Dibujar casillas
        for r in range(self.generador.filas):
            for c in range(self.generador.columnas):
                x1 = c * self.TAMANO_CASILLA
                y1 = r * self.TAMANO_CASILLA
                x2 = x1 + self.TAMANO_CASILLA
                y2 = y1 + self.TAMANO_CASILLA

                casilla = self.generador.mapa[r][c]
                color = self.colores.get(casilla.simbolo, "white")

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="gray")

                # Dibujar símbolo si no es camino
                if casilla.simbolo != ".":
                    self.canvas.create_text(
                        x1 + self.TAMANO_CASILLA // 2,
                        y1 + self.TAMANO_CASILLA // 2,
                        text=casilla.simbolo,
                        font=("Arial", 8, "bold"),
                        fill="white" if casilla.simbolo in ["#", "L"] else "black"
                    )

        # Dibujar jugador
        if self.jugador:
            self.dibujar_entidad(self.jugador.posicion, "J", self.colores["J"])

        # Dibujar enemigos vivos
        for enemigo in self.enemigos:
            if enemigo.vivo:
                self.dibujar_entidad(enemigo.posicion, "E", self.colores["E"])

    def dibujar_entidad(self, posicion, simbolo, color):
        """Dibuja una entidad (jugador o enemigo) en el mapa"""
        x1 = posicion.c * self.TAMANO_CASILLA + 2
        y1 = posicion.r * self.TAMANO_CASILLA + 2
        x2 = x1 + self.TAMANO_CASILLA - 4
        y2 = y1 + self.TAMANO_CASILLA - 4

        self.canvas.create_oval(x1, y1, x2, y2, fill=color, outline="black", width=2)
        self.canvas.create_text(
            x1 + (self.TAMANO_CASILLA - 4) // 2,
            y1 + (self.TAMANO_CASILLA - 4) // 2,
            text=simbolo,
            font=("Arial", 10, "bold"),
            fill="white"
        )

    def manejar_tecla(self, event):
        """Maneja las teclas presionadas"""
        if not self.juego_activo or self.juego_pausado:
            if event.keysym == "Escape":
                self.mostrar_menu_principal()
            return

        tecla = event.keysym.lower()
        corriendo = bool(event.state & 0x1)  # Shift presionado

        # Movimiento
        direcciones = {
            'w': (-1, 0), 'up': (-1, 0),
            's': (1, 0), 'down': (1, 0),
            'a': (0, -1), 'left': (0, -1),
            'd': (0, 1), 'right': (0, 1)
        }

        if tecla in direcciones:
            dr, dc = direcciones[tecla]
            nueva_r = self.jugador.posicion.r + dr
            nueva_c = self.jugador.posicion.c + dc

            if self.jugador.mover(self.generador.mapa, nueva_r, nueva_c, corriendo):
                self.verificar_colisiones()
                self.verificar_victoria()
                self.actualizar_interfaz()
                self.dibujar_mapa()

        # Colocar trampa (solo en modo escapa)
        elif tecla == 'space' and self.modo_juego == "escapa":
            if self.jugador.colocar_trampa_en_mapa(self.generador.mapa):
                self.dibujar_mapa()

        # Pausar
        elif tecla == 'p':
            self.pausar_juego()
        
        # Reiniciar juego
        elif tecla == 'r':
            self.reiniciar_juego()

        # Terminar juego en modo cazador
        elif tecla == 'q' and self.modo_juego == "cazador":
            resultado = messagebox.askyesno(
                "Terminar Juego", 
                f"¿Deseas terminar el juego?\nPuntaje actual: {self.jugador.puntaje}"
            )
            if resultado:
                self.fin_juego(True, f"Juego terminado voluntariamente")

        # Menú principal
        elif tecla == 'escape':
            self.mostrar_menu_principal()

    def loop_juego(self):
        """Loop principal del juego"""
        if not self.juego_activo or self.juego_pausado:
            self.root.after(100, self.loop_juego)
            return

        # Incrementar contador de frames
        self.contador_frames += 1

        # Mover enemigos con diferentes velocidades según el modo
        frames_enemigo = 4 if self.modo_juego == "escapa" else 3  # Más lento en ambos modos
        if self.contador_frames % frames_enemigo == 0:
            for enemigo in self.enemigos:
                if enemigo.vivo:
                    if self.modo_juego == "escapa":
                        enemigo.mover_hacia_objetivo(self.generador.mapa, self.jugador.posicion, huir=False)
                    else:  # modo cazador
                        enemigo.mover_hacia_objetivo(self.generador.mapa, self.jugador.posicion, huir=True)
                elif enemigo.puede_reaparecer():
                    # Reaparecer enemigo en una posición segura
                    posiciones_libres = obtener_posiciones_libres(self.generador.mapa, Camino)
                    # Filtrar posiciones muy cerca del jugador y evitar trampas
                    posiciones_validas = []
                    for pos in posiciones_libres:
                        distancia = abs(pos.r - self.jugador.posicion.r) + abs(pos.c - self.jugador.posicion.c)
                        casilla = self.generador.mapa[pos.r][pos.c]
                        if distancia >= 4 and not isinstance(casilla, Trampa):
                            posiciones_validas.append(pos)
                    
                    if posiciones_validas:
                        enemigo.posicion = random.choice(posiciones_validas)
                        enemigo.vivo = True

        # Verificar colisiones
        self.verificar_colisiones()

        # Verificar condiciones de victoria/derrota
        self.verificar_victoria()

        # Recuperar energía del jugador
        self.jugador.recuperar_energia()

        # Actualizar interfaz
        self.actualizar_interfaz()
        self.dibujar_mapa()

        # Continuar el loop
        self.root.after(100, self.loop_juego)  #movimiento mas fluido

    def verificar_colisiones(self):
        """Verifica colisiones entre jugador y enemigos/trampas"""
        # Verificar colisión con enemigos
        for enemigo in self.enemigos:
            if (enemigo.vivo and
                    self.jugador.posicion == enemigo.posicion):

                if self.modo_juego == "escapa":
                    # En modo escapa, enemigo atrapa al jugador
                    self.fin_juego(False, "Te atraparon!")
                    return
                else:
                    # En modo cazador, jugador atrapa al enemigo
                    enemigo.morir()
                    # El jugador obtiene puntos por atrapar (el doble de lo que perdería si escapa)
                    puntos_por_atrapar = 200  # Doble de los 100 que perdería si escapa
                    self.jugador.puntaje += puntos_por_atrapar
                    self.generar_nuevo_enemigo()

        # Verificar si el jugador está en una trampa (solo enemigos activan trampas)
        casilla_actual = self.generador.mapa[self.jugador.posicion.r][self.jugador.posicion.c]
        if isinstance(casilla_actual, Trampa) and casilla_actual.activa:
            # Solo los enemigos activan las trampas, no el jugador
            pass

        # Verificar si algún enemigo está en una trampa (solo en modo escapa)
        if self.modo_juego == "escapa":
            for enemigo in self.enemigos:
                if not enemigo.vivo:
                    continue

                casilla_enemigo = self.generador.mapa[enemigo.posicion.r][enemigo.posicion.c]
                if isinstance(casilla_enemigo, Trampa) and casilla_enemigo.activa:
                    # Activar trampa - el cazador muere inmediatamente
                    casilla_enemigo.activar_trampa()
                    enemigo.morir()
                    
                    # Pequeño bono de puntos adicional por eliminar cazador
                    bonus_trampa = 50  # Pequeño bono adicional
                    self.jugador.puntaje += bonus_trampa
                    self.jugador.trampas_activas -= 1

                    # La trampa desaparece del mapa
                    self.generador.mapa[enemigo.posicion.r][enemigo.posicion.c] = Camino()

    def verificar_victoria(self):
        """Verifica condiciones de victoria y enemigos en salidas"""
        # Verificar si algún enemigo llegó a una salida en modo cazador
        if self.modo_juego == "cazador":
            for enemigo in self.enemigos:
                if enemigo.vivo:
                    casilla_enemigo = self.generador.mapa[enemigo.posicion.r][enemigo.posicion.c]
                    if isinstance(casilla_enemigo, Salida) and not enemigo.escapo:
                        enemigo.escapo = True  # Evita múltiples ejecuciones
                        puntos_perdidos = 100
                        self.jugador.puntaje = max(0, self.jugador.puntaje - puntos_perdidos)

                        enemigo.morir()
                        self.generar_nuevo_enemigo()

    # Mostrar el messagebox fuera del loop principal
                        self.root.after(10, lambda: messagebox.showwarning(
                        "Enemigo Escapó",
                        f"Un cazador escapó! Perdiste {puntos_perdidos} puntos."
                        ))
                        break

        
        # Verificar victoria del jugador
        casilla_actual = self.generador.mapa[self.jugador.posicion.r][self.jugador.posicion.c]
        if isinstance(casilla_actual, Salida):
            if self.modo_juego == "escapa":
                # En modo escapa, llegar a la salida es victoria
                tiempo_transcurrido = time.time() - self.tiempo_inicio
                # Puntaje basado en tiempo: menor tiempo = mayor puntuación
                # Puntaje base: 2000 puntos, menos 20 puntos por segundo
                puntaje_tiempo = max(100, 2000 - int(tiempo_transcurrido * 20))
                # Bonus por dificultad (número de enemigos)
                bonus_dificultad = NUM_ENEMIGOS * 100
                puntaje_total = puntaje_tiempo + bonus_dificultad + self.jugador.puntaje
                self.jugador.puntaje = puntaje_total
                self.fin_juego(True, f"¡Escapaste! Tiempo: {tiempo_transcurrido:.1f}s - Puntaje: {puntaje_total}")
            else:
                # En modo cazador, si un enemigo llega a la salida, el jugador pierde puntos
                puntos_perdidos = 100
                self.jugador.puntaje = max(0, self.jugador.puntaje - puntos_perdidos)
                # Generar nuevo enemigo para reemplazar al que escapó
                self.generar_nuevo_enemigo()
                # Mostrar mensaje temporal de pérdida de puntos
                messagebox.showwarning("Enemigo Escapó", f"Un cazador escapó! Perdiste {puntos_perdidos} puntos.")

    def generar_nuevo_enemigo(self):
        """Genera un nuevo enemigo en una posición aleatoria"""
        posiciones_libres = obtener_posiciones_libres(self.generador.mapa, Camino)
        # No generar muy cerca del jugador
        posiciones_validas = [pos for pos in posiciones_libres
                              if abs(pos.r - self.jugador.posicion.r) + abs(pos.c - self.jugador.posicion.c) > 5]

        if posiciones_validas:
            nueva_posicion = random.choice(posiciones_validas)
            self.enemigos.append(Enemigo(nueva_posicion))

    def fin_juego(self, victoria, mensaje):
        """Termina el juego y muestra resultados"""
        self.juego_activo = False

        # Calcular tiempo transcurrido
        tiempo_transcurrido = time.time() - self.tiempo_inicio

        # Mostrar mensaje de resultado
        if victoria:
            if self.modo_juego == "escapa":
                messagebox.showinfo("¡Victoria!", mensaje)
            else:
                messagebox.showinfo("Juego Terminado", mensaje)
        else:
            messagebox.showinfo("Derrota", mensaje)

        # Guardar puntaje (siempre guardar en modo escapa cuando gana, en cazador siempre)
        if victoria or self.modo_juego == "cazador":
            self.sistema_puntajes.agregar_puntaje(
                self.nombre_jugador,
                self.jugador.puntaje,
                self.modo_juego
            )

        # Mostrar puntaje final
        messagebox.showinfo(
            "Puntaje Final",
            f"Jugador: {self.nombre_jugador}\n"
            f"Puntaje: {self.jugador.puntaje}\n"
            f"Tiempo: {tiempo_transcurrido:.1f}s"
        )

        self.mostrar_menu_principal()

    def pausar_juego(self):
        """Pausa o reanuda el juego"""
        if not self.juego_activo:
            return

        self.juego_pausado = not self.juego_pausado
        self.btn_pausar.config(text="Reanudar" if self.juego_pausado else "Pausar")

        if self.juego_pausado:
            self.canvas.create_text(
                COLUMNAS * self.TAMANO_CASILLA // 2,
                FILAS * self.TAMANO_CASILLA // 2,
                text="PAUSADO\nPresiona P para continuar",
                font=("Arial", 16, "bold"),
                fill="red",
                tags="pausa"
            )
        else:
            self.canvas.delete("pausa")
    
    def reiniciar_juego(self):
        """Reinicia el juego actual con el mismo modo y jugador"""
        if not self.modo_juego or not self.nombre_jugador:
            return  # Solo reinicia si ya hay un juego activo
        
        # Guardar datos actuales
        modo_actual = self.modo_juego
        nombre_actual = self.nombre_jugador
        
        # Reiniciar variables del juego
        self.juego_activo = True  # Reactivar el juego
        self.juego_pausado = False
        self.tiempo_inicio = time.time()
        self.contador_frames = 0

        # Generar nuevo mapa
        self.generador = generar_mapa_juego()

        # Crear nuevo jugador
        self.jugador = Jugador(self.generador.posicion_jugador)

        # Crear nuevos enemigos
        posiciones_enemigos = obtener_posiciones_enemigos(self.generador.mapa, NUM_ENEMIGOS, self.jugador.posicion)
        self.enemigos = [Enemigo(pos) for pos in posiciones_enemigos]

        # Restaurar datos
        self.modo_juego = modo_actual
        self.nombre_jugador = nombre_actual

        # Actualizar interfaz
        self.btn_pausar.config(text="Pausar")
        self.canvas.delete("pausa")  # Limpiar mensaje de pausa si existe
        self.actualizar_interfaz()
        self.dibujar_mapa()  # Dibujar el nuevo mapa
        self.dibujar_mapa()

    def actualizar_interfaz(self):
        """Actualiza la información mostrada en la interfaz"""
        if not self.jugador:
            return

        self.label_nombre.config(text=f"Jugador: {self.nombre_jugador}")
        self.label_modo.config(text=f"Modo: {self.modo_juego.title()}")
        self.label_puntaje.config(text=f"Puntaje: {self.jugador.puntaje}")

        if self.juego_activo:
            tiempo_transcurrido = time.time() - self.tiempo_inicio
            self.label_tiempo.config(text=f"Tiempo: {tiempo_transcurrido:.1f}s")

        # Actualizar barra de energía
        self.barra_energia.config(value=self.jugador.energia)
        self.label_energia.config(text=f"{self.jugador.energia}/{ENERGIA_MAXIMA}")

        # Actualizar información de trampas en modo escapa
        for widget in self.frame_trampas.winfo_children():
            widget.destroy()

        if self.modo_juego == "escapa":
            tk.Label(self.frame_trampas, text="Trampas:", font=("Arial", 10, "bold")).pack(anchor="w")
            tk.Label(self.frame_trampas, text=f"Activas: {self.jugador.trampas_activas}/{MAX_TRAMPAS_ACTIVAS}").pack(
                anchor="w")

            tiempo_desde_ultima = time.time() - self.jugador.ultimo_uso_trampa
            cooldown_restante = max(0, COOLDOWN_TRAMPA - tiempo_desde_ultima)
            tk.Label(self.frame_trampas, text=f"Cooldown: {cooldown_restante:.1f}s").pack(anchor="w")

    def mostrar_puntajes(self):
        """Muestra la ventana de puntajes"""
        ventana_puntajes = tk.Toplevel(self.root)
        ventana_puntajes.title("Puntajes")
        ventana_puntajes.geometry("400x500")
        ventana_puntajes.resizable(False, False)

        # Top 5 Modo Escapa
        tk.Label(ventana_puntajes, text="TOP 5 - MODO ESCAPA", font=("Arial", 14, "bold")).pack(pady=10)

        top_escapa = self.sistema_puntajes.obtener_top5("escapa")
        if top_escapa:
            for i, puntaje in enumerate(top_escapa, 1):
                tk.Label(
                    ventana_puntajes,
                    text=f"{i}. {puntaje['nombre']} - {puntaje['puntaje']} pts",
                    font=("Arial", 10)
                ).pack()
        else:
            tk.Label(ventana_puntajes, text="No hay puntajes registrados", font=("Arial", 9)).pack()

        tk.Label(ventana_puntajes, text="", height=2).pack()  # Espaciador

        # Top 5 Modo Cazador
        tk.Label(ventana_puntajes, text="TOP 5 - MODO CAZADOR", font=("Arial", 14, "bold")).pack(pady=10)

        top_cazador = self.sistema_puntajes.obtener_top5("cazador")
        if top_cazador:
            for i, puntaje in enumerate(top_cazador, 1):
                tk.Label(
                    ventana_puntajes,
                    text=f"{i}. {puntaje['nombre']} - {puntaje['puntaje']} pts",
                    font=("Arial", 10)
                ).pack()
        else:
            tk.Label(ventana_puntajes, text="No hay puntajes registrados", font=("Arial", 9)).pack()

        # Botón cerrar
        tk.Button(
            ventana_puntajes,
            text="Cerrar",
            command=ventana_puntajes.destroy,
            font=("Arial", 10),
            width=15
        ).pack(pady=20)

    def ejecutar(self):
        """Ejecuta el juego"""
        self.root.mainloop()


# ----------------- FUNCIÓN PRINCIPAL -----------------
def main():
    """Función principal del juego"""
    juego = JuegoLaberinto()
    juego.ejecutar()


# Ejecutar el juego
if __name__ == "__main__":
    main()