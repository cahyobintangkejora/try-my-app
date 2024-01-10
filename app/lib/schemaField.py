from marshmallow.fields import Str, Integer, Date
from marshmallow.validate import Length, OneOf, Regexp, Range
from datetime import datetime
from flask_login import current_user

# global variable
SIGNED = {'signed': True}

'''
    DataTables
'''

# dt offset
dt_start = Integer(
    required=True,
)

dt_search = Str(
    required=False,
    validate=Length(max=30)
)