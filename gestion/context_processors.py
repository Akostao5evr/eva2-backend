from gestion.models import Funcionario, Delegacion

def contexto_usuario(request):
    """
    Inyecta permanentemente el funcionario, rol y delegación activa
    en todos los templates del sistema.
    """
    if not request.user.is_authenticated:
        return {}

    # Buscar si el usuario actual corresponde a un funcionario por nombre o email
    funcionario = Funcionario.objects.filter(correo=request.user.email).first()
    if not funcionario:
        funcionario = Funcionario.objects.filter(nombre__icontains=request.user.first_name).first()

    # Delegación activa (toma la del funcionario o la primera delegación registrada por defecto)
    delegacion = None
    if funcionario and funcionario.delegacion:
        delegacion = funcionario.delegacion
    else:
        delegacion = Delegacion.objects.filter(estado=True).first()

    # Rol del funcionario o superusuario
    rol_nombre = "Administrador"
    if funcionario and funcionario.cargo:
        rol_nombre = funcionario.cargo.nombre
    elif request.user.is_superuser:
        rol_nombre = "Superadministrador"

    return {
        'funcionario_activo': funcionario,
        'delegacion_activa': delegacion,
        'rol_activo': rol_nombre,
    }