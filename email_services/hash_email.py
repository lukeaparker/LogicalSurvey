import base64

def hash_email(email):
    # return the base64 encoded string
    return base64.b64encode(email.encode()).decode()

def unhash_email(hashed):
    # return the base64 decoded string
    return base64.b64decode(hashed.encode()).decode()

def generate_referral_url(email):
    hashed = hash_email(email)
    return "http://localhost:5000/referred/"+hashed