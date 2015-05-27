#! -*- coding: utf8 -*-
#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.model import Workflow, fields, ModelView
from trytond.pyson import Eval, And
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from cStringIO import StringIO as StringIO
from PIL import Image, ImageDraw

import pdb

__all__ = ['Invoice']
__metaclass__ = PoolMeta

_STATES = {
    'readonly': Eval('state') != 'draft',
}
_DEPENDS = ['state']

_POS_STATES = _STATES.copy()
_POS_STATES.update({
        'required': And(Eval('type').in_(['out_invoice', 'out_credit_note']), ~Eval('state').in_(['draft'])),
        'invisible': Eval('type').in_(['in_invoice', 'in_credit_note']),
            })

INVOICE_TYPE_AFIP_CODE = {
        ('out_invoice', 'A'): ('17', u'17-Factura A'),
        ('out_invoice', 'B'): ('18', u'18-Factura B'),
        ('out_invoice', 'C'): ('11', u'11-Factura C'),
        ('out_invoice', 'E'): ('19', u'19-Factura E'),
        ('out_credit_note', 'A'): ('3', u'03-Nota de Crédito A'),
        ('out_credit_note', 'B'): ('8', u'08-Nota de Crédito B'),
        ('out_credit_note', 'C'): ('13', u'13-Nota de Crédito C'),
        ('out_credit_note', 'E'): ('21', u'21-Nota de Crédito E'),
        }

