import os
src = os.path.join(os.path.dirname(__file__), 'assets', 'styles.css')
with open(src, 'rb') as f:
    data = f.read()

old = b'.apply-btn {\r\n    margin: auto 14px 14px;\r\n    padding: 9px 16px;\r\n    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dim) 100%);\r\n    color: var(--bg-deepest);\r\n    border-radius: var(--radius-sm);\r\n    font-size: 12px;\r\n    font-weight: 700;\r\n    display: flex;\r\n    align-items: center;\r\n    justify-content: center;\r\n    gap: 6px;\r\n    transition: all var(--duration) var(--ease-out);\r\n    box-shadow: 0 2px 10px rgba(0, 230, 118, 0.2);\r\n}'

new = b'.apply-btn {\r\n    margin: auto 14px 14px;\r\n    padding: 9px 16px;\r\n    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dim) 100%);\r\n    color: var(--bg-deepest);\r\n    border: 1px solid rgba(255,255,255,0.25);\r\n    border-radius: var(--radius-sm);\r\n    font-size: 12px;\r\n    font-weight: 700;\r\n    display: flex;\r\n    align-items: center;\r\n    justify-content: center;\r\n    gap: 6px;\r\n    transition: all var(--duration) var(--ease-out);\r\n    box-shadow: 0 2px 10px rgba(0, 230, 118, 0.2);\r\n}'

count = data.count(old)
print(f'Found {count} occurrences')
if count > 0:
    data = data.replace(old, new)
    with open(src, 'wb') as f:
        f.write(data)
    print('Added white border to apply-btn')
else:
    idx = data.find(b'.apply-btn')
    if idx >= 0:
        end = data.find(b'\n}\n\n', idx)
        print('Current:')
        print(repr(data[idx:end+5]))
