import io
import urllib.request
from PIL import Image

img = Image.new('RGB', (64, 64), color=(255, 255, 255))
buf = io.BytesIO()
img.save(buf, format='PNG')
data = buf.getvalue()
boundary = '----debug-boundary'
body = (
    f'--{boundary}\r\n'
    'Content-Disposition: form-data; name="file"; filename="test.png"\r\n'
    'Content-Type: image/png\r\n\r\n'
).encode() + data + f'\r\n--{boundary}--\r\n'.encode()

req = urllib.request.Request(
    'http://localhost:8000/extract-and-validate',
    data=body,
    headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
    method='POST',
)

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        print('STATUS', resp.status)
        print(resp.read(2000).decode('utf-8', 'ignore'))
except Exception as e:
    print(type(e).__name__, e)