class Invoice:
    'Invoice'
    __name__ = 'account.invoice'

    pos = fields.Many2One('account.pos', 'Punto de Venta',
        on_change=['pos', 'party', 'type', 'company'],
        states=_POS_STATES, depends=_DEPENDS)
    invoice_type = fields.Many2One('account.pos.sequence', 'Tipo de Factura',
        domain=([('pos', '=', Eval('pos'))]),
        states=_POS_STATES, depends=_DEPENDS)
    
    #Que se vea solo si es factura proveedor
    #invoice_type_proveedor = fields.Many2One('account.pos.sequence', 'Tipo de Factura',
    #    domain=([('pos', '=', Eval('pos'))]),
    #    states=_POS_STATES, depends=_DEPENDS)


    @classmethod
    def __setup__(cls):
        super(Invoice, cls).__setup__()

        cls._error_messages.update({
            'missing_sequence':
                u'No existe una secuencia para facturas del tipo: %s',
            'too_many_sequences':
                u'Existe mas de una secuencia para facturas del tipo: %s',
            'missing_company_iva_condition': ('Falta CUIT de la Cooperativa'),
            'missing_party_iva_condition': ('La condicion de IVA Cliente'
                    '"%(party)s" esta ausente.'),
            'not_invoice_type':
                u'El campo «Tipo de factura» en «Factura» es requerido.',
            'missing_POS':
                u'Falta Punto de Venta',
            })

    @classmethod
    def validate(cls, invoices):
        super(Invoice, cls).validate(invoices)
        for invoice in invoices:
            invoice.check_invoice_type()

    def check_invoice_type(self):
        if not self.party.iva_condition:
            self.raise_user_error('missing_party_iva_condition', {
                    'party': self.party.rec_name,
                    })

    def tipo_letra_factura(self):

        client_iva = None
        if self.party:
            client_iva = self.party.iva_condition

        #Comenzamos por determinar el tipo de factura.
        if client_iva is None:
            self.raise_user_error('missing_party_iva_condition', {
                    'party': self.party.rec_name,
                    })
        if client_iva == 'responsable_inscripto':
            kind = 'A'
        elif client_iva == 'consumidor_final':
            kind = 'B'
        elif self.party.vat_country is None:
            self.raise_user_error('unknown_country')
        elif self.party.vat_country == u'AR':
            kind = 'B'
        else:
            kind = 'E'

        return kind

    def cod_letra_factura(self):
        kind = self.tipo_letra_factura()
        invoice_type, invoice_type_desc = INVOICE_TYPE_AFIP_CODE[
            (self.type, kind)
            ]
        return invoice_type

    def on_change_pos(self):
        import pudb;pu.db
        
        PosSequence = Pool().get('account.pos.sequence')
        if not self.pos:
            return {'invoice_type': None}

        res = {}
        kind = self.tipo_letra_factura()
        if not kind:
                return True

        #A partir del tipo de factura, buscamos el PosSequence del que vamos
        #a sacar el nuevo numero de sequencia.
        invoice_type, invoice_type_desc = INVOICE_TYPE_AFIP_CODE[
            (self.type, kind)
            ]
        sequences = PosSequence.search([
            ('pos', '=', self.pos.id),
            ('invoice_type', '=', invoice_type)
            ])
        if len(sequences) == 0:
            self.raise_user_error('missing_sequence', invoice_type_desc)
        elif len(sequences) > 1:
            self.raise_user_error('too_many_sequences', invoice_type_desc)
        else:
            res['invoice_type'] = sequences[0].id

        return res

    def set_number(self):
        '''
        Set number to the invoice
        '''
        #import pudb;pu.db
        pool = Pool()
        #PosSequence = Pool().get('account.pos.sequence')
        Period = pool.get('account.period')
        Sequence = pool.get('ir.sequence')
        Date = pool.get('ir.date')

        if self.number:
            return

        test_state = True
        if self.type in ('in_invoice', 'in_credit_note'):
            test_state = False

        # accounting_date = self.accounting_date or self.invoice_date
        # period_id = Period.find(self.company.id,
        #      date=accounting_date, test_state=test_state)
        # period = Period(period_id)
        # sequence = period.get_invoice_sequence(self.type)
        # if not sequence:
        #      self.raise_user_error('no_invoice_sequence', {
        #              'invoice': self.rec_name,
        #              'period': period.rec_name,
        #              })
        with Transaction().set_context(date=self.invoice_date or Date.today()):
            vals = {}
            # pdb.set_trace()
            if self.type == 'out_invoice' or self.type == 'out_credit_note':
                # number = Sequence._get_sequence(sequence)
                number = Sequence._get_sequence(self.invoice_type.invoice_sequence)
                vals['number'] = '%04d-%08d' % (self.pos.number, int(number))
            else:
                accounting_date = self.accounting_date or self.invoice_date
                period_id = Period.find(self.company.id,
                    date=accounting_date, test_state=test_state)
                period = Period(period_id)
                sequence = period.get_invoice_sequence(self.type)
                if not sequence:
                    self.raise_user_error('no_invoice_sequence', {
                        'invoice': self.rec_name,
                        'period': period.rec_name,
                    })

                number = Sequence.get_id(sequence.id)
                #number = Sequence.get_id(self.invoice_type.invoice_sequence.id)
                vals ['number']= number
            if (not self.invoice_date
                    and self.type in ('out_invoice', 'out_credit_note')):
                vals['invoice_date'] = Transaction().context['date']
        self.write([self], vals)


        '''
        import pudb;pu.db
        pool = Pool()
        Period = pool.get('account.period')
        Sequence = pool.get('ir.sequence.strict')
        Date = pool.get('ir.date')

        if self.number:
            return

        test_state = True
        if self.type in ('in_invoice', 'in_credit_note'):
            test_state = False

        accounting_date = self.accounting_date or self.invoice_date
        period_id = Period.find(self.company.id,
            date=accounting_date, test_state=test_state)
        period = Period(period_id)
        sequence = period.get_invoice_sequence(self.type)
        if not sequence:
            self.raise_user_error('no_invoice_sequence', {
                    'invoice': self.rec_name,
                    'period': period.rec_name,
                    })

        with Transaction().set_context(date=self.invoice_date or Date.today()):
            vals = {}
            if self.type == 'out_invoice' or self.type == 'out_credit_note':
                number = Sequence._get_sequence(sequence)
                vals['number'] = '%04d-%08d' % (self.pos.number, int(number))
            else:
                number = Sequence.get_id(sequence.id)
                vals ['number']= number
            if (not self.invoice_date
                    and self.type in ('out_invoice', 'out_credit_note')):
                vals['invoice_date'] = Transaction().context['date']
        self.write([self], vals)
        '''

    @classmethod
    @ModelView.button
    @Workflow.transition('posted')
    def post(cls, invoices):
        Move = Pool().get('account.move')
        moves = []
        for invoice in invoices:
            if invoice.type == u'out_invoice' or invoice.type == u'out_credit_note':
                if not invoice.invoice_type:
                    invoice.raise_user_error('not_invoice_type')
            invoice.set_number()
            moves.append(invoice.create_move())
        cls.write(invoices, {'state': 'posted',})
        Move.post(moves)
        for invoice in invoices:
            if invoice.type in ('out_invoice', 'out_credit_note'):
                invoice.print_invoice()
