from django.contrib import messages
from django.contrib.auth import login          
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction                                           
from django.shortcuts import get_object_or_404, render, redirect
from .forms import RegistroForm, UsuarioUpdateForm, PerfilUpdateForm
from .forms import InmuebleForm, InmuebleUpdateForm
from .models import Inmueble, Perfil, Region, TipoInmueble


@login_required
def home(request):
    inmuebles = Inmueble.objects.filter(estado='disponible')
    return render(request, 'home.html', {'inmuebles': inmuebles})


def registro(request):
    # Si ya inició sesión, no tiene sentido registrarse de nuevo
    if request.user.is_authenticated:
        return redirect('perfil')
 
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # inicia la sesión del usuario recién creado
            messages.success(request, f'¡Bienvenido/a, {user.first_name}! Tu cuenta quedó creada.')
            return redirect('perfil')
    else:
        form = RegistroForm()
    return render(request, 'register.html', {'form': form})


# Solo entra quien tenga el permiso add_inmueble (grupo Arrendadores o superusuario).
# raise_exception=True: al resto le responde 403 (Prohibido) en vez de mandarlo al login
@login_required
@permission_required('gestion_inmuebles.add_inmueble', raise_exception=True)
def mis_inmuebles(request):
    inmuebles = request.user.inmuebles.select_related(
        'comuna', 'tipo_inmueble'
    ).all()
    return render(request, 'mis_inmuebles.html', {'inmuebles': inmuebles})


@login_required
@permission_required('gestion_inmuebles.add_inmueble', raise_exception=True)
def crear_inmueble(request):
    if request.method == 'POST':
        form = InmuebleForm(request.POST)
        if form.is_valid():
            inmueble = form.save(commit=False)
            inmueble.propietario = request.user
            inmueble.save()
            messages.success(request, 'El inmueble se publicó correctamente.')
            return redirect('mis_inmuebles')
    else:
        form = InmuebleForm()
    return render(request, 'inmueble_form.html', {
        'form': form,
        'titulo': 'Publicar inmueble',
    })


@login_required
@permission_required('gestion_inmuebles.change_inmueble', raise_exception=True)
def editar_inmueble(request, pk):
    inmueble = get_object_or_404(Inmueble, pk=pk, propietario=request.user)
    if request.method == 'POST':
        form = InmuebleUpdateForm(request.POST, instance=inmueble)
        if form.is_valid():
            form.save()
            messages.success(request, 'El inmueble se actualizó correctamente.')
            return redirect('mis_inmuebles')
    else:
        form = InmuebleUpdateForm(instance=inmueble)
    return render(request, 'inmueble_form.html', {
        'form': form,
        'titulo': 'Editar inmueble',
        'inmueble': inmueble,
    })


@login_required
@permission_required('gestion_inmuebles.delete_inmueble', raise_exception=True)
def eliminar_inmueble(request, pk):
    inmueble = get_object_or_404(Inmueble, pk=pk, propietario=request.user)
    if request.method == 'POST':
        inmueble.delete()
        messages.success(request, 'El inmueble se eliminó correctamente.')
        return redirect('mis_inmuebles')
    return render(request, 'inmueble_eliminar.html', {'inmueble': inmueble})


@login_required
@permission_required('gestion_inmuebles.view_inmueble', raise_exception=True)
def oferta(request):
    inmuebles = Inmueble.objects.filter(estado='disponible').select_related(
        'comuna__region', 'tipo_inmueble'
    )
    region_id = request.GET.get('region')
    tipo_id = request.GET.get('tipo')
    if region_id and region_id.isdigit():
        inmuebles = inmuebles.filter(comuna__region_id=region_id)
    if tipo_id and tipo_id.isdigit():
        inmuebles = inmuebles.filter(tipo_inmueble_id=tipo_id)
    return render(request, 'oferta.html', {
        'inmuebles': inmuebles,
        'regiones': Region.objects.order_by('nombre'),
        'tipos': TipoInmueble.objects.order_by('nombre'),
        'region_seleccionada': region_id or '',
        'tipo_seleccionado': tipo_id or '',
    })


# Página personal de perfil: sirve para arrendatarios y arrendadores
@login_required
def perfil(request):
    # Ojo: el superusuario se creó con createsuperuser y NO tiene Perfil.
    # Con filter().first() obtenemos None en vez de un error.
    perfil = Perfil.objects.filter(user=request.user).first()
    contexto = {'perfil': perfil}

    # Solo los arrendadores (permiso add_inmueble) ven el resumen de sus inmuebles
    if request.user.has_perm('gestion_inmuebles.add_inmueble'):
        mis_inmuebles = request.user.inmuebles.all()
        contexto['total_inmuebles'] = mis_inmuebles.count()
        contexto['disponibles'] = mis_inmuebles.filter(estado='disponible').count()

    return render(request, 'perfil.html', contexto)

@login_required
def editar_perfil(request):
    # El superusuario no tiene Perfil: con filter().first() obtenemos None, no un error
    perfil = Perfil.objects.filter(user=request.user).first()

    if request.method == 'POST':
        # instance=...: el formulario MODIFICA ese registro en vez de crear uno nuevo
        usuario_form = UsuarioUpdateForm(request.POST, instance=request.user)
        perfil_form = PerfilUpdateForm(request.POST, instance=perfil) if perfil else None
        perfil_ok = perfil_form is None or perfil_form.is_valid()

        if usuario_form.is_valid() and perfil_ok:
            with transaction.atomic():  # se guardan los dos o ninguno
                usuario_form.save()
                if perfil_form:
                    perfil_form.save()
            messages.success(request, 'Tus datos se actualizaron correctamente.')
            return redirect('perfil')
    else:
        
        usuario_form = UsuarioUpdateForm(instance=request.user)
        perfil_form = PerfilUpdateForm(instance=perfil) if perfil else None

    return render(request, 'editar_perfil.html', {
        'usuario_form': usuario_form,
        'perfil_form': perfil_form,
        'perfil': perfil,
    })