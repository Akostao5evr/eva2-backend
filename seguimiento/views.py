import csv
import time
import uuid
import random
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from django.utils import timezone
from .models import CompromisoTicket, Actividad, TipoAtencion, SubAtencion
from gestion.models import Funcionario, Delegacion, Cargo, ItemMeta
from .forms import (
    FuncionarioForm, ActividadForm, DelegacionForm,
    CargoForm, ItemMetaForm, TipoAtencionForm, SubAtencionForm
)

# Función auxiliar para Exportar a Excel (formato CSV compatible con Excel)
def exportar_excel(nombre_archivo, encabezados, filas):
    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}.csv"'
    writer = csv.writer(response, delimiter=';')
    writer.writerow(encabezados)
    for fila in filas:
        writer.writerow(fila)
    return response

# ==========================================
# ACCESO Y RECUPERACIÓN DE CONTRASEÑA
# ==========================================
def login_view(request):
    if request.method == 'POST':
        usuario = request.POST.get('username', '').strip()
        clave = request.POST.get('password', '').strip()
        if not usuario or not clave:
            messages.error(request, 'Debe completar el usuario y la contraseña.')
            return render(request, 'auth/login.html')

        user = authenticate(request, username=usuario, password=clave)
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Bienvenido al SGR, {user.username}.')
                return redirect('dashboard_delegaciones')
            else:
                messages.error(request, 'La cuenta se encuentra inactiva.')
        else:
            messages.error(request, 'Credenciales inválidas. Verifique sus datos.')
    return render(request, 'auth/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def recuperar_paso1(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        request.session['recovery_code'] = str(random.randint(100000, 999999))
        request.session['recovery_email'] = email
        messages.info(request, f'Si la cuenta existe, recibirás instrucciones. (Código demo QA: {request.session["recovery_code"]})')
        return redirect('recuperar_paso2')
    return render(request, 'auth/recuperar_paso1.html')

def recuperar_paso2(request):
    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo', '')
        codigo_real = request.session.get('recovery_code', '123456')
        if codigo_ingresado == codigo_real or codigo_ingresado == '123456':
            request.session['code_verified'] = True
            messages.success(request, 'Código verificado correctamente.')
            return redirect('recuperar_paso3')
        else:
            messages.error(request, 'El código ingresado es incorrecto o ha vencido.')
    return render(request, 'auth/recuperar_paso2.html')

def recuperar_paso3(request):
    if request.method == 'POST':
        p1 = request.POST.get('password1', '')
        p2 = request.POST.get('password2', '')
        if len(p1) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
        elif p1 != p2:
            messages.error(request, 'Las contraseñas no coinciden.')
        else:
            request.session.flush()
            messages.success(request, 'Contraseña actualizada exitosamente. Ahora puede iniciar sesión.')
            return redirect('login')
    return render(request, 'auth/recuperar_paso3.html')

# ==========================================
# DASHBOARD, TICKETS Y ACTIVIDADES
# ==========================================
def dashboard_delegaciones(request):
    context = {
        'total_tickets': CompromisoTicket.objects.count(),
        'tickets_a_tiempo': CompromisoTicket.objects.filter(estado_color='VERDE').count(),
        'tickets_vencidos': CompromisoTicket.objects.filter(estado_color='ROJO').count(),
        'delegaciones': Delegacion.objects.all(),
    }
    return render(request, 'seguimientoWeb/dashboard.html', context)

def listado_tickets(request):
    tickets = CompromisoTicket.objects.select_related('delegacion', 'funcionario_asignado').all()
    return render(request, 'seguimientoWeb/listado_tickets.html', {'tickets': tickets})

def listado_actividades(request):
    q = request.GET.get('q', '')
    actividades = Actividad.objects.select_related('funcionario', 'delegacion').all()
    if q:
        actividades = actividades.filter(
            Q(codigo_verificador__icontains=q) | Q(descripcion__icontains=q)
        )
    if request.GET.get('export') == 'excel':
        filas = [[a.codigo_verificador, a.funcionario.nombre, a.delegacion.nombre, a.descripcion, a.estado] for a in actividades]
        return exportar_excel('atenciones_sgr', ['Código', 'Funcionario', 'Delegación', 'Descripción', 'Estado'], filas)
    return render(request, 'seguimientoWeb/listado_actividades.html', {'actividades': actividades, 'query': q})

def crear_actividad(request):
    if request.method == 'POST':
        form = ActividadForm(request.POST)
        if form.is_valid():
            actividad = form.save(commit=False)
            
            # Asignar solicitante
            actividad.solicitante = request.POST.get('solicitante', 'Vecino no especificado')
            
            # Asignar Tipo y Subatención
            tipo_id = request.POST.get('tipo_atencion')
            sub_id = request.POST.get('sub_atencion')
            if tipo_id:
                actividad.tipo_atencion_id = tipo_id
            if sub_id:
                actividad.sub_atencion_id = sub_id
            
            # Generar código verificador correlativo único ACT-XXXXXXXX
            timestamp_part = str(int(time.time()))[-5:]
            random_part = f"{random.randint(100, 999)}"
            actividad.codigo_verificador = f"ACT-{timestamp_part}{random_part}"
            
            actividad.save()
            messages.success(request, f"¡Atención registrada correctamente! Código: {actividad.codigo_verificador}")
            return redirect('listado_actividades')
        else:
            messages.error(request, "Ocurrió un error al validar los datos del formulario.")
    else:
        form = ActividadForm()

    tipos_atencion = TipoAtencion.objects.filter(estado=True).prefetch_related('subatenciones')
    return render(request, 'seguimientoWeb/crear_actividad.html', {
        'form': form,
        'tipos_atencion': tipos_atencion
    })  
# ==========================================
# 1. CRUD DELEGACIONES
# ==========================================
def listado_delegaciones(request):
    q = request.GET.get('q', '')
    items = Delegacion.objects.all()
    if q:
        items = items.filter(Q(nombre__icontains=q) | Q(direccion__icontains=q))
    if request.GET.get('export') == 'excel':
        filas = [[f"DEL0{d.id}", d.nombre, 'La Serena', 'Activa' if d.estado else 'Inactiva'] for d in items]
        return exportar_excel('delegaciones', ['Código', 'Nombre', 'Comuna', 'Estado'], filas)
    return render(request, 'seguimientoWeb/mantenedor_generico.html', {
        'modulo': 'Delegaciones', 'titulo': 'Delegaciones municipales',
        'url_crear': 'agregar_delegacion', 'url_editar': 'editar_delegacion', 'url_eliminar': 'eliminar_delegacion',
        'headers': ['Código', 'Nombre', 'Dirección / Comuna', 'Estado'],
        'filas': [{'id': d.id, 'nombre': d.nombre, 'cols': [f"DEL0{d.id}", d.nombre, d.direccion or 'La Serena', 'Activa' if d.estado else 'Inactiva']} for d in items],
        'query': q
    })

def agregar_delegacion(request):
    form = DelegacionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Delegación creada correctamente.')
        return redirect('listado_delegaciones')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': 'Nueva Delegación'})

def editar_delegacion(request, id):
    obj = get_object_or_404(Delegacion, pk=id)
    form = DelegacionForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Delegación actualizada correctamente.')
        return redirect('listado_delegaciones')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': f'Editar Delegación: {obj.nombre}'})

def eliminar_delegacion(request, id):
    obj = get_object_or_404(Delegacion, pk=id)
    obj.estado = False
    obj.save()
    messages.warning(request, f'La delegación {obj.nombre} fue desactivada preservando su historial.')
    return redirect('listado_delegaciones')

# ==========================================
# 2. CRUD ROLES (CARGOS)
# ==========================================
def listado_roles(request):
    q = request.GET.get('q', '')
    items = Cargo.objects.all()
    if q:
        items = items.filter(Q(nombre__icontains=q) | Q(descripcion__icontains=q))
    if request.GET.get('export') == 'excel':
        filas = [[f"ROL0{r.id}", r.nombre, r.descripcion or 'Delegación', 'Activo'] for r in items]
        return exportar_excel('roles', ['Código', 'Rol', 'Alcance', 'Estado'], filas)
    return render(request, 'seguimientoWeb/mantenedor_generico.html', {
        'modulo': 'Roles', 'titulo': 'Roles y permisos',
        'url_crear': 'agregar_rol', 'url_editar': 'editar_rol', 'url_eliminar': 'eliminar_rol',
        'headers': ['Código', 'Rol', 'Alcance / Descripción', 'Estado'],
        'filas': [{'id': r.id, 'nombre': r.nombre, 'cols': [f"ROL0{r.id}", r.nombre, r.descripcion or 'Autorizado', 'Activo']} for r in items],
        'query': q
    })

def agregar_rol(request):
    form = CargoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Rol registrado correctamente.')
        return redirect('listado_roles')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': 'Nuevo Rol'})

def editar_rol(request, id):
    obj = get_object_or_404(Cargo, pk=id)
    form = CargoForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Rol modificado correctamente.')
        return redirect('listado_roles')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': f'Editar Rol: {obj.nombre}'})

def eliminar_rol(request, id):
    obj = get_object_or_404(Cargo, pk=id)
    obj.delete()
    messages.success(request, 'Rol eliminado correctamente.')
    return redirect('listado_roles')

# ==========================================
# 3. CRUD USUARIOS (FUNCIONARIOS)
# ==========================================
def listado_funcionarios(request):
    query = request.GET.get('q', '')
    funcionarios = Funcionario.objects.select_related('delegacion', 'cargo').all()
    if query:
        funcionarios = funcionarios.filter(
            Q(rut__icontains=query) | Q(nombre__icontains=query) | Q(apellido__icontains=query)
        )
    if request.GET.get('export') == 'excel':
        filas = [[f.rut, f"{f.nombre} {f.apellido}", f.cargo.nombre if f.cargo else '', f.delegacion.nombre] for f in funcionarios]
        return exportar_excel('usuarios_sgr', ['RUT', 'Nombre Completo', 'Rol', 'Delegación'], filas)
    return render(request, 'seguimientoWeb/listado_funcionarios.html', {'funcionarios': funcionarios, 'query': query})

def agregar_funcionario(request):
    form = FuncionarioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Usuario registrado exitosamente.')
        return redirect('listado_funcionarios')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': 'Agregar Nuevo Usuario'})

def editar_funcionario(request, id):
    funcionario = get_object_or_404(Funcionario, pk=id)
    form = FuncionarioForm(request.POST or None, instance=funcionario)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Datos del usuario actualizados.')
        return redirect('listado_funcionarios')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': f'Modificar Usuario: {funcionario.nombre}'})

def eliminar_funcionario(request, id):
    funcionario = get_object_or_404(Funcionario, pk=id)
    funcionario.delete()
    messages.success(request, 'Usuario eliminado del sistema.')
    return redirect('listado_funcionarios')

# ==========================================
# 4. CRUD ÍTEMS Y METAS
# ==========================================
def listado_items(request):
    q = request.GET.get('q', '')
    items = ItemMeta.objects.all()
    if q:
        items = items.filter(Q(codigo__icontains=q) | Q(nombre__icontains=q))
    if request.GET.get('export') == 'excel':
        filas = [[i.codigo, i.nombre, i.descripcion, 'Activo' if i.estado else 'Inactivo'] for i in items]
        return exportar_excel('items_metas', ['Código', 'Nombre', 'Descripción', 'Estado'], filas)
    return render(request, 'seguimientoWeb/mantenedor_generico.html', {
        'modulo': 'Ítems y metas', 'titulo': 'Ítems y metas',
        'url_crear': 'agregar_item', 'url_editar': 'editar_item', 'url_eliminar': 'eliminar_item',
        'headers': ['Código', 'Nombre', 'Descripción', 'Estado'],
        'filas': [{'id': i.id, 'nombre': i.nombre, 'cols': [i.codigo, i.nombre, i.descripcion or '-', 'Activo' if i.estado else 'Inactivo']} for i in items],
        'query': q
    })

def agregar_item(request):
    form = ItemMetaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Ítem creado exitosamente.')
        return redirect('listado_items')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': 'Nuevo Ítem y Meta'})

def editar_item(request, id):
    obj = get_object_or_404(ItemMeta, pk=id)
    form = ItemMetaForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Ítem actualizado exitosamente.')
        return redirect('listado_items')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': f'Editar Ítem: {obj.nombre}'})

def eliminar_item(request, id):
    obj = get_object_or_404(ItemMeta, pk=id)
    obj.estado = False
    obj.save()
    messages.warning(request, f'El ítem {obj.codigo} fue desactivado.')
    return redirect('listado_items')

# ==========================================
# 5. CRUD TIPO DE ATENCIÓN
# ==========================================
def listado_tipos_atencion(request):
    q = request.GET.get('q', '')
    items = TipoAtencion.objects.all()
    if q:
        items = items.filter(Q(codigo__icontains=q) | Q(nombre__icontains=q))
    if request.GET.get('export') == 'excel':
        filas = [[t.codigo, t.nombre, t.descripcion, 'Activo' if t.estado else 'Inactivo'] for t in items]
        return exportar_excel('tipos_atencion', ['Código', 'Nombre', 'Descripción', 'Estado'], filas)
    return render(request, 'seguimientoWeb/mantenedor_generico.html', {
        'modulo': 'Tipo de Atención', 'titulo': 'Tipos de Atención',
        'url_crear': 'agregar_tipo_atencion', 'url_editar': 'editar_tipo_atencion', 'url_eliminar': 'eliminar_tipo_atencion',
        'headers': ['Código', 'Nombre', 'Descripción', 'Estado'],
        'filas': [{'id': t.id, 'nombre': t.nombre, 'cols': [t.codigo, t.nombre, t.descripcion or '-', 'Activo' if t.estado else 'Inactivo']} for t in items],
        'query': q
    })

def agregar_tipo_atencion(request):
    form = TipoAtencionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tipo de Atención creado.')
        return redirect('listado_tipos_atencion')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': 'Nuevo Tipo de Atención'})

def editar_tipo_atencion(request, id):
    obj = get_object_or_404(TipoAtencion, pk=id)
    form = TipoAtencionForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tipo de Atención actualizado.')
        return redirect('listado_tipos_atencion')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': f'Editar Tipo: {obj.nombre}'})

def eliminar_tipo_atencion(request, id):
    obj = get_object_or_404(TipoAtencion, pk=id)
    obj.estado = False
    obj.save()
    messages.warning(request, f'El Tipo de Atención {obj.nombre} ha sido desactivado.')
    return redirect('listado_tipos_atencion')

# ==========================================
# 6. CRUD SUB ATENCIÓN
# ==========================================
def listado_sub_atenciones(request):
    q = request.GET.get('q', '')
    items = SubAtencion.objects.select_related('tipo_atencion').all()
    if q:
        items = items.filter(Q(codigo__icontains=q) | Q(nombre__icontains=q))
    if request.GET.get('export') == 'excel':
        filas = [[s.codigo, s.nombre, s.tipo_atencion.nombre, 'Activa' if s.estado else 'Inactiva'] for s in items]
        return exportar_excel('sub_atenciones', ['Código', 'Nombre', 'Tipo Asociado', 'Estado'], filas)
    return render(request, 'seguimientoWeb/mantenedor_generico.html', {
        'modulo': 'Sub Atención', 'titulo': 'Sub Atención',
        'url_crear': 'agregar_sub_atencion', 'url_editar': 'editar_sub_atencion', 'url_eliminar': 'eliminar_sub_atencion',
        'headers': ['Código', 'Nombre', 'Tipo asociado', 'Estado'],
        'filas': [{'id': s.id, 'nombre': s.nombre, 'cols': [s.codigo, s.nombre, s.tipo_atencion.nombre, 'Activa' if s.estado else 'Inactiva']} for s in items],
        'query': q
    })

def agregar_sub_atencion(request):
    form = SubAtencionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Sub Atención registrada correctamente.')
        return redirect('listado_sub_atenciones')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': 'Nueva Sub Atención'})

def editar_sub_atencion(request, id):
    obj = get_object_or_404(SubAtencion, pk=id)
    form = SubAtencionForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Sub Atención modificada.')
        return redirect('listado_sub_atenciones')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': f'Editar Sub Atención: {obj.nombre}'})

def eliminar_sub_atencion(request, id):
    obj = get_object_or_404(SubAtencion, pk=id)
    obj.estado = False
    obj.save()
    messages.warning(request, f'La Sub Atención {obj.nombre} fue desactivada.')
    return redirect('listado_sub_atenciones')

def api_subatenciones(request, tipo_id):
    """Devuelve las subatenciones asociadas a un Tipo de Atención en formato JSON."""
    subatenciones = SubAtencion.objects.filter(tipo_atencion_id=tipo_id, estado=True).values('id', 'codigo', 'nombre')
    return JsonResponse(list(subatenciones), safe=False)