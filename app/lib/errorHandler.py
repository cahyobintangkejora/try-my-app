'''
    File ini berisi error handler ketika ada error di controller.
    Controller sendiri biasanya menerima 3 jenis request:
        1. Request dari data table (berupa ajax)
        2. Request dari ajax
        3. Normal request (biasanya dari form)
    ketika terjadi error, maka perlu di handle dgn baik, sehingga dibuatlah module ini
'''
from flask import make_response, render_template, jsonify, flash
from typing import List

default_err_message = 'Terjadi kesalahan internal!. Silahkan hubungi bagian IT!'


def dataTableError(error_message: str = default_err_message):
    response = {
        'error': error_message,
        'draw': 1,
        'recordsFiltered': 0,
        'recordsTotal': 0,
        'data': []
    }

    return jsonify(response)


def responseError(error_message: str = default_err_message):
    return render_template('error/500.html', error_message=error_message)


def ajaxNormalError(error_message: str = default_err_message, status_code: int = 500):
    responseJSON = {
        'errorType': 'ajaxNormalError',
        'result': error_message
    }
    return make_response(responseJSON, int(status_code), {'Content-Type': 'application/json'})

def validationError(list_message: List = []):
    responseJSON= {
        'errorType': 'validationError',
        'result': list_message 
    }
    return make_response(responseJSON, 400, {'Content-Type': 'application/json'})

def ajaxRedirect(location: str = '/', data: dict = {}, method: str = 'GET'):
    responseJSON = {
        'errorType': 'ajaxRedirect',
        'result': {
            'location': location,
            'data': data,
            'method': method
        }
    }
    return make_response(responseJSON, 302, {'Content-Type': 'application/json'})