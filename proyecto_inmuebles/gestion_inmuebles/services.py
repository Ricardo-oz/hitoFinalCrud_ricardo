from django.contrib.auth.models import User, Group, Permission

from .models import Region, Comuna, TipoInmueble, TipoUsuario, Perfil, Inmueble


# Datos iniciales: regiones, comunas y tipos. get_or_create evita duplicados
# si ejecutamos la función más de una vez.
def cargar_datos_iniciales():
    datos = {
        "Los Lagos": ["Osorno", "Puerto Montt", "Puerto Varas"],
        "Metropolitana de Santiago": ["Santiago", "Providencia", "Ñuñoa"],
    }
    for nombre_region, comunas in datos.items():
        region, _ = Region.objects.get_or_create(nombre=nombre_region)
        for nombre_comuna in comunas:
            Comuna.objects.get_or_create(nombre=nombre_comuna, region=region)

    for tipo in ["Casa", "Departamento", "Parcela"]:
        TipoInmueble.objects.get_or_create(nombre=tipo)

    for tipo in ["Arrendatario", "Arrendador"]:
        TipoUsuario.objects.get_or_create(nombre=tipo)


# CREATE: usuario + perfil. Ojo que create_user encripta la contraseña.
# Primero se valida el tipo de usuario: si no existe, get() lanza
# DoesNotExist antes de crear el User y no queda un usuario sin perfil.
def crear_usuario(username, password, nombres, apellidos, correo,
                  rut, direccion, telefono, tipo_usuario):
    tipo = TipoUsuario.objects.get(nombre=tipo_usuario)
    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=nombres,
        last_name=apellidos,
        email=correo,
    )
    Perfil.objects.create(
        user=user,
        tipo_usuario=tipo,
        rut=rut,
        direccion=direccion,
        telefono=telefono,
    )
    asignar_grupo(user, tipo)  # NUEVO: Arrendadores o Arrendatarios
    return user


# CREATE: inmueble. Se instancia el objeto y se guarda con save().
def insertar_inmueble(propietario, tipo_inmueble, comuna, nombre,
                      descripcion, m2_construidos, m2_totales,
                      estacionamientos, habitaciones, banos, direccion,
                      precio_mensual):
    inmueble = Inmueble(
        propietario=propietario,
        tipo_inmueble=TipoInmueble.objects.get(nombre=tipo_inmueble),
        comuna=Comuna.objects.get(nombre=comuna),
        nombre=nombre,
        descripcion=descripcion,
        m2_construidos=m2_construidos,
        m2_totales=m2_totales,
        estacionamientos=estacionamientos,
        habitaciones=habitaciones,
        banos=banos,
        direccion=direccion,
        precio_mensual=precio_mensual,
    )
    inmueble.save()
    return inmueble

# READ: todos los inmuebles
def get_all_inmuebles():
    return Inmueble.objects.all()


# READ con filtro: inmuebles de una comuna
# (lo usará el arrendatario más adelante)
def listar_inmuebles_por_comuna(nombre_comuna):
    return Inmueble.objects.filter(comuna__nombre=nombre_comuna)


# UPDATE: filter() + update() modifica directamente en la base de datos
def actualizar_descrp_inmueble(id_inmueble, nueva_descripcion):
    return Inmueble.objects.filter(pk=id_inmueble).update(
        descripcion=nueva_descripcion
    )


# UPDATE general: recibe cualquier campo como parámetro con nombre
def actualizar_inmueble(id_inmueble, **cambios):
    return Inmueble.objects.filter(pk=id_inmueble).update(**cambios)


# DELETE: se obtiene el objeto con get() y se elimina con delete().
# Ojo que get() lanza DoesNotExist si el id no existe, por eso el try/except.
def eliminar_inmueble(id_inmueble):
    try:
        inmueble = Inmueble.objects.get(id=id_inmueble)
    except Inmueble.DoesNotExist:
        return f"No existe un inmueble con id {id_inmueble}"
    inmueble.delete()
    return f"Inmueble '{inmueble.nombre}' eliminado"


# GRUPOS Y PERMISOS
# tipo de usuario -> (nombre del grupo, permisos sobre el modelo Inmueble)
GRUPOS = {
    "Arrendador": ("Arrendador", ["add_inmueble", "change_inmueble",
                                    "delete_inmueble", "view_inmueble"]),
    "Arrendatario": ("Arrendatario", ["view_inmueble"]),
}


def crear_grupos_y_permisos():
    for tipo, (nombre_grupo, codenames) in GRUPOS.items():
        grupo, creado = Group.objects.get_or_create(name=nombre_grupo)
        # Se busca por codename (no por el nombre en inglés "Can add inmueble")
        permisos = Permission.objects.filter(
            content_type__app_label="gestion_inmuebles", codename__in=codenames
        )
        # set() reemplaza los permisos: se puede ejecutar varias veces sin duplicar
        grupo.permissions.set(permisos)
        # Los usuarios que ya existían (Hito 1) también quedan en su grupo
        for perfil in Perfil.objects.filter(tipo_usuario__nombre=tipo):
            perfil.user.groups.add(grupo)
        accion = "creado" if creado else "actualizado"
        print(f"Grupo {nombre_grupo} {accion} con {permisos.count()} permisos")


def asignar_grupo(user, tipo_usuario):
    nombre_grupo, codenames = GRUPOS[tipo_usuario.nombre]
    grupo, _ = Group.objects.get_or_create(name=nombre_grupo)
    permisos = Permission.objects.filter(
        content_type__app_label="gestion_inmuebles", codename__in=codenames
    )
    grupo.permissions.add(*permisos)
    user.groups.add(grupo)