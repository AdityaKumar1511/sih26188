import urllib.request, re

url = 'https://sih26188-omega.vercel.app'
req = urllib.request.urlopen(url)
html = req.read().decode('utf-8')
scripts = re.findall(r'src="(/_next/static/[^"]+\.js)"', html)
print('Scripts count:', len(scripts))
for s in scripts:
    content = urllib.request.urlopen(url + s).read().decode('utf-8')
    matches = re.findall(r'https://[a-zA-Z0-9_\-\.]*onrender\.com[^"]*', content)
    if matches:
        print(s, 'matches:', set(matches))
