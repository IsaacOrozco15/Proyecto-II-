
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
                pass  # Error silencioso al cargar puntajes
        
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
            pass  # posible error

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

