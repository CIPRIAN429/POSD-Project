"""Generate the downloadable manual from the same content as the in-app guide."""
import argparse
import json
from pathlib import Path


def render(guide):
    lines = [f"# {guide['title']}", '', guide['description'], '', '## Contents', '']
    for section in guide['sections']:
        lines.append(f"- [{section['title']}](#{section['slug']})")
    for section in guide['sections']:
        lines.extend(['', f'<a id="{section["slug"]}"></a>', '',
                      f"## {section['title']}", '', f"For: {section['audience']}", ''])
        for paragraph in section.get('paragraphs', []):
            lines.extend([paragraph, ''])
        for number, step in enumerate(section.get('steps', []), 1):
            lines.append(f'{number}. {step}')
        if section.get('steps'):
            lines.append('')
        if section.get('rows'):
            def row(values):
                return '| ' + ' | '.join(value.replace('|', r'\|') for value in values) + ' |'
            lines.append(row(section['columns']))
            lines.append(row(['---'] * len(section['columns'])))
            lines.extend(row(values) for values in section['rows'])
            lines.append('')
        lines.extend(f'- {bullet}' for bullet in section.get('bullets', []))
    return '\n'.join(lines).rstrip() + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if the generated copy is out of date.')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    guide = json.loads((root / 'data/user-guide.json').read_text(encoding='utf-8'))
    target = root / 'docs/user-guide.md'
    content = render(guide)
    if args.check:
        if not target.exists() or target.read_text(encoding='utf-8') != content:
            raise SystemExit('User guide is out of date. Run python scripts/export-guide.py.')
        print('User guide is up to date.')
    else:
        target.write_text(content, encoding='utf-8')
        print(f'Exported {len(guide["sections"])} sections to {target}')
