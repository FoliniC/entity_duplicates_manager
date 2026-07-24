with open('/config/tuya_gui.py', 'r') as f:
    content = f.read()

start = content.find('HTML_TEMPLATE = """')
if start == -1:
    print('HTML_TEMPLATE not found')
else:
    end = content.find('"""', start + 15)
    html = content[start+15:end]
    print(f'HTML length: {len(html)}')
    script_start = html.find('<script>')
    print(f'script_start: {script_start}')
    if script_start > 0:
        before = html[:script_start]
        print(f'customCommandModal in before: {"customCommandModal" in before}')
        after = html[script_start:]
        for f in ['openCustomCommandModal', 'closeCustomCommandModal', 'sendCustomCloudCommand']:
            print(f'{f} in after: {f in after}')