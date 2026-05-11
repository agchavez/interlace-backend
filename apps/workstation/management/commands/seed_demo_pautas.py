"""
Genera PautaModel + PautaAssignment + PersonnelMetricSample coherentes para
una fecha y CD dados, usando los datos REALES del Excel de picking provisto
por el usuario. Cada fila del Excel se convierte en:
  · 1 PautaModel  (datos: viaje, total CA, PLT, fracciones, hora inicio/fin)
  · 1 PautaAssignment(role=PICKER) con la persona del Excel
  · 1 PautaAssignment(role=COUNTER) con un ayudante random del CD
  · samples derivados: picker_time_per_pauta, picker_pallets_per_hour,
    counter_time_per_truck, etc.

Pickers se buscan por nombre completo (insensible a case/diacríticos) entre
el personal activo del CD. Si una persona no existe, se omite con warning.
Counters siempre son `WAREHOUSE_ASSISTANT` (ayudantes) del mismo CD.

Uso:
    python manage.py seed_demo_pautas --dc 1 --date 2026-05-09 --replace
"""
import random
import unicodedata
from datetime import datetime, timedelta, time as dt_time
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from apps.maintenance.models.distributor_center import DistributorCenter
from apps.truck_cycle.models.catalogs import TruckModel
from apps.truck_cycle.models.core import PautaModel
from apps.truck_cycle.models.operational import PautaAssignmentModel, InconsistencyModel
from apps.personnel.models.metric_sample import PersonnelMetricSample
from apps.personnel.models.personnel import PersonnelProfile
from apps.personnel.models.performance_new import PerformanceMetricType


HN_TZ = ZoneInfo('America/Tegucigalpa')

# ── Counters reales del Excel de errores ───────────────────────────────────
# Pool de contadores que asignamos por rotación al `role=COUNTER` de cada pauta.
COUNTERS_EXCEL = [
    'CRISTHIAN GONZALO LANZA ZEPEDA',
    'ANDI XAVIER OCHOA MUÑOZ',
    'GERSON NOEL LOPEZ COREA',
    'FERNANDO JOSE VALLEJOS BACA',
    'CARLOS ENRIQUE PINEDA',
    'FREDY FAVIAN MARTINEZ OLIVA',
]

# ── Inconsistencias del Excel real (templates para sintetizar) ──────────────
# Tipo Inconsistencia → mapping a choices del modelo
INCONS_TYPE_MAP = {
    'Sobrante': 'SOBRANTE',
    'Faltante': 'FALTANTE',
    'Cruzado':  'CRUCE',
    'Dañado':   'DANADO',
}

# Materiales y nombres reales del Excel (para que las notes sean creíbles)
INCONS_MATERIALS = [
    ('14071', 'MICHELOB ULTRA 12OZ LAT 24U'),
    ('21021', 'MONSTER ENERGY LAT 12OZ'),
    ('14103', 'MONSTER ENERGY 24U LAT 16OZ'),
    ('14106', 'MONSTER MANGO LOCO LT 16OZ 24U'),
    ('14379', 'MONSTER MANGOLOCO 473ML LATA 1X6'),
    ('13968', 'COCA-COLA 12OZ LAT 12U'),
    ('14002', 'COCA-COLA 355 ML PET 12U'),
    ('13940', 'COCA-COLA 6.5OZ VR 24U'),
    ('13958', 'COCA-COLA 0.5LT PET 12U'),
    ('14620', 'COCA-COLA 1.5LT PET 6U'),
    ('14016', 'SPRITE 1.5LT PET 6U.'),
    ('14188', 'BARENA 16OZ LAT 24U'),
    ('13999', 'COCA COLA SIN AZUCAR 1.5LT 6U'),
]

