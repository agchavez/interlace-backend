from datetime import datetime, timedelta

def normalize_date(fecha):
    if isinstance(fecha, datetime):
        return fecha.strftime('%Y-%m-%d')

    if isinstance(fecha, (int, float)):
        try:
            dt = datetime(1899, 12, 30) + timedelta(days=fecha)
            return dt.strftime('%Y-%m-%d')
        except Exception:
            return str(fecha).strip()

    return str(fecha).strip()
