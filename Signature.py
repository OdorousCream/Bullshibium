from cryptography.exceptions import *
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from pickle import dumps as serialize, loads as unserialize

def generate_keys():
    private_key = rsa.generate_private_key(public_exponent=65537,key_size=2048)
    public_key = private_key.public_key()
    return private_key, public_key

def sign(message, private_key : rsa.RSAPrivateKey):
    signature = private_key.sign(
        serialize(message),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature

def verify(message, signature : bytes, public_key : rsa.RSAPrivateKey):
    try:
        public_key.verify(
            signature,
            serialize(message),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except:
        return False

def ser_priv(key : rsa.RSAPrivateKey, pw : str):
        key_ser = key.private_bytes(
                        encoding = serialization.Encoding.PEM,
                        format = serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm = serialization.BestAvailableEncryption(bytes(pw, 'utf8')) 
                      )
        return serialize(key_ser)
    
def ser_pub(in_key : rsa.RSAPublicKey):
    key_ser = in_key.public_bytes(
                    encoding = serialization.Encoding.PEM,
                    format = serialization.PublicFormat.SubjectPublicKeyInfo
                )
    return serialize(key_ser)

def load_priv(in_key : bytes, pw : str):
    return serialization.load_pem_private_key( unserialize(in_key)
                                             , password = bytes(pw, 'utf8')
                                             )
def load_pub(in_key : bytes):
    return serialization.load_pem_public_key(unserialize(in_key))