# ── Data del Excel real del usuario ─────────────────────────────────────────
# Tuplas: (nombre_picker, viaje, total_ca, full_pallet_plt, picking_plt,
#          tanda, hora_inicio, hora_fin)
# Si una persona no existe en la BD, se omite con warning.
EXCEL_ROWS = [
    ('EDSON DAVID PONCE SANCHEZ', 1869, 566, 0, 12, 1, '00:00:02', '01:03:09'),
    ('JAIRO ERAZO', 1986, 769, 0, 12, 1, '00:01:46', '01:03:08'),
    ('CARLOS ABEL GODOY GARAY', 1989, 939, 1, 11, 1, '00:06:00', '01:02:17'),
    ('JONATAN JOSUE SARMIENTO MATAMOROS', 1320, 735, 2, 12, 1, '00:01:24', '01:02:34'),
    ('CRISTHIAM MANUEL BAQUEDANO MENDEZ', 2003, 1031, 4, 8, 1, '00:05:31', '01:01:15'),
    ('DORLIN ALFREDO ELIAS MARTINEZ', 1281, 537, 0, 14, 1, '00:03:42', '01:03:35'),
    ('KEVIN ADALID ESPINO', 1937, 1301, 1, 13, 1, '00:00:33', '01:04:24'),
    ('WILSON ANTONIO ESCOTO RODRIGUEZ', 1990, 726, 1, 11, 1, '00:05:18', '01:05:06'),
    ('KEVIN GEOVANI FUNES HERNANDEZ', 1267, 694, 0, 14, 1, '00:02:45', '01:05:04'),
    ('CRISTHIAN GONZALO LANZA', 1284, 945, 4, 10, 1, '00:02:01', '01:03:35'),
    ('JOSE WILLIAMS RAMIREZ CARMONA', 2011, 1041, 1, 13, 1, '00:03:17', '01:00:23'),
    ('CRISTIAN ORLANDO LOPEZ OSORTO', 1862, 853, 6, 6, 1, '00:02:11', '01:05:29'),
    ('ERICK FRANCISCO GODOY BARELA', 1936, 933, 4, 10, 1, '00:03:16', '01:05:33'),
    ('CRISTHOFER JAEL VALERIANO IZAGUIRRE', 1264, 735, 1, 13, 1, '00:04:29', '01:05:36'),
    ('JASON AARON MEDINA ALVARADO', 1327, 873, 2, 12, 1, '00:01:20', '01:05:49'),
    ('CARLOS LEONEL MURILLO ZELAYA', 1887, 704, 0, 12, 1, '00:05:31', '01:04:59'),
    ('YORMAN NAHUN TORRES ALVARADO', 1838, 717, 3, 9, 1, '00:00:44', '01:05:43'),
    ('JAFETH ALDAHIR ACOSTA PERALTA', 1317, 849, 4, 10, 1, '00:02:32', '01:02:47'),
    ('LUIS FAVIO FUNES GALVEZ', 1697, 761, 0, 12, 1, '00:04:34', '01:02:18'),
    ('JUNIOR ALEXANDER PINEDA ANDRADE', 1639, 714, 3, 9, 1, '00:04:40', '01:00:27'),
    ('EDWIN JOEL ORTEGA CASTRO', 2000, 788, 3, 9, 1, '00:02:15', '01:02:24'),
    ('CARLOS ENRIQUE PINEDA MATUTE', 1752, 785, 4, 8, 1, '00:01:03', '01:03:49'),
    ('CARLOS ENRIQUE PINEDA MATUTE', 1857, 515, 6, 8, 1, '00:04:07', '01:03:01'),
    ('MAYNOR SANDOVAL', 1283, 1086, 2, 12, 1, '00:05:13', '01:01:44'),
    ('CRISTIAN DANIEL RAMIREZ COLINDREZ', 1622, 207, 1, 7, 1, '00:04:46', '01:03:42'),
    ('NELSON YOVANI BACA NUÑEZ', 1663, 284, 0, 8, 1, '00:03:04', '01:00:56'),
    ('OLVAN ONIEL SANCHEZ IZAGUIRRE', 1620, 277, 0, 8, 1, '00:01:45', '01:03:39'),
    ('MIGUEL ANGEL HERNANDEZ FUNES', 1826, 207, 0, 8, 1, '00:05:42', '01:05:31'),
    ('EDWIN ORLANDO MEZA DIAZ', 1621, 278, 0, 8, 1, '00:00:11', '01:03:57'),
    ('OLIVER JAVIER VARELA HERRERA', 1958, 352, 0, 8, 1, '00:03:48', '01:01:15'),
    ('JUAN ANGEL HERNANDEZ COREA', 1328, 1174, 9, 5, 1, '00:03:49', '01:01:57'),
    ('JUAN ANGEL HERNANDEZ COREA', 1324, 1018, 11, 3, 1, '00:01:44', '01:05:52'),
    ('CARLOS ALEXIS NUÑEZ BETANCOURTH', 1957, 367, 0, 8, 1, '00:03:15', '01:04:27'),
    ('MARVIN ALEXANDER HERNANDEZ CRUZ', 1754, 554, 2, 10, 1, '00:01:46', '01:02:45'),
    ('SAMUEL ISAIAS ORTIZ DIAZ', 1315, 1200, 6, 8, 1, '00:03:24', '01:01:41'),
    # Tanda 2
    ('EDSON DAVID PONCE SANCHEZ', 1742, 995, 9, 3, 2, '00:59:49', '02:01:21'),
    ('JAIRO ERAZO', 2078, 398, 0, 8, 2, '00:55:46', '02:04:38'),
    ('CARLOS ABEL GODOY GARAY', 1952, 254, 1, 7, 2, '00:59:25', '02:00:29'),
    ('JONATAN JOSUE SARMIENTO MATAMOROS', 1618, 447, 1, 11, 2, '00:56:32', '02:02:13'),
    ('CRISTHIAM MANUEL BAQUEDANO MENDEZ', 2079, 435, 2, 6, 2, '00:56:59', '02:03:10'),
    ('DORLIN ALFREDO ELIAS MARTINEZ', 1265, 835, 4, 10, 2, '00:56:26', '02:04:29'),
    ('KEVIN ADALID ESPINO', 1872, 408, 0, 8, 2, '00:54:18', '02:00:37'),
    ('WILSON ANTONIO ESCOTO RODRIGUEZ', 1955, 241, 0, 8, 2, '00:54:03', '02:04:58'),
    ('KEVIN GEOVANI FUNES HERNANDEZ', 1987, 486, 0, 12, 2, '00:58:50', '02:05:32'),
    ('CRISTHIAN GONZALO LANZA', 1614, 360, 1, 11, 2, '00:55:23', '02:02:35'),
    ('JOSE WILLIAMS RAMIREZ CARMONA', 1653, 578, 3, 9, 2, '00:55:33', '02:04:37'),
    ('CRISTIAN ORLANDO LOPEZ OSORTO', 1988, 692, 1, 11, 2, '00:55:15', '02:00:22'),
    ('ERICK FRANCISCO GODOY BARELA', 1824, 234, 1, 7, 2, '00:57:04', '02:05:54'),
    ('CRISTHOFER JAEL VALERIANO IZAGUIRRE', 2102, 437, 0, 8, 2, '00:58:09', '02:00:58'),
    ('JASON AARON MEDINA ALVARADO', 1959, 321, 0, 8, 2, '00:59:34', '02:04:49'),
    ('CARLOS LEONEL MURILLO ZELAYA', 1992, 500, 2, 10, 2, '00:57:15', '02:00:31'),
    ('YORMAN NAHUN TORRES ALVARADO', 1820, 363, 0, 8, 2, '00:58:31', '02:00:14'),
    ('JAFETH ALDAHIR ACOSTA PERALTA', 2098, 419, 0, 8, 2, '00:55:34', '02:02:13'),
    ('LUIS FAVIO FUNES GALVEZ', 1873, 308, 0, 8, 2, '00:59:58', '02:02:58'),
    ('JUNIOR ALEXANDER PINEDA ANDRADE', 1956, 294, 0, 8, 2, '00:57:51', '02:03:30'),
    ('EDWIN JOEL ORTEGA CASTRO', 1694, 638, 1, 11, 2, '00:58:36', '02:00:16'),
    ('CARLOS ENRIQUE PINEDA MATUTE', 1326, 1004, 2, 12, 2, '00:58:26', '02:02:45'),
    ('MAYNOR SANDOVAL', 1757, 470, 0, 12, 2, '00:59:02', '02:01:13'),
    # Tanda 3
    ('EDSON DAVID PONCE SANCHEZ', 1266, 633, 5, 9, 3, '02:23:55', '03:31:36'),
    ('JAIRO ERAZO', 1617, 517, 1, 11, 3, '02:18:56', '03:30:23'),
    ('CARLOS ABEL GODOY GARAY', 1708, 417, 1, 11, 3, '02:22:07', '03:31:11'),
    ('JONATAN JOSUE SARMIENTO MATAMOROS', 1991, 654, 0, 12, 3, '02:23:29', '03:34:36'),
    ('DORLIN ALFREDO ELIAS MARTINEZ', 1807, 314, 0, 8, 3, '02:22:35', '03:35:19'),
    ('KEVIN ADALID ESPINO', 2101, 319, 2, 6, 3, '02:23:06', '03:34:36'),
    ('WILSON ANTONIO ESCOTO RODRIGUEZ', 1886, 584, 2, 10, 3, '02:19:58', '03:30:55'),
    ('KEVIN GEOVANI FUNES HERNANDEZ', 1901, 631, 1, 11, 3, '02:19:38', '03:34:33'),
    ('JOSE WILLIAMS RAMIREZ CARMONA', 1954, 329, 0, 8, 3, '02:22:02', '03:30:58'),
    ('CRISTIAN ORLANDO LOPEZ OSORTO', 1955, 343, 0, 8, 3, '02:21:49', '03:31:29'),
    ('ERICK FRANCISCO GODOY BARELA', 1638, 487, 2, 10, 3, '02:21:40', '03:34:20'),
    ('CRISTHOFER JAEL VALERIANO IZAGUIRRE', 1902, 648, 0, 12, 3, '02:23:57', '03:32:31'),
    ('CARLOS LEONEL MURILLO ZELAYA', 2099, 363, 0, 8, 3, '02:23:13', '03:33:26'),
    ('YORMAN NAHUN TORRES ALVARADO', 1620, 224, 0, 8, 3, '02:21:21', '03:34:21'),
    ('JAFETH ALDAHIR ACOSTA PERALTA', 1959, 283, 0, 8, 3, '02:20:12', '03:30:47'),
    ('LUIS FAVIO FUNES GALVEZ', 1615, 594, 2, 10, 3, '02:18:48', '03:33:52'),
    ('JUNIOR ALEXANDER PINEDA ANDRADE', 1616, 507, 3, 9, 3, '02:22:31', '03:33:05'),
    ('EDWIN JOEL ORTEGA CASTRO', 1941, 460, 1, 7, 3, '02:18:21', '03:32:40'),
    ('CARLOS ENRIQUE PINEDA MATUTE', 1960, 327, 0, 8, 3, '02:22:06', '03:30:11'),
    ('MAYNOR SANDOVAL', 1935, 568, 3, 11, 3, '02:19:19', '03:31:10'),
    # Tanda 4
    ('EDSON DAVID PONCE SANCHEZ', 1318, 725, 10, 4, 4, '03:32:28', '04:36:06'),
    ('JAIRO ERAZO', 1826, 194, 0, 8, 4, '03:32:51', '04:36:50'),
    ('CARLOS ABEL GODOY GARAY', 1960, 376, 1, 7, 4, '03:30:41', '04:40:00'),
    ('JONATAN JOSUE SARMIENTO MATAMOROS', 1988, 301, 1, 11, 4, '03:33:30', '04:40:43'),
    ('CRISTHIAM MANUEL BAQUEDANO MENDEZ', 1621, 231, 0, 8, 4, '03:31:37', '04:41:12'),
    ('DORLIN ALFREDO ELIAS MARTINEZ', 1621, 155, 1, 7, 4, '03:34:45', '04:41:02'),
    ('KEVIN ADALID ESPINO', 1622, 375, 2, 6, 4, '03:34:51', '04:40:59'),
    ('WILSON ANTONIO ESCOTO RODRIGUEZ', 1752, 278, 0, 12, 4, '03:30:56', '04:40:24'),
    ('KEVIN GEOVANI FUNES HERNANDEZ', 1752, 196, 0, 12, 4, '03:31:50', '04:39:06'),
    ('CRISTHIAN GONZALO LANZA', 1587, 142, 0, 10, 4, '03:34:10', '04:39:33'),
    ('JOSE WILLIAMS RAMIREZ CARMONA', 1752, 401, 1, 11, 4, '03:34:47', '04:41:33'),
    ('CRISTIAN ORLANDO LOPEZ OSORTO', 1663, 309, 2, 6, 4, '03:35:07', '04:40:09'),
    ('JASON AARON MEDINA ALVARADO', 1952, 284, 0, 8, 4, '03:31:36', '04:39:39'),
    ('CARLOS LEONEL MURILLO ZELAYA', 1941, 394, 0, 8, 4, '03:30:37', '04:37:09'),
    ('YORMAN NAHUN TORRES ALVARADO', 1958, 221, 0, 8, 4, '03:31:14', '04:40:05'),
    ('LUIS FAVIO FUNES GALVEZ', 1958, 393, 0, 8, 4, '03:35:50', '04:38:39'),
    ('EDWIN JOEL ORTEGA CASTRO', 1873, 1191, 6, 2, 4, '03:32:18', '04:38:35'),
    ('CARLOS ENRIQUE PINEDA MATUTE', 1873, 213, 0, 8, 4, '03:30:09', '04:38:36'),
    ('MAYNOR SANDOVAL', 1941, 281, 0, 8, 4, '03:32:45', '04:38:10'),
    ('CRISTIAN DANIEL RAMIREZ COLINDREZ', 1323, 766, 0, 14, 4, '03:35:13', '04:41:32'),
    ('NELSON YOVANI BACA NUÑEZ', 1869, 566, 0, 12, 4, '03:34:09', '04:36:06'),
    ('OLVAN ONIEL SANCHEZ IZAGUIRRE', 1619, 384, 0, 12, 4, '03:30:51', '04:39:22'),
    ('MIGUEL ANGEL HERNANDEZ FUNES', 1318, 1191, 0, 14, 4, '03:35:00', '04:36:45'),
]


