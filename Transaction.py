from typing import List
from collections import namedtuple

from Signature import *

Input  = namedtuple('Input', ['address', 'amount'])
Output = namedtuple('Output', ['address', 'amount'])
Detail = namedtuple('Detail', ['text', 'pub_keys'])

class Tx:
    def __init__(self):
        self.inputs  : List[Input]  = []
        self.outputs : List[Output] = []
        self.sigs    = []
        self.reqd    = []
    
    @property
    def total_in(self):
        return sum(i.amount for i in self.inputs)
    
    @property
    def total_out(self):
        return sum(o.amount for o in self.outputs)

    def add_input(self, from_addr : rsa.RSAPublicKey, amount):
        self.inputs.append(Input(ser_pub(from_addr), amount))
        self.add_reqd(from_addr)

    def add_output(self, to_addr : rsa.RSAPublicKey, amount):
        self.outputs.append(Output(ser_pub(to_addr), amount))

    def add_reqd(self, pub_key : rsa.RSAPublicKey):
        self.reqd.append(ser_pub(pub_key))

    def sign(self, private : rsa.RSAPrivateKey):
        self.sigs.append(sign(self.get_msg(), private))
    
    def get_msg(self):
        return "\n".join( [str(i) for i in self.inputs] 
                        + [str(o) for o in self.outputs])

    def get_details(self):
        ins = [i for i in self.inputs if i.amount > 0]
        outs = [o for o in self.outputs if o.amount > 0]

        if len(ins) == 0:
            return [Detail(f"{{0}} received {o.amount} BSM as a reward for mining.", [o.address]) for o in outs]

        if len(ins) == 1 and len(outs) == 1:
            i = ins[0]
            o = outs[0]
            if i.amount == o.amount:
                return [Detail(f"{{0}} paid {i.amount} BSM to {{1}}.", [i.address, o.address])]
        
        inDetails = [Detail(f"{{0}} paid {i.amount} BSM.", [i.address]) for i in ins]
        outDetails = [Detail(f"{{0}} received {o.amount} BSM.", [o.address]) for o in outs]
        return inDetails + outDetails
        
    def is_valid(self):
        ins  = [amount for _, amount in self.inputs]
        outs = [amount for _, amount in self.outputs]
        if any(num < 0 for num in ins + outs):
            return False
        if(sum(outs) > sum(ins) and sum(ins) != 0):
            return False
        has_signed = lambda key : any(verify(self.get_msg(), sig, key) for sig in self.sigs)
        return all(has_signed(load_pub(key)) for key in self.reqd)      