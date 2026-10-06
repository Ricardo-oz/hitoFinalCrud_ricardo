# Evidencia Hito 4 - Parte 2

**Proyecto:** `proyecto_inmuebles`  
**Aplicación:** `gestion_inmuebles`  
**Evidencia:** fragmentos del código implementado y páginas asociadas.

Este informe documenta el cumplimiento de los requerimientos para publicar inmuebles, administrar las publicaciones del arrendador y consultar la oferta disponible.

## 1. Agregar inmuebles

### 1.a Rutas para agregar viviendas

En `gestion_inmuebles/urls.py` se define la ruta para abrir el formulario de publicación:

```python
path('inmuebles/nuevo/', views.crear_inmueble, name='crear_inmueble'),
```

La ruta queda integrada junto al listado personal del arrendador:

```python
path('mis-inmuebles/', views.mis_inmuebles, name='mis_inmuebles'),
path('inmuebles/nuevo/', views.crear_inmueble, name='crear_inmueble'),
```

La vista exige sesión iniciada y el permiso `add_inmueble`:

```python
@login_required
@permission_required('gestion_inmuebles.add_inmueble', raise_exception=True)
def crear_inmueble(request):
    ...
```

**Archivo:** `proyecto_inmuebles/gestion_inmuebles/views.py`

### 1.b Formulario basado en el modelo

`InmuebleForm` es un `ModelForm` basado en `Inmueble`. No expone `propietario`, que se asigna desde la sesión, ni `estado`, que comienza disponible por defecto.

```python
class InmuebleForm(forms.ModelForm):
    class Meta:
        model = Inmueble
        fields = [
            'nombre', 'tipo_inmueble', 'comuna', 'direccion', 'descripcion',
            'm2_construidos', 'm2_totales', 'habitaciones', 'banos',
            'estacionamientos', 'precio_mensual'
        ]
```

El campo de comuna se obtiene de la base de datos y la validación evita que los metros construidos superen los metros totales:

```python
comuna = forms.ModelChoiceField(
    label='Comuna',
    queryset=Comuna.objects.select_related('region').order_by('region__nombre', 'nombre'),
    empty_label='Selecciona una comuna',
)

if construidos is not None and totales is not None and construidos > totales:
    self.add_error('m2_construidos', 'No puede ser mayor que los m² totales.')
```

**Archivo:** `proyecto_inmuebles/gestion_inmuebles/forms.py`

### 1.c Guardar el inmueble

La vista valida el formulario, crea el objeto sin guardarlo inicialmente, asigna como propietario a la persona autenticada y persiste el inmueble.

```python
if form.is_valid():
    inmueble = form.save(commit=False)
    inmueble.propietario = request.user
    inmueble.save()
    return redirect('mis_inmuebles')
```

La vista también crea un formulario vacío al entrar por GET y vuelve a mostrarlo con errores si los datos no pasan la validación:

```python
if request.method == 'POST':
    form = InmuebleForm(request.POST)
    if form.is_valid():
        inmueble = form.save(commit=False)
        inmueble.propietario = request.user
        inmueble.save()
        return redirect('mis_inmuebles')
else:
    form = InmuebleForm()
return render(request, 'inmueble_form.html', {'form': form, 'titulo': 'Publicar inmueble'})
```

La página envía los datos de forma segura mediante POST y CSRF:

```html
<form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit" class="btn btn-success">Guardar</button>
</form>
```

**Archivo:** `proyecto_inmuebles/gestion_inmuebles/views.py`  
**Interfaz:** `templates/inmueble_form.html` muestra el formulario con método POST y token CSRF; `templates/mis_inmuebles.html` incluye el botón “Publicar inmueble”.

## 2. Actualizar y borrar inmuebles existentes

### 2.a Rutas por identificador

Las rutas identifican el inmueble mediante `pk`:

```python
path('mis-inmuebles/', views.mis_inmuebles, name='mis_inmuebles'),
path('inmuebles/<int:pk>/editar/', views.editar_inmueble, name='editar_inmueble'),
path('inmuebles/<int:pk>/eliminar/', views.eliminar_inmueble, name='eliminar_inmueble'),
```

El listado obtiene las publicaciones del usuario autenticado, y cada ruta de edición/eliminación recibe el `pk` del inmueble:

```python
inmuebles = request.user.inmuebles.select_related(
    'comuna', 'tipo_inmueble'
).all()
```

**Archivo:** `proyecto_inmuebles/gestion_inmuebles/urls.py`

### 2.b Formulario basado en el modelo

El formulario de actualización hereda los campos y validaciones de `InmuebleForm` y agrega el estado del inmueble:

```python
class InmuebleUpdateForm(InmuebleForm):
    class Meta(InmuebleForm.Meta):
        fields = InmuebleForm.Meta.fields + ['estado']
```

Al construir el formulario se pasa `instance=inmueble`, por lo que Django carga los datos existentes para editarlos.

La vista usa esa instancia tanto para mostrar los datos en GET como para aplicar los cambios en POST:

