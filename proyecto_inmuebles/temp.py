import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proyecto_inmuebles.settings")
django.setup()

from gestion_inmuebles.models import Inmueble  

def get_list_inmuebles(comuna=""):
    select = """
        SELECT i.id, i.nombre, i.descripcion, c.nombre AS nombre_comuna
        FROM gestion_inmuebles_inmueble AS i
        INNER JOIN gestion_inmuebles_comuna AS c ON i.comuna_id = c.id
        WHERE i.estado = 'disponible'
            AND c.nombre LIKE %s
        ORDER BY c.nombre, i.nombre
    """

    query = Inmueble.objects.raw(select, [f"%{comuna}%"])

    total = 0
    with open("datos.txt", "w", encoding="utf-8") as archi1:
        comuna_actual = None
        for p in query:
            if p.nombre_comuna != comuna_actual: 
                archi1.write(f"\n=== {p.nombre_comuna} ===\n")
                comuna_actual = p.nombre_comuna
            archi1.write(p.nombre + " - " + p.descripcion + "\n")
            total += 1
    print(f"{total} inmuebles escritos en datos.txt")


if __name__ == "__main__":
    comuna = sys.argv[1] if len(sys.argv) > 1 else ""
    get_list_inmuebles(comuna)