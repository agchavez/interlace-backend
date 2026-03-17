"""
Carga masiva inicial de catálogos de tokens:
- Tipos de horas extra (OvertimeTypeModel)
- Motivos de horas extra (OvertimeReasonModel)
- Materiales de uniforme (Material con categoría UNIFORME)
"""
from django.core.management.base import BaseCommand
from apps.tokens.models import OvertimeTypeModel, OvertimeReasonModel, Material, UnitOfMeasure


class Command(BaseCommand):
    help = 'Carga datos iniciales para catálogos de tokens (tipos/motivos de horas extra y materiales de uniforme)'

    def handle(self, *args, **options):
        self.seed_overtime_types()
        self.seed_overtime_reasons()
        self.seed_uniform_materials()
        self.stdout.write(self.style.SUCCESS('Carga masiva completada exitosamente'))

    def seed_overtime_types(self):
        types_data = [
            {'code': 'REGULAR', 'name': 'Horas Extra Regulares', 'description': 'Horas extra en día laboral normal', 'default_multiplier': 1.50},
            {'code': 'HOLIDAY', 'name': 'Horas en Feriado', 'description': 'Horas trabajadas en días feriados oficiales', 'default_multiplier': 2.00},
            {'code': 'WEEKEND', 'name': 'Horas en Fin de Semana', 'description': 'Horas trabajadas en sábado o domingo', 'default_multiplier': 2.00},
            {'code': 'NIGHT', 'name': 'Horas Nocturnas', 'description': 'Horas trabajadas en horario nocturno (después de las 19:00)', 'default_multiplier': 1.75},
            {'code': 'DOUBLE', 'name': 'Doble Turno', 'description': 'Doble jornada laboral completa', 'default_multiplier': 2.00},
            {'code': 'MIXED', 'name': 'Jornada Mixta', 'description': 'Horas extra en jornada mixta (diurna y nocturna)', 'default_multiplier': 1.50},
            {'code': 'EMERGENCY', 'name': 'Emergencia', 'description': 'Horas extra por situación de emergencia', 'default_multiplier': 2.50},
        ]

        created = 0
        for data in types_data:
            _, was_created = OvertimeTypeModel.objects.get_or_create(
                code=data['code'],
                defaults=data,
            )
            if was_created:
                created += 1

        self.stdout.write(f'  Tipos de hora extra: {created} creados, {len(types_data) - created} ya existían')

    def seed_overtime_reasons(self):
        reasons_data = [
            {'code': 'PRODUCTION', 'name': 'Demanda de Producción', 'description': 'Incremento en demanda de producción que requiere horas adicionales'},
            {'code': 'DEADLINE', 'name': 'Cumplimiento de Plazo', 'description': 'Necesidad de cumplir plazos de entrega o fechas límite'},
            {'code': 'COVERAGE', 'name': 'Cobertura de Personal', 'description': 'Cobertura por ausencia, incapacidad o vacaciones de otro empleado'},
            {'code': 'EMERGENCY', 'name': 'Emergencia', 'description': 'Situación de emergencia que requiere atención inmediata'},
            {'code': 'SPECIAL_PROJECT', 'name': 'Proyecto Especial', 'description': 'Trabajo en proyecto especial o iniciativa temporal'},
            {'code': 'INVENTORY', 'name': 'Inventario', 'description': 'Conteo o auditoría de inventario físico'},
            {'code': 'MAINTENANCE', 'name': 'Mantenimiento', 'description': 'Mantenimiento preventivo o correctivo de equipos/instalaciones'},
            {'code': 'SEASONAL', 'name': 'Temporada Alta', 'description': 'Incremento de trabajo por temporada alta o fechas especiales'},
            {'code': 'TRAINING', 'name': 'Capacitación', 'description': 'Capacitación o entrenamiento fuera del horario regular'},
            {'code': 'AUDIT', 'name': 'Auditoría', 'description': 'Preparación o ejecución de auditorías'},
            {'code': 'OTHER', 'name': 'Otro', 'description': 'Otro motivo no categorizado'},
        ]

        created = 0
        for data in reasons_data:
            _, was_created = OvertimeReasonModel.objects.get_or_create(
                code=data['code'],
                defaults=data,
            )
            if was_created:
                created += 1

        self.stdout.write(f'  Motivos de hora extra: {created} creados, {len(reasons_data) - created} ya existían')

    def seed_uniform_materials(self):
        # Obtener unidad de medida
        try:
            und = UnitOfMeasure.objects.get(code='UND')
        except UnitOfMeasure.DoesNotExist:
            self.stdout.write(self.style.WARNING('  No se encontró la unidad UND. Creando...'))
            und = UnitOfMeasure.objects.create(code='UND', name='Unidad', abbreviation='und')

        try:
            par = UnitOfMeasure.objects.get(code='PAR')
        except UnitOfMeasure.DoesNotExist:
            self.stdout.write(self.style.WARNING('  No se encontró la unidad PAR. Creando...'))
            par = UnitOfMeasure.objects.create(code='PAR', name='Par', abbreviation='par')

        materials_data = [
            # Camisas
            {'code': 'UNI-CAM-MC', 'name': 'Camisa Manga Corta', 'description': 'Camisa de uniforme manga corta', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            {'code': 'UNI-CAM-ML', 'name': 'Camisa Manga Larga', 'description': 'Camisa de uniforme manga larga', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            {'code': 'UNI-POLO', 'name': 'Polo Institucional', 'description': 'Polo con logo institucional', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            # Pantalones
            {'code': 'UNI-PAN-JN', 'name': 'Pantalón Jean', 'description': 'Pantalón de jean para uniforme', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            {'code': 'UNI-PAN-VE', 'name': 'Pantalón de Vestir', 'description': 'Pantalón de vestir para uniforme', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            {'code': 'UNI-PAN-CR', 'name': 'Pantalón Cargo', 'description': 'Pantalón cargo de trabajo', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            # Calzado
            {'code': 'UNI-ZAP-SE', 'name': 'Zapatos de Seguridad', 'description': 'Zapatos de seguridad industrial con punta de acero', 'unit_of_measure': par, 'category': 'UNIFORME', 'requires_return': True},
            {'code': 'UNI-BOT-SE', 'name': 'Botas de Seguridad', 'description': 'Botas de seguridad industrial', 'unit_of_measure': par, 'category': 'UNIFORME', 'requires_return': True},
            {'code': 'UNI-BOT-HU', 'name': 'Botas de Hule', 'description': 'Botas de hule impermeables', 'unit_of_measure': par, 'category': 'UNIFORME', 'requires_return': True},
            # Chaquetas y chalecos
            {'code': 'UNI-CHA-LI', 'name': 'Chaqueta Ligera', 'description': 'Chaqueta ligera institucional', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            {'code': 'UNI-CHA-PE', 'name': 'Chaqueta Pesada', 'description': 'Chaqueta pesada para clima frío', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            {'code': 'UNI-CHAL-RE', 'name': 'Chaleco Reflectivo', 'description': 'Chaleco de seguridad reflectivo', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            {'code': 'UNI-CHAL-IN', 'name': 'Chaleco Institucional', 'description': 'Chaleco institucional con logo', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            # EPP
            {'code': 'UNI-CAS-SE', 'name': 'Casco de Seguridad', 'description': 'Casco de seguridad industrial', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            {'code': 'UNI-GUA-CU', 'name': 'Guantes de Cuero', 'description': 'Guantes de cuero para trabajo', 'unit_of_measure': par, 'category': 'UNIFORME', 'requires_return': False},
            {'code': 'UNI-GUA-LA', 'name': 'Guantes de Látex', 'description': 'Guantes desechables de látex', 'unit_of_measure': par, 'category': 'UNIFORME', 'requires_return': False},
            {'code': 'UNI-GAF-SE', 'name': 'Gafas de Seguridad', 'description': 'Gafas de protección industrial', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            {'code': 'UNI-TAP-AU', 'name': 'Tapones Auditivos', 'description': 'Tapones de protección auditiva', 'unit_of_measure': par, 'category': 'UNIFORME', 'requires_return': False},
            {'code': 'UNI-ORE-SE', 'name': 'Orejeras de Seguridad', 'description': 'Orejeras de protección auditiva', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            # Accesorios
            {'code': 'UNI-GOR-IN', 'name': 'Gorra Institucional', 'description': 'Gorra con logo institucional', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            {'code': 'UNI-CIN-CU', 'name': 'Cinturón de Cuero', 'description': 'Cinturón de cuero para uniforme', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            {'code': 'UNI-CRED', 'name': 'Credencial / Gafete', 'description': 'Credencial de identificación con lanyard', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            # Overol
            {'code': 'UNI-OVE-MC', 'name': 'Overol Manga Corta', 'description': 'Overol de trabajo manga corta', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            {'code': 'UNI-OVE-ML', 'name': 'Overol Manga Larga', 'description': 'Overol de trabajo manga larga', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
            # Mascarillas
            {'code': 'UNI-MASC', 'name': 'Mascarilla Desechable', 'description': 'Mascarilla de protección desechable', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': False},
            {'code': 'UNI-RESP', 'name': 'Respirador Reutilizable', 'description': 'Respirador con filtros reutilizables', 'unit_of_measure': und, 'category': 'UNIFORME', 'requires_return': True},
        ]

        created = 0
        for data in materials_data:
            _, was_created = Material.objects.get_or_create(
                code=data['code'],
                defaults=data,
            )
            if was_created:
                created += 1

        self.stdout.write(f'  Materiales de uniforme: {created} creados, {len(materials_data) - created} ya existían')
