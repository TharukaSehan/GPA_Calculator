import urllib.request, json
import random

username = "testuser" + str(random.randint(1000, 9999))
print("Registering:", username)

req = urllib.request.Request(
    'http://localhost:8001/api/register',
    method='POST',
    headers={'Content-Type': 'application/json'},
    data=json.dumps({'username': username, 'password': 'password123', 'full_name': 'Test User', 'student_id': '12345'}).encode('utf-8')
)

try:
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read().decode('utf-8'))
    print("Reg response:", data)
    token = data['token']
    
    print("Testing me endpoint...")
    req2 = urllib.request.Request(
        'http://localhost:8001/api/me',
        headers={'Authorization': f'Bearer {token}'}
    )
    resp2 = urllib.request.urlopen(req2)
    print("Me response:", resp2.read().decode('utf-8'))

    print("Testing save-progress...")
    req3 = urllib.request.Request(
        'http://localhost:8001/api/save-progress',
        method='POST',
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'},
        data=json.dumps({'state': {'program': 'CIS', 'semesters': []}}).encode('utf-8')
    )
    resp3 = urllib.request.urlopen(req3)
    print("Save progress:", resp3.read().decode('utf-8'))

except Exception as e:
    print("ERROR:", e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
