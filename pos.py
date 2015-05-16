#! -*- coding: utf8 -*-
from trytond.model import ModelView, ModelSQL, fields

__all__ = ['Pos', 'PosSequence']


class Pos(ModelSQL, ModelView):
    'Punto de Venta'
    __name__ = 'account.pos'

    name = fields.Function(fields.Char('Nombre'), 'get_name')
    number = fields.Integer('Punto de Venta AFIP', required=True,
        help=u"Prefijo de emisión habilitado en AFIP")
    pos_sequences = fields.One2Many('account.pos.sequence', 'pos',
        'Punto de Venta')
    pos_type = fields.Selection([
            ('manual', u'Manual'),
            ('electronic', u'Electronic'),
            ('fiscal_printer', u'Fiscal Printer'),
            ], 'Tipo de Punto de Venta', required=True)

    @staticmethod
    def default_pos_type():
        return 'manual'

    @classmethod
    def get_name(cls, account_pos, name):
        res = {}
        for pos in cls.browse(account_pos):
            res[pos.id] = str(pos.number)+ ' - '+\
            dict(pos.fields_get(fields_names=['pos_type'])\
            ['pos_type']['selection'])[pos.pos_type]
        return res


class PosSequence(ModelSQL, ModelView):
    'Secuencias de Punto de Venta'
    __name__ = 'account.pos.sequence'

    pos = fields.Many2One('account.pos', 'Punto de Venta')
    invoice_type = fields.Selection([
            ('', ''),
            ('17', u'17-Factura A'),
            ('2', u'02-Nota de Débito A'),
            ('3', u'03-Nota de Crédito A'),
            ('4', u'04-Recibos A'),
            ('5', u'05-Nota de Venta al Contado A'),
            ('18', u'18-Factura B'),
            ('7', u'07-Nota de Débito B'),
            ('8', u'08-Nota de Crédito B'),
            ('9', u'09-Recibos B'),
            ('10', u'10-Notas de Venta al Contado B'),
            ('11', u'11-Factura C'),
            ('12', u'12-Nota de Débito C'),
            ('13', u'13-Nota de Crédito C'),
            ('15', u'Recibo C'),
            ('19', u'19-Factura E'),
            ('20', u'20-Nota de Débito E'),
            ('21', u'21-Nota de Crédito E'),
            ], 'Tipo Comprobante AFIP', required=True,
        help="Tipo de Comprobante AFIP")
    invoice_sequence = fields.Property(fields.Many2One('ir.sequence',
            'Secuencia', required=True,
            domain=[('code', '=', 'account.invoice')],
            context={'code': 'account.invoice'}))

    def get_rec_name(self, name):
        type2name = {}
        for type, name in self.fields_get(fields_names=['invoice_type']
                )['invoice_type']['selection']:
            type2name[type] = name
        return type2name[self.invoice_type][3:]
