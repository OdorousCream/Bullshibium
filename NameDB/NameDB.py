from typing import List
from sqlalchemy import Column, Integer, String, PickleType, create_engine, true
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from Signature import ser_pub, load_pub

engine = create_engine('sqlite:///NameDB/names.db?check_same_thread=False', echo = False)

base = declarative_base()

class NameKeyPair(base):
    __tablename__ = "name_key_pair"
    pair_id = Column(Integer, primary_key = True)
    name = Column(String)
    key = Column(PickleType)

    def __init__(self, name, key):
        self.name = name
        self.key = key

class IP(base):
    __tablename__ = "ip"
    ip_id = Column(Integer, primary_key = True)
    ip = Column(String)

    def __init__(self, ip):
        self.ip = ip

def create_db():
    base.metadata.create_all(engine)

def get_session(session : Session = None):
    if not session:
        session = sessionmaker(bind = engine)()
    return session

def add_pair(name : str, key : RSAPublicKey):
    session = get_session()
    session.add(NameKeyPair(name, ser_pub(key)))
    session.commit()

def add_ip(ip : str):
    session = get_session()
    session.add(IP(ip))
    session.commit()

def key_to_name(key : RSAPublicKey) -> str:
    session = get_session()
    pairs = session.query(NameKeyPair)

    pairs = [pair for pair in pairs if load_pub(pair.key).public_numbers() == key.public_numbers()]
    return pairs[0].name

def name_to_key(name : str) -> RSAPublicKey:
    session = get_session()
    pair = session.query(NameKeyPair).filter(NameKeyPair.name == name)[0]
    return load_pub(pair.key)

def has_name(name : str) -> bool:
    session = get_session()
    pairs = session.query(NameKeyPair).filter(NameKeyPair.name == name)
    return pairs.count() > 0

def has_ip(ip : str) -> bool:
    session = get_session()
    ips = session.query(IP).filter(IP.ip == ip)
    return ips.count() > 0

def name_has_key(name: str, key: RSAPublicKey):
    return name_to_key(name).public_numbers() == key.public_numbers()

def get_all_pairs() -> List[NameKeyPair]:
    session = get_session()
    pairs = session.query(NameKeyPair)
    return [pair for pair in pairs]

def get_all_ips() -> List[IP]:
    session = get_session()
    ips = session.query(IP)
    return [entry.ip for entry in ips]