```python
inmueble = get_object_or_404(Inmueble, pk=pk, propietario=request.user)
if request.method == 'POST':
    form = InmuebleUpdateForm(request.POST, instance=inmueble)
else:
    form = InmuebleUpdateForm(instance=inmueble)
```

Así el formulario no crea otro inmueble: actualiza el registro recuperado.

### 2.c Actualización y eliminación

Antes de editar o eliminar, la vista recupera el inmueble verificando que pertenezca al usuario actual. La actualización guarda la instancia existente:

```python
inmueble = get_object_or_404(Inmueble, pk=pk, propietario=request.user)
if request.method == 'POST':
    form = InmuebleUpdateForm(request.POST, instance=inmueble)
    if form.is_valid():
        form.save()
        return redirect('mis_inmuebles')
```

La eliminación también verifica la propiedad y solo ejecuta `delete()` al recibir POST desde la página de confirmación:

```python
inmueble = get_object_or_404(Inmueble, pk=pk, propietario=request.user)
if request.method == 'POST':
    inmueble.delete()
    return redirect('mis_inmuebles')
```

**Archivo:** `proyecto_inmuebles/gestion_inmuebles/views.py`  
**Interfaz:** `templates/mis_inmuebles.html` muestra acciones “Editar” y “Eliminar”; `templates/inmueble_eliminar.html` solicita confirmación mediante POST.

En el listado, las acciones generan las URL usando la clave primaria de cada inmueble:

```django
<a href="{% url 'editar_inmueble' inmueble.pk %}">Editar</a>
<a href="{% url 'eliminar_inmueble' inmueble.pk %}">Eliminar</a>
```

La confirmación de borrado exige POST y token CSRF; abrir la página no elimina datos:

```html
<form method="post">
    {% csrf_token %}
    <button type="submit">Sí, eliminar</button>
</form>
```

## 3. Ver la oferta disponible

### 3.a Ruta de oferta

```python
path('oferta/', views.oferta, name='oferta'),
```

La página se enlaza desde la navegación para usuarios con permiso de consulta:

```django
{% if perms.gestion_inmuebles.view_inmueble %}
    <a class="nav-link" href="{% url 'oferta' %}">Oferta</a>
{% endif %}
```

**Archivo:** `proyecto_inmuebles/gestion_inmuebles/urls.py`

### 3.b Vista y listado de viviendas

La vista consulta solo inmuebles disponibles, carga sus relaciones para presentarlas en la página y admite filtros por región y tipo:

```python
inmuebles = Inmueble.objects.filter(estado='disponible').select_related(
    'comuna__region', 'tipo_inmueble'
)
region_id = request.GET.get('region')
tipo_id = request.GET.get('tipo')
if region_id and region_id.isdigit():
    inmuebles = inmuebles.filter(comuna__region_id=region_id)
if tipo_id and tipo_id.isdigit():
    inmuebles = inmuebles.filter(tipo_inmueble_id=tipo_id)
```

La vista envía el listado y las opciones de filtro a la plantilla:

```python
return render(request, 'oferta.html', {
    'inmuebles': inmuebles,
    'regiones': Region.objects.order_by('nombre'),
    'tipos': TipoInmueble.objects.order_by('nombre'),
    'region_seleccionada': region_id or '',
    'tipo_seleccionado': tipo_id or '',
})
```

La vista requiere usuario autenticado con permiso de consulta. La plantilla recorre el resultado y muestra un mensaje cuando no hay coincidencias:

```python
@login_required
@permission_required('gestion_inmuebles.view_inmueble', raise_exception=True)
def oferta(request):
    ...
```

```django
{% for inmueble in inmuebles %}
    <tr>
        <td>{{ inmueble.nombre }}</td>
        <td>{{ inmueble.tipo_inmueble.nombre }}</td>
        <td>{{ inmueble.comuna.nombre }}</td>
        <td>{{ inmueble.comuna.region.nombre }}</td>
        <td>${{ inmueble.precio_mensual }}</td>
    </tr>
{% empty %}
    <tr><td colspan="6">No hay inmuebles disponibles con esos filtros.</td></tr>
{% endfor %}
```

**Archivo:** `proyecto_inmuebles/gestion_inmuebles/views.py`  
**Interfaz:** `templates/oferta.html` presenta filtros y una tabla con nombre, tipo, comuna, región, precio y descripción.

## Archivos de referencia

- `proyecto_inmuebles/gestion_inmuebles/urls.py`
- `proyecto_inmuebles/gestion_inmuebles/forms.py`
- `proyecto_inmuebles/gestion_inmuebles/views.py`
- `proyecto_inmuebles/gestion_inmuebles/templates/inmueble_form.html`
- `proyecto_inmuebles/gestion_inmuebles/templates/mis_inmuebles.html`
- `proyecto_inmuebles/gestion_inmuebles/templates/inmueble_eliminar.html`
- `proyecto_inmuebles/gestion_inmuebles/templates/oferta.html`

## Verificación

El proyecto pasó `manage.py check` sin errores y las plantillas del CRUD y de oferta compilaron correctamente. La aplicación no cuenta actualmente con pruebas automatizadas (`manage.py test gestion_inmuebles` encontró 0 pruebas).
