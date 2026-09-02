import io
import traceback
from PIL import Image
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
img = Image.new('RGB', (64, 64), color=(255, 255, 255))
buf = io.BytesIO()
img.save(buf, format='PNG')

try:
    resp = client.post('/extract-and-validate', files={'file': ('test.png', buf.getvalue(), 'image/png')})
    print('STATUS', resp.status_code)
    print(resp.text[:2000])
except Exception:
    traceback.print_exc()
