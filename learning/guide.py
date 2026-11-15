"""Public help content contains no account or course records."""
import json

from django.conf import settings


def load_guide():
    guide = json.loads((settings.BASE_DIR / 'data' / 'user-guide.json').read_text(encoding='utf-8'))
    for section in guide['sections']:
        section['table_rows'] = [
            [{'label': label, 'value': value} for label, value in zip(section['columns'], row)]
            for row in section.get('rows', [])
        ]
    return guide
