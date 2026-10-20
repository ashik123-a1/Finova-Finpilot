import glob
import re
import json
import os

templates = glob.glob('src/web/templates/**/*.html', recursive=True)

# Load locales
with open('src/i18n/locales/en.json', encoding='utf-8') as f:
    en = json.load(f)
with open('src/i18n/locales/bn.json', encoding='utf-8') as f:
    bn = json.load(f)
with open('src/i18n/locales/zh.json', encoding='utf-8') as f:
    zh = json.load(f)

def has_key(d, key):
    parts = key.split('.')
    curr = d
    for p in parts:
        if isinstance(curr, dict) and p in curr:
            curr = curr[p]
        else:
            return False
    return True

print("=== TEMPLATE TRANSLATION AUDIT ===")
all_keys = set()
missing_in_bn = set()
missing_in_zh = set()

for t in sorted(templates):
    with open(t, encoding='utf-8') as f:
        content = f.read()
    # Find all {{ _('...') }} or {{ _("...") }}
    tags = re.findall(r'\{\{\s*_\([\'"]([^\'"]+)[\'"]\)\s*\}\}', content)
    unique_tags = set(tags)
    all_keys.update(unique_tags)
    missing_bn_file = [k for k in unique_tags if not has_key(bn, k)]
    missing_zh_file = [k for k in unique_tags if not has_key(zh, k)]
    missing_in_bn.update(missing_bn_file)
    missing_in_zh.update(missing_zh_file)
    print(f"{os.path.basename(t)}: {len(tags)} tags ({len(unique_tags)} unique) | Missing in BN: {len(missing_bn_file)}, ZH: {len(missing_zh_file)}")

print("\nTotal unique keys across all templates:", len(all_keys))
print("Total missing in bn.json:", len(missing_in_bn))
print("Total missing in zh.json:", len(missing_in_zh))
if missing_in_bn:
    print("Sample missing in BN:", sorted(list(missing_in_bn))[:15])
