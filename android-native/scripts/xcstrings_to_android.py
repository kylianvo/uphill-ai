#!/usr/bin/env python3
"""Generate Android EN/VI resources and a stable key map from the iOS catalog."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET


def resource_ids(keys):
    result = {}
    used = set()
    for key in sorted(keys):
        base = re.sub(r'[^a-z0-9]+', '_', key.lower()).strip('_')[:80] or 'text'
        if not base[0].isalpha() or base in {'private', 'public', 'class', 'default', 'new', 'return', 'switch', 'enum', 'void', 'int', 'true', 'false', 'null', 'final', 'protected', 'static', 'package', 'import', 'abstract', 'assert', 'boolean', 'break', 'byte', 'case', 'catch', 'char', 'const', 'continue', 'do', 'double', 'else', 'extends', 'finally', 'float', 'for', 'goto', 'if', 'implements', 'instanceof', 'interface', 'long', 'native', 'short', 'strictfp', 'super', 'synchronized', 'this', 'throw', 'throws', 'transient', 'try', 'volatile', 'while'}: base = 'text_' + base
        name = base
        if name in used: name += '_' + hashlib.sha256(key.encode()).hexdigest()[:10]
        used.add(name)
        result[key] = name
    return result


def android_text(text):
    position = 0
    def convert(match):
        nonlocal position
        if match.group() == '%%': return '%%'
        position += 1
        explicit, flags, precision, kind = match.groups()
        index = explicit or str(position)
        kind = 's' if kind == '@' else ('d' if kind.endswith('d') else kind)
        return '%' + index + '$' + (flags or '') + (precision or '') + kind
    text = re.sub(r'%%|%(?:(\d+)\$)?([-+0]*)(\.\d+)?(@|lld|ld|d|f|s)', convert, text)
    return text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\t', '\\t')


def generate(source, output):
    catalog = json.loads(source.read_text())['strings']
    extras_file = Path(__file__).with_name('extra_strings.json')
    if extras_file.exists():
        for key, vi in json.loads(extras_file.read_text()).items():
            catalog.setdefault(key, {'localizations': {'en': {'stringUnit': {'value': key}}, 'vi': {'stringUnit': {'value': vi}}}})
    mapping = resource_ids(catalog)
    for locale, folder in [('en', 'values'), ('vi', 'values-vi')]:
        root = ET.Element('resources')
        for key in sorted(catalog):
            localization = catalog[key].get('localizations', {}).get(locale, {})
            if 'variations' in localization:
                raise ValueError(f'Plural variation needs explicit conversion: {key}')
            text = localization.get('stringUnit', {}).get('value', key if locale == 'en' else None)
            if text is None: raise ValueError(f'Missing Vietnamese translation: {key}')
            attrs = {'name': mapping[key]}
            # Literal percentages aren't Java format specifiers.
            if not re.search(r'%(?:\d+\$)?[-+0]*(?:\.\d+)?(?:@|lld|ld|d|f|s)', text): attrs['formatted'] = 'false'
            ET.SubElement(root, 'string', attrs).text = android_text(text)
        ET.indent(root)
        target = output / folder / 'strings.xml'
        target.parent.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(root).write(target, encoding='utf-8', xml_declaration=True)
    (output.parent / 'assets').mkdir(exist_ok=True)
    (output.parent / 'assets' / 'string_keys.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n')
    print(f'Generated {len(mapping)} strings in EN and VI')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[2] / 'ios-native/UphillAI/Resources/Localizable.xcstrings')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'app/src/main/res')
    args = parser.parse_args()
    generate(args.source, args.output)
