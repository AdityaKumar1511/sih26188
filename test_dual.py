import httpx

with open(r'C:/Users/Yuvraj Atri/.gemini/antigravity/brain/b14854f3-891b-4187-96da-9eb366e04f94/actual_card.png', 'rb') as fp:
    card_bytes = fp.read()

files = {
    'file': ('card.png', card_bytes, 'image/png'),
    'live_face': ('passenger_live_snapshot.jpg', card_bytes, 'image/jpeg')
}
headers = {
    'Origin': 'https://sih26188-omega.vercel.app'
}

try:
    print('Sending dual image POST request to Render...')
    res = httpx.post(
        'https://sih-sentinel-backend.onrender.com/extract-and-validate',
        files=files,
        headers=headers,
        timeout=60.0
    )
    print('Status:', res.status_code)
    print('Response:', res.json().get('verdict'), res.json().get('authenticity_score'))
except Exception as e:
    print('Error:', e)