class Command(BaseCommand):
    help = 'Genera pautas + assignments + samples desde el Excel real.'

    def add_arguments(self, parser):
        parser.add_argument('--dc', type=int, required=True, help='ID del CD.')
        parser.add_argument('--date', type=str, required=True, help='YYYY-MM-DD.')
        parser.add_argument('--replace', action='store_true',
                            help='Borra pautas/samples previos del día/CD.')
        parser.add_argument('--shift-start', type=str, default='10:00',
                            help='Hora a la que arranca la tanda 1 (default 10:00 — turno TB).')

    def handle(self, *args, **options):
        try:
            op_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
        except ValueError:
            raise CommandError('Fecha inválida')
        try:
            dc = DistributorCenter.objects.get(pk=options['dc'])
        except DistributorCenter.DoesNotExist:
            raise CommandError(f'CD {options["dc"]} no existe')
        try:
            base_h, base_m = map(int, options['shift_start'].split(':'))
            shift_base = datetime.combine(op_date, dt_time(base_h, base_m), tzinfo=HN_TZ)
        except ValueError:
            raise CommandError('shift-start debe ser HH:MM')

        self.stdout.write(self.style.WARNING(f'=== {dc.name} ({op_date}) — turno arranca {options["shift_start"]} ==='))

        # 1) Personal: pickers por nombre. El Excel real tiene "ayudantes" que
        # operan como pickers — por eso buscamos en WAREHOUSE_ASSISTANT/LOADER/PICKER.
        all_people = list(PersonnelProfile.objects.filter(
            distributor_centers=dc, is_active=True,
            position_type__in=['PICKER', 'LOADER', 'WAREHOUSE_ASSISTANT'],
        ))
        # Index: tokens normalizados → persona
        people_tokens = [(p, set(_norm(f'{p.first_name} {p.last_name}').split())) for p in all_people]

        unique_names = sorted({row[0] for row in EXCEL_ROWS})
        matched = {}
        missing = []
        for name in unique_names:
            target = set(_norm(name).split())
            # Mejor match: máxima intersección de tokens, con >=2 tokens en común.
            best = None
            best_score = 0
            for p, toks in people_tokens:
                if p.id in {m.id for m in matched.values()}:
                    continue  # ya asignado a otra fila → seguimos buscando
                score = len(target & toks)
                if score > best_score:
                    best_score = score
                    best = p
            if best and best_score >= 2:
                matched[name] = best
            else:
                missing.append(name)

        self.stdout.write(f'  · pickers del Excel encontrados: {len(matched)}/{len(unique_names)}')
        if missing:
            self.stdout.write(self.style.WARNING(
                f'  · faltantes ({len(missing)}): ' + ', '.join(missing[:5]) + ('…' if len(missing) > 5 else '')
            ))

        # Counters: pool fijo del Excel de errores (6 nombres). Buscamos por
        # token-match, excluyendo a los ya asignados como pickers.
        used_ids = {p.id for p in matched.values()}
        counters_matched = {}
        counters_missing = []
        for cname in COUNTERS_EXCEL:
            target = set(_norm(cname).split())
            best, best_score = None, 0
            for p, toks in people_tokens:
                if p.id in used_ids or p.id in {c.id for c in counters_matched.values()}:
                    continue
                score = len(target & toks)
                if score > best_score:
                    best_score = score
                    best = p
            if best and best_score >= 2:
                counters_matched[cname] = best
            else:
                counters_missing.append(cname)
        counters = list(counters_matched.values())
        if not counters:
            raise CommandError('No se encontró ningún counter del Excel en el CD.')
        self.stdout.write(f'  · counters del Excel encontrados: {len(counters_matched)}/{len(COUNTERS_EXCEL)}')
        if counters_missing:
            self.stdout.write(self.style.WARNING(
                f'  · counters faltantes: ' + ', '.join(counters_missing)
            ))
        yards = list(PersonnelProfile.objects.filter(
            distributor_centers=dc, is_active=True,
            position_type='YARD_DRIVER',
        ))

        trucks = list(TruckModel.objects.filter(distributor_center=dc, is_active=True))
        if not trucks:
            raise CommandError('No hay trucks activos en el CD.')

        # 2) Métricas
        metric_id = {
            m.code: m.id for m in PerformanceMetricType.objects.filter(
                code__in=[
                    'picker_pallets_per_hour', 'picker_time_per_pauta',
                    'picker_load_error_rate', 'counter_time_per_truck',
                    'counter_pallets_per_hour', 'counter_error_rate',
                    'yard_time_park_to_bay', 'yard_time_bay_to_park',
                    'yard_time_total_move', 'yard_trucks_moved',
                ],
            )
        }

        # 3) Replace
        if options['replace']:
            with transaction.atomic():
                d1 = PersonnelMetricSample.objects.filter(
                    operational_date=op_date, personnel__distributor_centers=dc,
                ).delete()[0]
                d2 = PautaModel.objects.filter(
                    operational_date=op_date, distributor_center=dc,
                ).delete()[0]
                self.stdout.write(f'  · borrados {d1} samples y {d2} pautas previas')

        # 4) Crear pautas a partir del Excel
        pautas = []
        pauta_meta = []  # (picker_id, total_pallets, start_dt, end_dt, fractions)
        for name, viaje, total_ca, full_plt, picking_plt, tanda, hh_ini, hh_fin in EXCEL_ROWS:
            picker = matched.get(name)
            if not picker:
                continue
            start_dt = shift_base + _hms_to_timedelta(hh_ini)
            end_dt = shift_base + _hms_to_timedelta(hh_fin)
            total_plt = full_plt + picking_plt
            p = PautaModel(
                transport_number=f'T{viaje}',
                trip_number=str(viaje),
                route_code=f'R{viaje % 1000:03d}',
                total_boxes=total_ca,
                total_pallets=Decimal(str(total_plt)),
                assembled_fractions=full_plt,
                total_skus=random.randint(15, 50),
                status='CLOSED',
                operational_date=op_date,
                truck=random.choice(trucks),
                distributor_center=dc,
            )
            pautas.append(p)
            pauta_meta.append((picker, total_plt, start_dt, end_dt, full_plt, picking_plt, total_ca))

        PautaModel.objects.bulk_create(pautas)
        _set_pauta_created_at(pautas, [m[2] for m in pauta_meta])
        self.stdout.write(f'  · {len(pautas)} pautas creadas')

        # 5) Assignments + samples
        assignments = []
        sample_rows = []
        for p, (picker, total_plt, start_dt, end_dt, full_plt, picking_plt, total_ca) in zip(pautas, pauta_meta):
            counter = random.choice(counters)
            yard = random.choice(yards) if yards else None

            assignments.append(PautaAssignmentModel(pauta=p, role='PICKER', personnel=picker))
            assignments.append(PautaAssignmentModel(pauta=p, role='COUNTER', personnel=counter))
            if yard:
                assignments.append(PautaAssignmentModel(pauta=p, role='YARD_DRIVER', personnel=yard))

            # picker_time_per_pauta = duración real en minutos
            dur_min = (end_dt - start_dt).total_seconds() / 60.0
            mid_ts = start_dt + (end_dt - start_dt) / 2
            if 'picker_time_per_pauta' in metric_id:
                sample_rows.append((picker.id, metric_id['picker_time_per_pauta'],
                                    op_date, Decimal(str(round(dur_min, 2))),
                                    PersonnelMetricSample.SOURCE_AUTO, mid_ts))
            # picker_pallets_per_hour = PLT/Hr derivado
            if 'picker_pallets_per_hour' in metric_id and dur_min > 0:
                plt_h = total_plt / (dur_min / 60.0)
                sample_rows.append((picker.id, metric_id['picker_pallets_per_hour'],
                                    op_date, Decimal(str(round(plt_h, 2))),
                                    PersonnelMetricSample.SOURCE_AUTO, mid_ts))
            # picker_load_error_rate: error en ~20% de pautas
            if 'picker_load_error_rate' in metric_id and random.random() < 0.20:
                sample_rows.append((picker.id, metric_id['picker_load_error_rate'],
                                    op_date, Decimal(str(round(random.uniform(0.5, 4.0), 2))),
                                    PersonnelMetricSample.SOURCE_AUTO, mid_ts))

            # counter: empieza ~5 min después de cerrar la pauta del picker
            ctr_start = end_dt + timedelta(minutes=random.uniform(3, 8))
            ctr_dur = max(8.0, random.gauss(18.0, 5.0))
            ctr_mid = ctr_start + timedelta(minutes=ctr_dur / 2)
            if 'counter_time_per_truck' in metric_id:
                sample_rows.append((counter.id, metric_id['counter_time_per_truck'],
                                    op_date, Decimal(str(round(ctr_dur, 2))),
                                    PersonnelMetricSample.SOURCE_AUTO, ctr_mid))
            if 'counter_pallets_per_hour' in metric_id and ctr_dur > 0:
                cnt_plt_h = total_plt / (ctr_dur / 60.0)
                sample_rows.append((counter.id, metric_id['counter_pallets_per_hour'],
                                    op_date, Decimal(str(round(cnt_plt_h, 2))),
                                    PersonnelMetricSample.SOURCE_AUTO, ctr_mid))
            if 'counter_error_rate' in metric_id and random.random() < 0.12:
                sample_rows.append((counter.id, metric_id['counter_error_rate'],
                                    op_date, Decimal(str(round(random.uniform(0.3, 3.0), 2))),
                                    PersonnelMetricSample.SOURCE_AUTO, ctr_mid))

            # yard: tres tiempos
            if yard:
                y_ts = ctr_mid + timedelta(minutes=5)
                park_to_bay = max(2.0, random.gauss(6, 2))
                bay_to_park = max(2.0, random.gauss(7, 2.5))
                total_move = park_to_bay + bay_to_park + random.uniform(1, 4)
                if 'yard_time_park_to_bay' in metric_id:
                    sample_rows.append((yard.id, metric_id['yard_time_park_to_bay'],
                                        op_date, Decimal(str(round(park_to_bay, 2))),
                                        PersonnelMetricSample.SOURCE_AUTO, y_ts))
                if 'yard_time_bay_to_park' in metric_id:
                    sample_rows.append((yard.id, metric_id['yard_time_bay_to_park'],
                                        op_date, Decimal(str(round(bay_to_park, 2))),
                                        PersonnelMetricSample.SOURCE_AUTO, y_ts))
                if 'yard_time_total_move' in metric_id:
                    sample_rows.append((yard.id, metric_id['yard_time_total_move'],
                                        op_date, Decimal(str(round(total_move, 2))),
                                        PersonnelMetricSample.SOURCE_AUTO, y_ts))

        PautaAssignmentModel.objects.bulk_create(assignments)
        _bulk_insert_samples(sample_rows, op_date, dc.id)

        # 6) Inconsistencias sintéticas (~18% de las pautas tienen al menos 1).
        # Patrón del Excel real de errores: Sobrante/Faltante/Cruce, fase
        # VERIFICATION (≈40%) o CHECKOUT (≈60%), 1-9 cajas de diferencia.
        incons = []
        for p in pautas:
            n_errors = random.choices([0, 1, 2], weights=[0.78, 0.18, 0.04])[0]
            for _ in range(n_errors):
                mat_code, mat_name = random.choice(INCONS_MATERIALS)
                excel_type = random.choices(
                    list(INCONS_TYPE_MAP.keys()),
                    weights=[0.40, 0.35, 0.25, 0.0],  # Sobrante, Faltante, Cruzado, Dañado
                )[0]
                inc_type = INCONS_TYPE_MAP[excel_type]
                phase = random.choices(['VERIFICATION', 'CHECKOUT'], weights=[0.4, 0.6])[0]
                cajas = random.choices([1, 2, 3, 5, 9], weights=[0.55, 0.20, 0.12, 0.08, 0.05])[0]
                # Diferencia: + para sobrante, - para faltante, 0 para cruce (no aporta)
                if inc_type == 'SOBRANTE':
                    diff = cajas
                elif inc_type == 'FALTANTE':
                    diff = -cajas
                else:
                    diff = 0
                incons.append(InconsistencyModel(
                    pauta=p,
                    phase=phase,
                    inconsistency_type=inc_type,
                    material_code=mat_code,
                    product_name=mat_name,
                    expected_quantity=cajas if inc_type == 'FALTANTE' else 0,
                    actual_quantity=cajas if inc_type == 'SOBRANTE' else 0,
                    difference=diff,
                ))
        if incons:
            InconsistencyModel.objects.bulk_create(incons)

        self.stdout.write(self.style.SUCCESS(
            f'\nResumen: {len(pautas)} pautas · {len(assignments)} assignments · '
            f'{len(sample_rows)} samples · {len(incons)} inconsistencias'
        ))


