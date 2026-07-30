import subprocess, time, httpx, os, signal

if os.path.exists('data/app.db'):
    os.remove('data/app.db')

proc = subprocess.Popen(
    ['python', '-m', 'uvicorn', 'app.main:app', '--port', '8000'],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
time.sleep(4)

try:
    r = httpx.get('http://127.0.0.1:8000/docs', timeout=10)
    print('Docs:', r.status_code)

    r = httpx.post('http://127.0.0.1:8000/api/auth/register',
                   json={'username': 'alice', 'password': 'pass123'}, timeout=10)
    print('Register:', r.status_code, r.text)

    r = httpx.post('http://127.0.0.1:8000/api/auth/login',
                   json={'username': 'alice', 'password': 'pass123'}, timeout=10)
    print('Login:', r.status_code, r.text)
except Exception as e:
    print('Error:', e)
    out, err = proc.communicate(timeout=5)
    if err:
        print('Server stderr:', err.decode()[-1500:])
finally:
    proc.terminate()
    proc.wait(timeout=5)
