"""
Configuración de logging para Django
Incluye formatters personalizados y handlers de email
"""
import os
from pathlib import Path
from django.utils.log import AdminEmailHandler


# Directorio base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Crear directorio de logs si no existe
os.makedirs(LOG_DIR, exist_ok=True)


class ColorFormatter:
    """
    Formatter personalizado que agrega colores ANSI a los logs en consola
    """
    COLORS = {
        'INFO': '\033[92m',      # Verde
        'DEBUG': '\033[94m',     # Azul
        'WARNING': '\033[93m',   # Amarillo
        'ERROR': '\033[91m',     # Rojo
        'CRITICAL': '\033[41m',  # Fondo rojo
        'RESET': '\033[0m',
    }

    def __init__(self, fmt):
        self.fmt = fmt

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        msg = self.fmt.format(
            levelname=record.levelname,
            asctime=self.formatTime(record),
            module=record.module,
            message=record.getMessage()
        )
        return f"{color}{msg}{reset}"

    def formatTime(self, record, datefmt=None):
        from datetime import datetime
        ct = datetime.fromtimestamp(record.created)
        if datefmt:
            return ct.strftime(datefmt)
        else:
            return ct.strftime("%Y-%m-%d %H:%M:%S")


class CustomAdminEmailHandler(AdminEmailHandler):
    """
    Handler personalizado para enviar emails con formato HTML mejorado
    """
    def emit(self, record):
        # Personaliza el mensaje del correo
        record.message = f"""
        <h2>Error en Django</h2>
        <b>Tipo:</b> {record.levelname}<br>
        <b>Mensaje:</b> {record.getMessage()}<br>
        <b>Ruta:</b> {getattr(record, 'pathname', '')}<br>
        <b>Línea:</b> {getattr(record, 'lineno', '')}<br>
        <b>Función:</b> {getattr(record, 'funcName', '')}<br>
        <b>Usuario:</b> {getattr(record, 'request', None) and getattr(record.request, 'user', None)}<br>
        <pre>{getattr(record, 'exc_text', '')}</pre>
        """
        super().emit(record)


# Configuración completa de logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
        'color': {
            '()': ColorFormatter,
            'fmt': '{levelname} {asctime} {module} {message}',
        },
    },
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'django_errors.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'color',
        },
        'mail_admins_simple': {
            'level': 'CRITICAL',
            'class': 'config.logging_config.CustomAdminEmailHandler',
            'formatter': 'verbose',
            'include_html': True,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['file', 'console', 'mail_admins_simple'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}
