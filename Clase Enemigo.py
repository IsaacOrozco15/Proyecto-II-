class Enemigo:
    def __init__(self, posicion):
        self.posicion = posicion
        self.vivo = True
        self.tiempo_muerte = 0

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
