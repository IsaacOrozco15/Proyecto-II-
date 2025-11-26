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

        # --- CARGAR SPRITES DEL JUGADOR (usar ruta robusta y escalar si PIL está disponible) ---
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Si tus sprites están en Escapa_del_Laberinto/sprites_personaje relativo al script:
        sprites_dir = os.path.join(base_dir, "sprites_personaje")
        # Si están directamente en sprites_personaje a la par del script, usa:
        # sprites_dir = os.path.join(base_dir, "sprites_personaje")

        def _cargar_sprite(nombre):
            ruta = os.path.join(sprites_dir, nombre)
            if not os.path.exists(ruta):
                print(f"[Sprites] No encontrado: {ruta}")
                return None
            try:
                if PIL_AVAILABLE:
                    img = Image.open(ruta).convert("RGBA")
                    img = img.resize((self.TAMANO_CASILLA, self.TAMANO_CASILLA), Image.Resampling.LANCZOS)
                    return ImageTk.PhotoImage(img)
                else:
                    # PhotoImage no escala; la imagen debe tener el tamaño correcto
                    return tk.PhotoImage(file=ruta)
            except Exception as e:
                print(f"[Sprites] Error cargando {ruta}: {e}")
                return None

        # nombres exactos de archivos (incluye extensión)
        self.sprites_jugador = {
            "down": _cargar_sprite("Personaje_down.png"),
            "up": _cargar_sprite("Personaje_up.png"),
            "left": _cargar_sprite("Personaje_left.png"),
            "right": _cargar_sprite("Personaje_right.png")
        }

        # lista para mantener referencias temporales y evitar GC accidental
        self._image_refs = []


        Muro.cargar_imagen(self.TAMANO_CASILLA)
        Liana.cargar_imagen(self.TAMANO_CASILLA)


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