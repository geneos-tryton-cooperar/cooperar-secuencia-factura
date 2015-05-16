from string import Template

from trytond.model import ModelSQL, ModelView, fields
from ...tools import datetime_strftime
from ...pool import Pool
from ...transaction import Transaction


class Sequence(ModelSQL, ModelView):
    "Sequence"
    __name__ = 'ir.sequence'

    idempresa = fields.Char('Id Empresa', required=False)
    idsucursal = fields.Char('Id Sucursal', required=False)
    grupocbte = fields.Char('Grupo Comprobante', required=False)


    @classmethod
    def get_id(cls, domain):
        '''
        Return sequence value for the domain
        '''
        if isinstance(domain, cls):
            domain = domain.id
        if isinstance(domain, (int, long)):
            domain = [('id', '=', domain)]

        # bypass rules on sequences
        with Transaction().set_context(user=False):
            with Transaction().set_user(0):
                try:
                    sequence, = cls.search(domain, limit=1)
                except TypeError:
                    cls.raise_user_error('missing')
            date = Transaction().context.get('date')
            #pdb.set_trace()
            datos= [sequence.idempresa, sequence.idsucursal, sequence.grupocbte]#,sequence.puntoVenta]
            return '%s%s%s' % (
                cls._process(sequence.prefix, date=date, otros=datos),
                cls._get_sequence(sequence),
                cls._process(sequence.suffix, date=date, otros=datos),
                )


    @staticmethod
    def _process(string, date=None, otros=None):
        pool = Pool()
        Date = pool.get('ir.date')

        if not date:
            date = Date.today()
        if not otros:
            otros = ["","","",""]

        year = datetime_strftime(date, '%Y')
        month = datetime_strftime(date, '%m')
        day = datetime_strftime(date, '%d')

        res = Template(string or '').substitute(
            year=year,
            month=month,
            day=day,
            id_empresa=otros[0],
            id_sucursal=otros[1],
            grupo_cbte=otros[2],
            #punto_venta=otros[3],
            )
        return res

class SequenceStrict(Sequence):
    "Sequence Strict"
    __name__ = 'ir.sequence.strict'