def _norm(s):
    """Normaliza para matching: upper, sin acentos, espacios colapsados."""
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return ' '.join(s.upper().split())


def _hms_to_timedelta(hms):
    """'01:03:09' → timedelta."""
    h, m, s = hms.split(':')
    return timedelta(hours=int(h), minutes=int(m), seconds=int(s))


def _set_pauta_created_at(pautas, timestamps):
    pairs = [(p.pk, ts) for p, ts in zip(pautas, timestamps) if p.pk is not None]
    if not pairs:
        return
    table = PautaModel._meta.db_table
    placeholders = ','.join(['(%s, %s::timestamptz)'] * len(pairs))
    params = [v for pair in pairs for v in pair]
    sql = (
        f'UPDATE "{table}" AS t SET created_at = v.ts '
        f'FROM (VALUES {placeholders}) AS v(id, ts) WHERE t.id = v.id'
    )
    with connection.cursor() as cur:
        cur.execute(sql, params)


def _bulk_insert_samples(rows, op_date, dc_id, batch_size=500):
    if not rows:
        return
    import json
    table = PersonnelMetricSample._meta.db_table
    ctx_json = json.dumps({'demo': True, 'date': str(op_date), 'dc': dc_id})
    cols = '(personnel_id, metric_type_id, operational_date, numeric_value, source, context, created_at)'
    placeholder = '(%s,%s,%s,%s,%s,%s::jsonb,%s::timestamptz)'
    with connection.cursor() as cur:
        for i in range(0, len(rows), batch_size):
            chunk = rows[i:i + batch_size]
            params = []
            for (p_id, m_id, op_d, val, src, ts) in chunk:
                params.extend([p_id, m_id, op_d, val, src, ctx_json, ts])
            sql = (
                f'INSERT INTO "{table}" {cols} VALUES '
                + ','.join([placeholder] * len(chunk))
            )
            cur.execute(sql, params)
