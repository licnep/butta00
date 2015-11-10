__author__ = 'andrewgodbehere'
__all__ = ["analytics", "connection", "data", "utilities", "data_management"]


# noinspection PyPep8Naming
class JS_CONST(object):
    def __init__(self, val):
        self.CONST_VAL = val

    def __repr__(self):
        return repr(self.CONST_VAL)
