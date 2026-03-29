import urllib.request, json
try:
    req = urllib.request.Request('http://127.0.0.1:8000/api/analytics', data=json.dumps({'table':'scam_taxonomy'}).encode('utf-8'), headers={'Content-Type':'application/json'})
    print(urllib.request.urlopen(req).read().decode())
except Exception as e:
    if hasattr(e, 'read'):
        print(e.read().decode())
    else:
        print(str(e))
