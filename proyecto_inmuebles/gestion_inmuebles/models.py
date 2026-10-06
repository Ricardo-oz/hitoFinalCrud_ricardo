from django.db import models
from django.contrib.auth.models import User

class Region(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Comuna(models.Model):
    nombre = models.CharField(max_length=100)
    region = models.ForeignKey(
        Region, on_delete=models.PROTECT, related_name="comunas"
    )

    def __str__(self):
        return f"{self.nombre} ({self.region})"

class TipoInmueble(models.Model):
    # Casa, Departamento, Parcela
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class TipoUsuario(models.Model):
    # Arrendatario, Arrendador
    nombre = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nombre

class Perfil(models.Model):
    # Nombres, apellidos y correo ya vienen en User
    # (first_name, last_name, email)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil"
    )
    tipo_usuario = models.ForeignKey(TipoUsuario, on_delete=models.PROTECT)
    rut = models.CharField(max_length=12, unique=True)
    direccion = models.CharField(max_length=200)
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.tipo_usuario}"

class Inmueble(models.Model):
    ESTADOS = [
        ("disponible", "Disponible"),
        ("arrendado", "Arrendado"),
    ]

    propietario = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="inmuebles"
    )
    tipo_inmueble = models.ForeignKey(TipoInmueble, on_delete=models.PROTECT)
    comuna = models.ForeignKey(
        Comuna, on_delete=models.PROTECT, related_name="inmuebles"
    )
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField()
    m2_construidos = models.FloatField()
    m2_totales = models.FloatField()
    estacionamientos = models.PositiveIntegerField(default=0)
    habitaciones = models.PositiveIntegerField(default=0)
    banos = models.PositiveIntegerField(default=0)
    direccion = models.CharField(max_length=200)
    precio_mensual = models.PositiveIntegerField()
    estado = models.CharField(
        max_length=20, choices=ESTADOS, default="disponible"
    )

    def __str__(self):
        return f"{self.nombre} - {self.comuna.nombre}"