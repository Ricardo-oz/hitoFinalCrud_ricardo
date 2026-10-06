from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction

from .models import Perfil, TipoUsuario, Inmueble, Comuna
from .services import asignar_grupo  


class RegistroForm(UserCreationForm):
    
    first_name = forms.CharField(label='Nombres', max_length=150)
    last_name = forms.CharField(label='Apellidos', max_length=150)
    email = forms.EmailField(label='Correo electrónico')
    tipo_usuario = forms.ModelChoiceField(
        label='Quiero registrarme como',
        queryset=TipoUsuario.objects.all(),
        widget=forms.RadioSelect,
        empty_label=None,
    )
    rut = forms.CharField(label='RUT', max_length=12, help_text='Ejemplo: 12345678-9')
    direccion = forms.CharField(label='Dirección', max_length=200)
    telefono = forms.CharField(label='Teléfono', max_length=20)

    # Orden en que se muestran los campos: las contraseñas al final
    field_order = ['username', 'first_name', 'last_name', 'email', 'tipo_usuario',
                   'rut', 'direccion', 'telefono', 'password1', 'password2']

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')

    def clean_rut(self):
        # NUEVO: 18.765.432-1 y 18765432-1 se guardan igual (sin puntos ni espacios, K mayúscula)
        rut = self.cleaned_data['rut'].replace('.', '').replace(' ', '').upper()
        if Perfil.objects.filter(rut=rut).exists():
            raise forms.ValidationError('Ya existe un usuario registrado con este RUT.')
        return rut

    # atomic: si falla la creación del perfil, tampoco se guarda el usuario
    @transaction.atomic
    def save(self):
        user = super().save()  # crea el User con la contraseña encriptada
        Perfil.objects.create(
            user=user,
            tipo_usuario=self.cleaned_data['tipo_usuario'],
            rut=self.cleaned_data['rut'],
            direccion=self.cleaned_data['direccion'],
            telefono=self.cleaned_data['telefono'],
        )
        asignar_grupo(user, self.cleaned_data['tipo_usuario'])  # NUEVO: Arrendadores o Arrendatarios
        return user
    
class UsuarioUpdateForm(forms.ModelForm):
    # En el modelo User estos tres campos son opcionales (blank=True).
    # Los volvemos a declarar para que sean obligatorios y no se puedan dejar vacíos.
    first_name = forms.CharField(label='Nombres', max_length=150)
    last_name = forms.CharField(label='Apellidos', max_length=150)
    email = forms.EmailField(label='Correo electrónico')
 
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
 
 
class PerfilUpdateForm(forms.ModelForm):
    # El RUT y el tipo de usuario NO se editan: el RUT identifica a la persona
    # y el tipo define su grupo y sus permisos.
    class Meta:
        model = Perfil
        fields = ['direccion', 'telefono']
        labels = {'direccion': 'Dirección', 'telefono': 'Teléfono'}
class InmuebleForm(forms.ModelForm):
   
    comuna = forms.ModelChoiceField(
        label='Comuna',
        queryset=Comuna.objects.select_related('region').order_by('region__nombre', 'nombre'),
        empty_label='Selecciona una comuna',
    )
 
    class Meta:
        model = Inmueble
        # propietario y estado NO van: el propietario es quien inició sesión
        # y un inmueble nuevo siempre parte "disponible".
        fields = ['nombre', 'tipo_inmueble', 'comuna', 'direccion', 'descripcion',
                  'm2_construidos', 'm2_totales', 'habitaciones', 'banos',
                  'estacionamientos', 'precio_mensual']
        labels = {
            'nombre': 'Nombre de la publicación',
            'tipo_inmueble': 'Tipo de inmueble',
            'direccion': 'Dirección',
            'descripcion': 'Descripción',
            'm2_construidos': 'M² construidos',
            'm2_totales': 'M² totales del terreno',
            'banos': 'Baños',
            'precio_mensual': 'Precio mensual ($)',
        }
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 3})}
 
    def clean(self):
        datos = super().clean()
        construidos = datos.get('m2_construidos')
        totales = datos.get('m2_totales')
        # Regla de negocio: no se puede construir más de lo que mide el terreno
        if construidos is not None and totales is not None and construidos > totales:
            self.add_error('m2_construidos', 'No puede ser mayor que los m² totales.')
        return datos


class InmuebleUpdateForm(InmuebleForm):
    class Meta(InmuebleForm.Meta):
        fields = InmuebleForm.Meta.fields + ['estado']