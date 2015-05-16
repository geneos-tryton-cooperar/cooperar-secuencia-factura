from trytond.pool import Pool
from .secuencia import Sequence, SequenceStrict
from .invoice import Invoice
from .pos import Pos, PosSequence
from .cae import Cae

def register():
    Pool.register(
        Sequence,
        SequenceStrict,
        Pos,
        PosSequence,
        Invoice,
        Cae,
        module='cooperar-secuencia-factura', type_='model'
    )

