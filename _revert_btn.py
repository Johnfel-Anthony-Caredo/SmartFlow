import os

src = os.path.join(os.path.dirname(__file__), 'assets', 'styles.css')
with open(src, 'rb') as f:
    data = f.read()

# Current broken style
current = b'.apply-btn {\r\n    margin: 6px 14px 14px;\r\n    padding: 11px 16px;\r\n    background: #00c853;\r\n    color: #ffffff;\r\n    border: 2px solid #ffffff;\r\n    border-radius: var(--radius-sm);\r\n    font-size: 13px;\r\n    font-weight: 700;\r\n    letter-spacing: 0.5px;\r\n    display: flex;\r\n    align-items: center;\r\n    justify-content: center;\r\n    gap: 8px;\r\n    cursor: pointer;\r\n    transition: all var(--duration) var(--ease-out);\r\n    box-shadow: 0 2px 12px rgba(0, 200, 83, 0.35);\r\n}\r\n\r\n.apply-btn:hover {\r\n    transform: translateY(-1px);\r\n    box-shadow: 0 4px 20px rgba(0, 200, 83, 0.5);\r\n    background: #00e676;\r\n}\r\n\r\n.apply-btn:active {\r\n    transform: translateY(0);\r\n}'

# Original style before any changes
orig = b'.apply-btn {\r\n    margin: auto 14px 14px;\r\n    padding: 9px 16px;\r\n    background: linear-gradient(135deg, var(--accent) 0%, var(--accent-dim) 100%);\r\n    color: var(--bg-deepest);\r\n    border-radius: var(--radius-sm);\r\n    font-size: 12px;\r\n    font-weight: 700;\r\n    display: flex;\r\n    align-items: center;\r\n    justify-content: center;\r\n    gap: 6px;\r\n    transition: all var(--duration) var(--ease-out);\r\n    box-shadow: 0 2px 10px rgba(0, 230, 118, 0.2);\r\n}\r\n\r\n.apply-btn:hover {\r\n    transform: translateY(-1px);\r\n    box-shadow: 0 4px 16px rgba(0, 230, 118, 0.35);\r\n}\r\n\r\n.apply-btn:active {\r\n    transform: translateY(0);\r\n}'

idx = data.find(current)
if idx >= 0:
    data = data[:idx] + orig + data[idx+len(current):]
    with open(src, 'wb') as f:
        f.write(data)
    print('SUCCESS: Reverted to original')
else:
    print('FAIL: Current pattern not found')
    # Find the apply-btn block
    idx2 = data.find(b'.apply-btn')
    if idx2 >= 0:
        end = data.find(b'\n}\n\n', idx2)
        print('Current block:')
        print(repr(data[idx2:end+5]))
