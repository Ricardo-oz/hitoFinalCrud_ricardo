import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "proyecto_inmuebles.settings")
django.setup()

from gestion_inmuebles.models import Inmueble

def get_list_inmuebles_region(region=""):
    # El inmueble no guarda la región: se llega a ella a través de la comuna
    # inmueble -> comuna -> region  (por eso hay dos INNER JOIN)
    select = """
        SELECT i.id, i.nombre, i.descripcion,
                c.nombre AS nombre_comuna, r.nombre AS nombre_region
        FROM gestion_inmuebles_inmueble AS i
        INNER JOIN gestion_inmuebles_comuna AS c ON i.comuna_id = c.id
        INNER JOIN gestion_inmuebles_region AS r ON c.region_id = r.id
        WHERE i.estado = 'disponible'
            AND r.nombre LIKE %s
        ORDER BY r.id, c.nombre, i.nombre
    """
    query = Inmueble.objects.raw(select, [f"%{region}%"])

    total = 0
    with open("datos_regiones.txt", "w", encoding="utf-8") as archi1:
        region_actual = None
        for p in query:
            if p.nombre_region != region_actual:
                archi1.write(f"\n=== Región {p.nombre_region} ===\n")
                region_actual = p.nombre_region
            archi1.write(p.nombre + " - " + p.descripcion + " (" + p.nombre_comuna + ")\n")
            total += 1
    print(f"{total} inmuebles escritos en datos_regiones.txt")

if __name__ == "__main__":
    region = sys.argv[1] if len(sys.argv) > 1 else ""
    get_list_inmuebles_region(region)