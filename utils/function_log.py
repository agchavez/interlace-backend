# SECCION: IMPORTACION DE RECURSOS DE DJANGO 
from datetime import datetime
import asyncio
# SECCION: IMPORTACION DE RECURSOS LOCALES 
from apps.logs.models.logs import LogActionModel, LogControlModel
from apps.user.models.user import UserModel

#SECCION: EXCEPCIONES
from apps.logs.exceptions.logs import *

# celery
from celery import shared_task

@shared_task(name='Guardar Logs/crear acciones')
def LogProcess(user_id, id_register, name, action, description, leyenda, data):
    try:
        ### ************** REGISTRO LOG **************
        users = UserModel.objects.get(pk=user_id)
        count = LogActionModel.objects.filter(name=name).count()
        if count == 0:
            LogActionModel.objects.create(
                name = name,
                action = action,
                description = description,
                created_at = datetime.now()
            )
        log_action = LogActionModel.objects.get(name=name)
        log = LogControlModel.objects.create(
            description = leyenda,
            id_register = id_register,
            created_at = datetime.now(),
            action = log_action,
            data = data,
            user = users
        )

        return (True, f'LogProcess: Se ha registrado el log {name} exitosamente, id: {log.id}')
        ### ************** FIN REGISTRO LOG 
    except Exception as e:
        print('LogProcess errro' + str(e))
        raise RegisterLogNotFoundException

# guardar log solo validando por el nombre
@shared_task(name='Guardar Logs')
def log_process_name(user_id, id_register, name, leyenda, data):
    try:
        if LogActionModel.objects.filter(name=name).exists():
            log_action = LogActionModel.objects.get(name=name)
            users = UserModel.objects.get(pk=user_id)
            log = LogControlModel.objects.create(
                description = leyenda,
                id_register = id_register,
                created_at = datetime.now(),
                action = log_action,
                data = data,
                user = users
            )
            return (True, f'LogProcess: Se ha registrado el log {name} exitosamente, id: {log.id}')
        else:
            print('LogProcess error: No existe el nombre de la accion')
            return (False, 'No existe el nombre de la accion')

    except Exception as e:
        print('LogProcess errro' + str(e))
        raise RegisterLogNotFoundException