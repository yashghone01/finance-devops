import urllib.request
import urllib.parse
import urllib.error

data = urllib.parse.urlencode({'username':'test@example.com', 'password':'password123'}).encode()
req = urllib.request.Request('https://finance-api-docker.onrender.com/login', data=data)
req.add_header('Content-Type', 'application/x-www-form-urlencoded')
try:
    print('OK', urllib.request.urlopen(req).getcode())
except urllib.error.HTTPError as e:
    print('HTTP ERROR', e.code, e.read().decode())
except Exception as e:
    print('OTHER ERROR', e)
