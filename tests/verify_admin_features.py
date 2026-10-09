import urllib.request
import json
import time

def req(url, method='GET', data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    b = json.dumps(data).encode('utf-8') if data is not None else None
    r = urllib.request.Request(url, data=b, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body

BASE = 'http://127.0.0.1:8000'

# 1. Public signup as admin is rejected (400)
status, res = req(f'{BASE}/api/v1/auth/register', 'POST', {
    'username': 'fakeadmin',
    'email': 'fakeadmin@test.com',
    'password': 'password123',
    'role': 'admin'
})
print('1. Public signup as admin rejected:', status == 400, res)

# 2. Public signup as normal user succeeds
status, res = req(f'{BASE}/api/v1/auth/register', 'POST', {
    'username': 'test_student',
    'email': 'student@test.com',
    'password': 'password123'
})
print('2. Public signup as user succeeds:', status == 200, res.get('user', {}).get('role'))
user_token = res.get('token')

# 3. Demo Admin login succeeds
status, res = req(f'{BASE}/api/v1/auth/login', 'POST', {
    'email': 'admin@contentgenie.ai',
    'password': 'admin123'
})
print('3. Demo Admin login succeeds:', status == 200, res.get('user', {}).get('role'))
admin_token = res.get('token')
admin_id = res.get('user', {}).get('id')

# 4. Demo User login succeeds
status, res = req(f'{BASE}/api/v1/auth/login', 'POST', {
    'email': 'user@contentgenie.ai',
    'password': 'user123'
})
print('4. Demo User login succeeds:', status == 200, res.get('user', {}).get('role'))

# 5. User blocked from admin analytics (403)
status, res = req(f'{BASE}/api/v1/auth/admin/analytics', 'GET', token=user_token)
print('5. User blocked from admin analytics (403):', status == 403)

# 6. Admin accesses analytics
status, res = req(f'{BASE}/api/v1/auth/admin/analytics', 'GET', token=admin_token)
print('6. Admin analytics status:', status == 200)
ah = res.get('account_health', {})
print(f"   Account Health: {ah.get('health_score')}% | Status: {ah.get('system_status')} | Storage: {ah.get('storage_engine')}")
metrics = res.get('metrics', {})
print(f"   Metrics: Total Tokens = {metrics.get('total_tokens')}, Input = {metrics.get('total_input_tokens')}, Output = {metrics.get('total_output_tokens')}, Cost = ${metrics.get('total_cost_usd')}")
events = res.get('recent_events', [])
print(f"   Recent Events count (for each use): {len(events)}")
if events:
    ev = events[0]
    print(f"   Sample Use: Agent={ev.get('agent')}, Model={ev.get('model')}, Input={ev.get('input_tokens')}, Output={ev.get('output_tokens')}, Cost=${ev.get('estimated_cost_usd')}")

# 7. Admin provisions a new user account
status, res = req(f'{BASE}/api/v1/auth/admin/users', 'POST', {
    'username': 'devops_eng',
    'email': 'devops@test.com',
    'full_name': 'DevOps Engineer',
    'password': 'password123',
    'role': 'user'
}, token=admin_token)
print('7. Admin created user:', status == 200, res.get('username'), res.get('role'))
new_uid = res.get('id')

# 8. Admin promotes user to admin
status, res = req(f'{BASE}/api/v1/auth/admin/users/{new_uid}/role', 'PATCH', {'role': 'admin'}, token=admin_token)
print('8. Admin promoted user:', status == 200, res)

# 9. Admin tries to demote self (blocked with 400)
status, res = req(f'{BASE}/api/v1/auth/admin/users/{admin_id}/role', 'PATCH', {'role': 'user'}, token=admin_token)
print('9. Admin prevented from demoting self (400):', status == 400, res)

# 10. Admin deletes user
status, res = req(f'{BASE}/api/v1/auth/admin/users/{new_uid}', 'DELETE', token=admin_token)
print('10. Admin deleted user:', status == 200, res)

# 11. Admin tries to delete self (blocked with 400)
status, res = req(f'{BASE}/api/v1/auth/admin/users/{admin_id}', 'DELETE', token=admin_token)
print('11. Admin prevented from deleting self (400):', status == 400, res)
