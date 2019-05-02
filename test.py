import hashlib

for i in range(10):
    hash_text = hashlib.md5("all-output_0-134".encode()).hexdigest()
    print(hash_text)
