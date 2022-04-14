from datetime import datetime
from typing import Dict

from django.http import HttpRequest


def year(request: HttpRequest) -> Dict:
    """Добавляет переменную с текущим годом."""
    return {'year': datetime.today().year}
