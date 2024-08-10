import os
import base64

# Generate 32 random bytes
random_bytes = os.urandom(32)

# Encode the bytes using base64 to get a string similar to your example
secret_key = base64.b64encode(random_bytes).decode('utf-8')

print(secret_key)