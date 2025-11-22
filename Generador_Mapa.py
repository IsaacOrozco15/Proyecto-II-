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