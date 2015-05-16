#! -*- coding: utf8 -*-
from trytond.model import ModelView, ModelSQL, fields
import datetime

__all__ = ['Cae']

class Cae(ModelSQL, ModelView):
    'Codigo de autorizacion electronico'
    __name__ = 'cooperar_secuencia_factura.cae'
    name = fields.Function(fields.Char("Numero"), 'get_name')
    numero = fields.Char("CAE", size=14, required=True)
    desde = fields.Date("Fecha desde", required=True)
    hasta = fields.Date("Vencimiento CAE", required=True)

    @classmethod
    def get_name(cls, cae_ids, name):
        res = {}
        for cae in cls.browse(cae_ids):
            res[cae.id] = str(cae.numero)
        return res

    @classmethod
    def get_ultimo(cls):
        ultimo = cls.search([], limit=1, order=[('desde', 'DESC')])
        if ultimo: return ultimo[0]
        else: return None

    @staticmethod
    def default_desde():
        return datetime.date.today()

    @classmethod
    def validate(cls, caes):
        """
        La validacion verifica que la fecha de comienzo
        del nuevo CAE sea mayor que el fin del ultimo.
        Tambien chequeamos que la fecha desde sea previa a la
        fecha hasta en los CAEs nuevos.
        """
        super(Cae, cls).validate(caes)
        for cae in caes:
            if cae.hasta < cae.desde:
                cls.raise_user_error('La fecha \'desde\' debe ser anterior a la fecha \'hasta\'.')
