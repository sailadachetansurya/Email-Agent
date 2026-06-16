from hashlib import sha256

def hash_string(string):
    result = sha256(string.encode())
    return result.hexdigest()
    
def compare_hashes(hash1, hash2):
    return hash1 == hash2


