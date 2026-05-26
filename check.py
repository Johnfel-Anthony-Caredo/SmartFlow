with open('pages/admin_roles.py', 'r', encoding='utf-8') as f:
    content = f.read()

if 'granted_admin' in content:
    print('STILL PRESENT')
    idx = content.find('granted_admin')
    print(content[idx-10:idx+80])
else:
    print('REMOVED')

print(f'\ngoogle_admin count: {content.find(\"google_admin\")}')
print(f'PROTECTED_LABELS: {content.count(\"PROTECTED_LABELS\")}')
print(f'ADMIN_PERMISSION_KEYS: {content.count(\"ADMIN_PERMISSION_KEYS\")}')
