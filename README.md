DOCUMENTACION TECNICA DEL SISTEMA DE GESTION DE RESULTADOS (SGR)
MUNICIPALIDAD DE LA SERENA - INACAP SEDE LA SERENA

1.DESCRIPCION GENERAL DEL PROYECTO

El Sistema de Gestion de Resultados (SGR) es una plataforma web desarrollada para la Ilustre Municipalidad de La Serena en el ambito academico de INACAP Sede La Serena. Su proposito es centralizar el control operativo, el registro de atenciones ciudadanas por delegacion territorial y la medicion de indicadores de cumplimiento mediante una arquitectura relacional, autenticacion basada en roles y despliegue en infraestructura cloud sobre Amazon Web Services (AWS EC2).


2.MODULOS Y FUNCIONALIDADES IMPLEMENTADAS

2.1. Control de Acceso y Autenticacion Basada en Roles (RBAC)

  Redireccion Raiz Automatica: La ruta principal del sistema redirige de forma obligatoria al formulario de inicio de sesion.

  Proteccion Perimetral de Rutas: Implementacion del decorador de autenticacion sobre todas las vistas operativas y administrativas para denegar el acceso a solicitudes no autenticadas.

  Segregacion Dinamica de Interfaz: En la barra de navegacion superior, los funcionarios regulares visualizan unicamente los enlaces operativos (Inicio y Atenciones). El usuario con privilegios de Administrador Global visualiza ademas los mantenedores maestros (Delegaciones, Roles, Funcionarios, Items y Metas, Tipos y Subatenciones) junto al boton de acceso al panel administrativo de Django.

2.2. Flujo Institucional de Recuperacion de Clave en 3 Pasos (OTP)

  Paso 1 (Solicitud y Generacion): El usuario ingresa su correo institucional o nombre de usuario. El backend valida la existencia de la cuenta, invalida codigos anteriores no utilizados, genera un codigo numerico OTP de 6 digitos con vigencia de 15 minutos y lo persiste en la tabla CodigoRecuperacion de MariaDB. Paralelamente, se envia el codigo por correo electronico mediante protocolo SMTP.

  Paso 2 (Validacion de Codigo): Interfaz con casilla numerica de 6 digitos. El sistema valida la coincidencia y la vigencia temporal del OTP contra la base de datos antes de permitir el paso al cambio de credenciales.

  Paso 3 (Restablecimiento Seguro): Formulario de asignacion de nueva contraseña con confirmacion obligatoria y actualizacion directa de la clave cifrada en el modelo de usuario.

2.3. Politica de Contraseñas Seguras y Alertas SweetAlert2

  Doble Validacion (Cliente y Servidor): Se aplican comprobaciones mediante expresiones regulares tanto en el navegador antes del envio como en el controlador backend para asegurar que no se vulneren los parametros requeridos.

  Criterios de Complejidad Institucional: La clave debe tener una longitud minima de 8 caracteres, al menos una letra mayuscula, al menos una letra minuscula, al menos un digito numerico y al menos un caracter especial (como arroba, signo de exclamacion, numeral, punto o guion).

  Notificaciones Interactivas: Reemplazo de alertas genericas del navegador por ventanas modales de SweetAlert2 para reportar campos vacios, falta de coincidencia, advertencias de complejidad y mensajes de confirmacion.

2.4. Atencion Ciudadana y Gestion Operativa

  Registro estructurado de atenciones ciudadanas vinculadas a la delegacion y al funcionario responsable en sesion.

  Emision automatica de codigos unicos UUID para asegurar la trazabilidad e inmutabilidad de las evidencias registradas.

  Clasificacion por estados (Pendiente, Aprobado y Rechazado) que alimentan los tableros de avance institucional.

2.5. Identidad Visual y Contexto de Usuario

  Maquetacion responsiva sobre Bootstrap 5 y tipografia Arial.

  Incorporacion del color institucional carmesi (#AD0000) en barra de navegacion y elementos de accion.

  Identificacion permanente en el Topbar: visualizacion del codigo y nombre de la delegacion activa, nombre completo del funcionario en sesion y denominacion de su rol activo.


3. ARQUITECTURA TECNOLOGICA

  Lenguaje de Programacion: Python 3.12 o superior.

  Framework Web Backend: Django 5.1 / 6.x.

  Motor de Base de Datos: MariaDB 10.11 / MySQL 8.0 sobre puerto local 3306.

  Protocolo de Correo Saliente: SMTP Gmail mediante la especificacion MAILERS con bloque OPTIONS sobre puerto 587 (TLS).

  Capa Frontend: Bootstrap 5.3, Bootstrap Icons y SweetAlert2 v11.

  Administrador de Base de Datos Web: phpMyAdmin.

  Infraestructura Cloud: Instancia Amazon Web Services (AWS) EC2 con sistema operativo Amazon Linux 2023 vinculada a IP Elastica.

  Sistema de Control de Versiones: Git y GitHub.


4. INFRAESTRUCTURA Y SERVICIOS EN AWS EC2

  La instancia EC2 mantiene los siguientes servicios y puertos en ejecucion:

  Puerto 8000 (HTTP): Servidor de aplicacion Django con el sistema SGR. La ruta raiz redirige a la vista de login.

  Ruta /admin/: Consola nativa de administracion del framework Django.

  Ruta /phpmyadmin/: Interfaz web para administracion directa de las tablas en MariaDB.

  Puerto 3306: Servicio local de MariaDB para la persistencia del sistema.

  Puerto 587 (Saliente): Canal TLS cifrado para el despacho de correos OTP hacia smtp.gmail.com.


5. GUIA DE INSTALACION, CONFIGURACION Y EJECUCION

5.1. Clonar el Repositorio
git clone https://github.com/Akostao5evr/eva2-backend.git
cd eva2-backend

5.2. Crear y Activar Entorno Virtual
python3 -m venv entorno
source entorno/bin/activate

5.3. Instalar Dependencias
pip install -r requirements.txt

5.4. Configuracion de Variables de Entorno (.env)
Crear un archivo llamado .env en la raiz del proyecto con la siguiente estructura:

  SECRET_KEY=django-insecure-tu-clave-secreta-institucional
  DEBUG=True
  ALLOWED_HOSTS=127.0.0.1,localhost,tu_ip_publica_ec2

  DB_NAME=sgr_db
  DB_USER=root
  DB_PASSWORD=TuPasswordSegura123!
  DB_HOST=127.0.0.1
  DB_PORT=3306

  EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
  EMAIL_HOST=smtp.gmail.com
  EMAIL_PORT=587
  EMAIL_USE_TLS=True
  EMAIL_HOST_USER=tu_correo_institucional@gmail.com
  EMAIL_HOST_PASSWORD=token_de_16_caracteres_de_aplicacion
  DEFAULT_FROM_EMAIL=SGR Municipalidad de La Serena no-reply@laserena.cl

  5.5. Aplicar Migraciones y Crear Administrador Inicial
  python manage.py migrate
  python manage.py createsuperuser

  5.6. Levantar Servidor Web
  python manage.py runserver 0.0.0.0:8000


6.PROCEDIMIENTO DE INTEGRACION Y DESPLIEGUE CONTINUO

  Modificacion en Entorno Local:
  Desarrollo de nuevas funcionalidades o ajustes en el computador de trabajo.

  Versionamiento y Publicacion Remota:
  git add .
  git commit -m "Mensaje descriptivo del avance"
  git push origin main

  Actualizacion en la Instancia AWS EC2:
  git pull origin main
  python manage.py migrate
  python manage.py runserver 0.0.0.0:8000