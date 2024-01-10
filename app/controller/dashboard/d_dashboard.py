from app import app
from flask import render_template, request
from app.repo.r_dashboard import dt_dashboardData, cari_data_dummy
from app.lib import ajaxNormalError, dataTableError, validationError, sf, Validasi

from marshmallow.fields import String
from marshmallow.validate import Length

@app.get("/")
def index():
    return render_template('dashboard/dashboard.html', title='Dashboard')

@app.get('/dt-caridata')
def dt_caridata():
    schema = {
        'start': sf.dt_start,
        'search': sf.dt_search
    }
    valid = Validasi(schema, request.args.to_dict())
    if valid.error:
        return validationError(valid.list_message)
    data = valid.getData()

    hasil = dt_dashboardData(data['search'], data['start']) 
    if hasil.is_error:
        return dataTableError()

    return {
        'recordsFiltered': hasil.dt_total,
        'data': hasil.result
    }
    
@app.get('/search-name')
def search_name():
    schema = {
        'name': String(required=True, allow_none=False, validate=[Length(min=1, max=5)])
    }
    valid = Validasi(schema, request.args.to_dict())
    if valid.error:
        return validationError(valid.list_message)
    data = valid.getData()

    hasil = cari_data_dummy(data['name'])
    if hasil.is_error:
        return ajaxNormalError()
    elif hasil.is_empty:
        return ajaxNormalError(f"Name <b>{data['name']}</b> tidak ditemukan!")
    
