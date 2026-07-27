import re

path = r'd:\News_Dashboard\frontend\src\api\newsApi.js'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the catch block condition
old_catch = r"if \(err\.name === 'TypeError' \|\| err\.message === 'Failed to fetch' \|\| err\.message\.includes\('fetch'\)\) \{"
new_catch = r"if (err.name === 'TypeError' || err.message === 'Failed to fetch') {"
content = re.sub(old_catch, new_catch, content)

# Replace "Could not reach the backend — is the server running?" with "Backend unreachable"
old_msg1 = r'"ConnectionError: Could not reach the backend — is the server running\?"'
new_msg1 = r'"ConnectionError: Backend unreachable"'
content = re.sub(old_msg1, new_msg1, content)

# Replace "Could not reach the backend" with "Backend unreachable"
old_msg2 = r'"ConnectionError: Could not reach the backend"'
new_msg2 = r'"ConnectionError: Backend unreachable"'
content = re.sub(old_msg2, new_msg2, content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated newsApi.js")
