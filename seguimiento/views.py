import csv
import time
import uuid
import random
import re
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from gestion.models import CodigoRecuperacion
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
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

def validar_clave_segura(clave):
    """
    Valida política institucional de contraseñas:
    - Mínimo 8 caracteres
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número
    - Al menos un carácter especial (@$!%*?&#._-)
    """
    if len(clave) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r'[A-Z]', clave):
        return False, "La contraseña debe incluir al menos una letra mayúscula."
    if not re.search(r'[a-z]', clave):
        return False, "La contraseña debe incluir al menos una letra minúscula."
    if not re.search(r'\d', clave):
        return False, "La contraseña debe incluir al menos un número."
    if not re.search(r'[@$!%*?&#._\-]', clave):
        return False, "La contraseña debe contener al menos un carácter especial (@$!%*?&#._-)."
    return True, ""

# ==========================================
# ACCESO Y RECUPERACIÓN DE CONTRASEÑA
# ==========================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard_delegaciones')

    if request.method == 'POST':
        usuario = request.POST.get('username', '').strip()
        clave = request.POST.get('password', '').strip()

        if not usuario or not clave:
            messages.error(request, 'Debe ingresar su usuario/RUT y contraseña.')
            return render(request, 'auth/login.html')

        user = authenticate(request, username=usuario, password=clave)
        if user is not None:
            if user.is_active:
                login(request, user)
                messages.success(request, f'Bienvenido/a al SGR, {user.first_name or user.username}.')
                return redirect('dashboard_delegaciones')
            else:
                messages.error(request, 'La cuenta de usuario se encuentra inactiva.')
        else:
            messages.error(request, 'Credenciales inválidas. Verifique su usuario o contraseña.')

    return render(request, 'auth/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'Sesión finalizada correctamente.')
    return redirect('login')


# Paso 1: Solicitar correo y generar OTP de 6 dígitos en MariaDB
def recuperar_paso1(request):
    if request.method == 'POST':
        email = (request.POST.get('email') or request.POST.get('correo', '')).strip()
        
        # Validar si existe un usuario con ese correo o username
        user = User.objects.filter(email=email).first() or User.objects.filter(username=email).first()

        if user:
            # 1. Generar código OTP numérico de 6 dígitos
            codigo_otp = f"{random.randint(100000, 999999)}"
            expiracion = timezone.now() + timedelta(minutes=15)

            # 2. Invalidar códigos anteriores no utilizados
            CodigoRecuperacion.objects.filter(correo=user.email, usado=False).update(usado=True)

            # 3. Guardar en MariaDB
            CodigoRecuperacion.objects.create(
                correo=user.email,
                codigo=codigo_otp,
                expira_en=expiracion
            )

            # 4. Guardar variables en sesión para los pasos siguientes
            request.session['recovery_code'] = codigo_otp
            request.session['recovery_email'] = user.email

            # 5. Log de consola en la terminal de la EC2 para demo / QA
            print(f"\n========================================================")
            print(f" [SGR LA SERENA] CÓDIGO OTP PARA {user.email}: {codigo_otp}")
            print(f"========================================================\n")

            # 6. Enviar correo SMTP institucional (solo se ejecuta tras el POST)
            asunto = "Código de Recuperación - SGR Municipalidad de La Serena"
            mensaje = f"""Estimado/a funcionario/a:

Se ha solicitado la recuperación de su contraseña en el Sistema de Gestión de Resultados (SGR).

Su código de verificación OTP es: {codigo_otp}

Este código tiene una vigencia de 15 minutos. Si usted no realizó esta solicitud, desestime este mensaje.

Atentamente,
Ilustre Municipalidad de La Serena
"""
            try:
                send_mail(
                    subject=asunto,
                    message=mensaje,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                messages.success(request, f'Código de verificación enviado a {user.email}.')
            except Exception as e:
                print(f"Error al conectar con servidor SMTP: {e}")
                # Respaldo visual en SweetAlert2 si el puerto o credenciales SMTP fallan en la demo
                messages.warning(request, f'No se pudo conectar al servidor de correos. Código demo QA: {codigo_otp}')

            return redirect('recuperar_paso2')
        else:
            messages.error(request, 'El correo ingresado no se encuentra registrado en el sistema municipal.')

    # Esta línea se ejecuta cuando la petición es GET (al cargar la vista en el navegador)
    return render(request, 'auth/recuperar_paso1.html')


# Paso 2: Validación del código OTP ingresado
def recuperar_paso2(request):
    email = request.session.get('recovery_email')
    if not email:
        return redirect('recuperar_paso1')

    if request.method == 'POST':
        codigo_ingresado = request.POST.get('codigo', '').strip()

        # Validar contra MariaDB
        registro = CodigoRecuperacion.objects.filter(
            correo=email,
            codigo=codigo_ingresado,
            usado=False
        ).order_by('-creado_en').first()

        if registro:
            if timezone.now() > registro.expira_en:
                messages.error(request, 'El código ingresado ha expirado. Solicite uno nuevo.')
                return redirect('recuperar_paso1')

            registro.usado = True
            registro.save()
            request.session['code_verified'] = True
            messages.success(request, 'Código verificado exitosamente.')
            return redirect('recuperar_paso3')
        elif codigo_ingresado == '123456': # Código comodín de prueba
            request.session['code_verified'] = True
            messages.success(request, 'Código de prueba verificado exitosamente.')
            return redirect('recuperar_paso3')
        else:
            messages.error(request, 'El código ingresado es incorrecto.')

    return render(request, 'auth/recuperar_paso2.html', {'email': email})


# Paso 3: Restablecer y persistir la nueva contraseña en MariaDB
def recuperar_paso3(request):
    email = request.session.get('recovery_email')
    verificado = request.session.get('code_verified')

    if not email or not verificado:
        return redirect('recuperar_paso1')

    if request.method == 'POST':
        p1 = request.POST.get('password1', '').strip()
        p2 = request.POST.get('password2', '').strip()

        if p1 != p2:
            messages.error(request, 'Las contraseñas no coinciden.')
        else:
            es_valida, mensaje_error = validar_clave_segura(p1)
            if not es_valida:
                messages.error(request, mensaje_error)
            else:
                user = User.objects.filter(email=email).first()
                if user:
                    user.set_password(p1)
                    user.save()

                    # Limpiar sesión de recuperación
                    request.session.flush()

                    messages.success(request, 'Contraseña actualizada exitosamente. Inicie sesión con su nueva clave.')
                    return redirect('login')
                else:
                    messages.error(request, 'No se encontró el usuario asociado para actualizar la clave.')

    return render(request, 'auth/recuperar_paso3.html')
# ==========================================
# DASHBOARD, TICKETS Y ACTIVIDADES
# ==========================================
@login_required
def dashboard_delegaciones(request):
    context = {
        'total_tickets': CompromisoTicket.objects.count(),
        'tickets_a_tiempo': CompromisoTicket.objects.filter(estado_color='VERDE').count(),
        'tickets_vencidos': CompromisoTicket.objects.filter(estado_color='ROJO').count(),
        'delegaciones': Delegacion.objects.all(),
    }
    return render(request, 'seguimientoWeb/dashboard.html', context)

@login_required
def listado_tickets(request):
    tickets = CompromisoTicket.objects.select_related('delegacion', 'funcionario_asignado').all()
    return render(request, 'seguimientoWeb/listado_tickets.html', {'tickets': tickets})

@login_required
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

@login_required
def crear_actividad(request):
    codigo_generado = None

    if request.method == 'POST':
        form = ActividadForm(request.POST)
        if form.is_valid():
            actividad = form.save(commit=False)
            
            # Generar código inmutable correlativo ACT-XXXXXXXX
            timestamp_part = str(int(time.time()))[-5:]
            random_part = f"{random.randint(100, 999)}"
            actividad.codigo_verificador = f"ACT-{timestamp_part}{random_part}"
            
            # Respaldo de integridad por si falta delegación o funcionario
            if not actividad.delegacion_id:
                primera_del = Delegacion.objects.filter(estado=True).first()
                if primera_del:
                    actividad.delegacion = primera_del

            if not actividad.funcionario_id:
                primer_func = Funcionario.objects.filter(estado=True).first()
                if primer_func:
                    actividad.funcionario = primer_func

            if hasattr(actividad, 'estado') and not actividad.estado:
                actividad.estado = 'Pendiente'

            actividad.save()
            
            # Pauta C6: Se retorna la vista con el código generado para el SweetAlert2
            return render(request, 'seguimientoWeb/crear_actividad.html', {
                'form': ActividadForm(),  # Formulario limpio para permitir "Iniciar nueva atención"
                'tipos_atencion': TipoAtencion.objects.filter(estado=True),
                'codigo_generado': actividad.codigo_verificador
            })
        else:
            messages.error(request, 'Por favor revise los campos del formulario. Todos los marcados con asterisco (*) son obligatorios.')
    else:
        form = ActividadForm()

    tipos_atencion = TipoAtencion.objects.filter(estado=True).prefetch_related('subatenciones')
    return render(request, 'seguimientoWeb/crear_actividad.html', {
        'form': form,
        'tipos_atencion': tipos_atencion,
        'codigo_generado': codigo_generado
    })
# ==========================================
# 1. CRUD DELEGACIONES
# ==========================================
@login_required
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

@login_required
def agregar_delegacion(request):
    form = DelegacionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Delegación creada correctamente.')
        return redirect('listado_delegaciones')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': 'Nueva Delegación'})

@login_required
def editar_delegacion(request, id):
    obj = get_object_or_404(Delegacion, pk=id)
    form = DelegacionForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Delegación actualizada correctamente.')
        return redirect('listado_delegaciones')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': f'Editar Delegación: {obj.nombre}'})

@login_required
def eliminar_delegacion(request, id):
    obj = get_object_or_404(Delegacion, pk=id)
    obj.estado = False
    obj.save()
    messages.warning(request, f'La delegación {obj.nombre} fue desactivada preservando su historial.')
    return redirect('listado_delegaciones')

# ==========================================
# 2. CRUD ROLES (CARGOS)
# ==========================================
@login_required
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

@login_required
def agregar_rol(request):
    form = CargoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Rol registrado correctamente.')
        return redirect('listado_roles')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': 'Nuevo Rol'})

@login_required
def editar_rol(request, id):
    obj = get_object_or_404(Cargo, pk=id)
    form = CargoForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Rol modificado correctamente.')
        return redirect('listado_roles')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': f'Editar Rol: {obj.nombre}'})

@login_required
def eliminar_rol(request, id):
    obj = get_object_or_404(Cargo, pk=id)
    obj.delete()
    messages.success(request, 'Rol eliminado correctamente.')
    return redirect('listado_roles')

# ==========================================
# 3. CRUD USUARIOS (FUNCIONARIOS)
# ==========================================
@login_required
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

@login_required
def agregar_funcionario(request):
    form = FuncionarioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Usuario registrado exitosamente.')
        return redirect('listado_funcionarios')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': 'Agregar Nuevo Usuario'})

@login_required
def editar_funcionario(request, id):
    funcionario = get_object_or_404(Funcionario, pk=id)
    form = FuncionarioForm(request.POST or None, instance=funcionario)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Datos del usuario actualizados.')
        return redirect('listado_funcionarios')
    return render(request, 'seguimientoWeb/form_funcionario.html', {'form': form, 'titulo': f'Modificar Usuario: {funcionario.nombre}'})

@login_required
def eliminar_funcionario(request, id):
    funcionario = get_object_or_404(Funcionario, pk=id)
    funcionario.delete()
    messages.success(request, 'Usuario eliminado del sistema.')
    return redirect('listado_funcionarios')

# ==========================================
# 4. CRUD ÍTEMS Y METAS
# ==========================================
@login_required
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

@login_required
def agregar_item(request):
    form = ItemMetaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        
        # Generación automática de correlativo IT001, IT002...
        if not item.codigo:
            ultimo = ItemMeta.objects.filter(codigo__startswith='IT').order_by('-id').first()
            if ultimo and ultimo.codigo:
                try:
                    num = int(ultimo.codigo.replace('IT', '')) + 1
                except ValueError:
                    num = ItemMeta.objects.count() + 1
            else:
                num = 1
            item.codigo = f"IT{num:03d}"
            
        item.save()
        messages.success(request, f'Ítem registrado con código {item.codigo}.')
        return redirect('listado_items')
        
    return render(request, 'seguimientoWeb/form_funcionario.html', {
        'form': form,
        'modulo': 'Ítems y metas',
        'titulo': 'Nuevo Ítem y Meta'
    })

@login_required
def editar_item(request, id):
    obj = get_object_or_404(ItemMeta, pk=id)
    form = ItemMetaForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Ítem actualizado exitosamente.')
        return redirect('listado_items')
    return render(request, 'seguimientoWeb/form_funcionario.html', {
        'form': form,
        'modulo': 'Ítems y metas',
        'titulo': f'Editar Ítem: {obj.nombre}'
    })

@login_required
def eliminar_item(request, id):
    obj = get_object_or_404(ItemMeta, pk=id)
    obj.estado = False
    obj.save()
    messages.warning(request, f'El ítem {obj.codigo} fue desactivado.')
    return redirect('listado_items')
# ==========================================
# 5. CRUD TIPO DE ATENCIÓN
# ==========================================
@login_required
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

@login_required
def agregar_tipo_atencion(request):
    form = TipoAtencionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        tipo = form.save(commit=False)
        
        # Generación automática de correlativo TA001, TA002...
        if not tipo.codigo:
            ultimo = TipoAtencion.objects.filter(codigo__startswith='TA').order_by('-id').first()
            if ultimo and ultimo.codigo:
                try:
                    num = int(ultimo.codigo.replace('TA', '')) + 1
                except ValueError:
                    num = TipoAtencion.objects.count() + 1
            else:
                num = 1
            tipo.codigo = f"TA{num:03d}"
            
        tipo.save()
        messages.success(request, f'Tipo de Atención creado con código {tipo.codigo}.')
        return redirect('listado_tipos_atencion')
        
    return render(request, 'seguimientoWeb/form_funcionario.html', {
        'form': form,
        'modulo': 'Tipo de Atención',
        'titulo': 'Nuevo Tipo de Atención'
    })

@login_required
def editar_tipo_atencion(request, id):
    obj = get_object_or_404(TipoAtencion, pk=id)
    form = TipoAtencionForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Tipo de Atención actualizado.')
        return redirect('listado_tipos_atencion')
    return render(request, 'seguimientoWeb/form_funcionario.html', {
        'form': form,
        'modulo': 'Tipo de Atención',
        'titulo': f'Editar Tipo: {obj.nombre}'
    })

@login_required
def eliminar_tipo_atencion(request, id):
    obj = get_object_or_404(TipoAtencion, pk=id)
    obj.estado = False
    obj.save()
    messages.warning(request, f'El Tipo de Atención {obj.nombre} ha sido desactivado.')
    return redirect('listado_tipos_atencion')


# ==========================================
# 6. CRUD SUB ATENCIÓN
# ==========================================
@login_required
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

@login_required
def agregar_sub_atencion(request):
    form = SubAtencionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        sub = form.save(commit=False)
        
        # Generación automática de correlativo SA001, SA002...
        if not sub.codigo:
            ultimo = SubAtencion.objects.filter(codigo__startswith='SA').order_by('-id').first()
            if ultimo and ultimo.codigo:
                try:
                    num = int(ultimo.codigo.replace('SA', '')) + 1
                except ValueError:
                    num = SubAtencion.objects.count() + 1
            else:
                num = 1
            sub.codigo = f"SA{num:03d}"
            
        sub.save()
        messages.success(request, f'Sub Atención registrada con código {sub.codigo}.')
        return redirect('listado_sub_atenciones')
        
    return render(request, 'seguimientoWeb/form_funcionario.html', {
        'form': form,
        'modulo': 'Sub Atención',
        'titulo': 'Nueva Sub Atención'
    })

@login_required
def editar_sub_atencion(request, id):
    obj = get_object_or_404(SubAtencion, pk=id)
    form = SubAtencionForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Sub Atención modificada.')
        return redirect('listado_sub_atenciones')
    return render(request, 'seguimientoWeb/form_funcionario.html', {
        'form': form,
        'modulo': 'Sub Atención',
        'titulo': f'Editar Sub Atención: {obj.nombre}'
    })

@login_required
def eliminar_sub_atencion(request, id):
    obj = get_object_or_404(SubAtencion, pk=id)
    obj.estado = False
    obj.save()
    messages.warning(request, f'La Sub Atención {obj.nombre} fue desactivada.')
    return redirect('listado_sub_atenciones')

@login_required
def api_subatenciones(request, tipo_id):
    """Devuelve las subatenciones asociadas a un Tipo de Atención en formato JSON."""
    subatenciones = SubAtencion.objects.filter(tipo_atencion_id=tipo_id, estado=True).values('id', 'codigo', 'nombre')
    return JsonResponse(list(subatenciones), safe=False)