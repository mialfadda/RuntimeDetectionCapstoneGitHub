import sys
sys.path.insert(0, '/Users/aljohara/PycharmProjects/capstone')

from backend.app.runtime.url_extractor import extract_url_features

# Test with a normal URL
print('--- Google ---')
print(extract_url_features('https://www.google.com'))

# Test with a suspicious URL
print('--- Suspicious ---')
print(extract_url_features('http://login-verify.account-secure.com/banking/confirm?user=test'))

# Test with an IP address URL
print('--- IP Address ---')
print(extract_url_features('http://192.168.1.1/update/password'))