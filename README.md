SISTEMA DE GESTION DE RESULTADOS SGR - BACKEND Y DESPLIEGUE

Este repositorio contiene la implementacion backend del Sistema de Gestion de Resultados SGR, desarrollada para el entorno academico de INACAP Sede La Serena. El proyecto contempla la arquitectura de software, gestion de base de datos relacional y despliegue en la nube mediante infraestructura de Amazon Web Services AWS EC2.

DESCRIPCION DEL PROYECTO:

El SGR es una plataforma orientada a la gestion operativa, seguimiento de actividades e indicadores de cumplimiento por delegaciones y cargos institucionales.

Funcionalidades Clave Desarrolladas:
  
  CU-RF-009 Registrar Actividades: Formulario web para el ingreso de actividades operativas con asignacion de funcionario y delegacion.
  
  CU-RF-011 Generar Codigo de Evidencia: Generacion automatica de codigos unicos e inmutables UUID para trazabilidad de evidencias.
  
  CU-RF-013 y CU-RF-014 Validacion de Evidencias: Control de estados Pendiente, Aprobado y Rechazado que impactan en los indicadores de avance.
  
  CU-RF-027 y CU-RF-028 Tablero y Semaforo de Avance: Visualizacion del estado de cumplimiento respecto a las metas configuradas.
  
  Gestion de Base de Datos: Persistencia relacional completa integrada a phpMyAdmin para la administracion de datos en tiempo real.

ARQUITECTURA Y TECNOLOGIAS:

  Lenguaje: Python 3.12 o superior
  
  Framework Backend: Django 5.1 o superior
  
  Base de Datos: MariaDB 10.11 o superior y MySQL 8.0
  
  Administrador de Base de Datos: phpMyAdmin
  
  Servidor Web e Infraestructura: Apache httpd sobre AWS EC2 con Amazon Linux 2023
  
  Control de Versiones: Git y GitHub
  
  DESPLIEGUE EN AWS EC2

  La infraestructura fue desplegada en una instancia EC2 en Amazon Linux 2023 vinculada a una IP Elastica publica para garantizar el acceso continuo a los servicios.
  
  Estructura de Servicios en la Instancia:
  
  Aplicacion Django: Servidor web del SGR en el puerto 8000
  
  Panel Django Admin: Panel de administracion en la ruta /admin/
  
  phpMyAdmin: Interfaz grafica para MariaDB en la ruta /phpmyadmin/
  
  MariaDB: Motor de base de datos relacional en localhost puerto 3306

GUIA DE INSTALACION Y EJECUCION

  Clonar el repositorio:
  git clone https://github.com/Akostao5evr/eva2-backend.git
  cd eva2-backend
  
  Crear y activar el entorno virtual:
  python3 -m venv entorno
  source entorno/bin/activate
  
  Instalar dependencias:
  pip install -r requirements.txt
  
  Configurar variables de entorno creando un archivo .env en la raiz del proyecto:
  SECRET_KEY=django-insecure-tu-clave-secreta
  DEBUG=True
  ALLOWED_HOSTS=*
  DB_NAME=sgr_db
  DB_USER=root
  DB_PASSWORD=TuPasswordSegura123!
  DB_HOST=127.0.0.1
  DB_PORT=3306
  
  Ejecutar migraciones e iniciar servidor:
  python manage.py migrate
  python manage.py createsuperuser
  python manage.py runserver 0.0.0.0:8000

FLUJO DE DESARROLLO E INTEGRACION CONTINUA

  El proyecto sigue un flujo estricto de control de versiones para asegurar la integridad en el servidor de produccion EC2:
  
  Desarrollo Local: Modificacion de codigo, modelos y vistas en el computador personal.
  
  Sube a GitHub:
  git add .
  git commit -m "Descripcion del cambio"
  git push origin main
  
  Actualizacion en EC2:
  git pull origin main
  python manage.py migrate
  python manage.py runserver 0.0.0.0:8000
