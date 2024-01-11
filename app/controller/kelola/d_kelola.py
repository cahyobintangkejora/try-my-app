from app import app
from flask import render_template, request
from app.repo.r_kelola import insert_data, delete_data, edit_data, insert_data_faker
from app.lib import ajaxNormalError, dataTableError, validationError, sf, Validasi
from faker import Faker
from flask import jsonify


from marshmallow.fields import String, Integer
from marshmallow.validate import Length, Range

@app.get("/kelola")
def kelolaren():
    return render_template('kelola/kelola.html', title='Kelola Data')

@app.post('/insert_data')
def insertDataKaryawan():
    schema = {
        'name': String(required=True, allow_none=False, validate=[Length(min=1, max=50)]),
        'email': String(required=True, allow_none=False, validate=[Length(min=1, max=50)]),
        'age': Integer(required=True, allow_none=False, validate=[Range(min=1, max=200)]),
        'address': String(required=True, allow_none=False, validate=[Length(min=1, max=100)])
    }

    valid = Validasi(schema, request.form.to_dict())
    if valid.error:
        return validationError(valid.list_message)
    
    data = valid.getData()
    hasil = insert_data(data['name'], data['email'], data['age'], data['address'])

    if hasil.is_error:
        return ajaxNormalError()

    return {
        'data': hasil.result
    }
    

@app.post('/delete_data')
def deleteDataKaryawan():
    id = request.form.get('id')

    # Validasi id sesuai kebutuhan (contoh: pastikan id adalah integer)
    try:
        id = int(id)
    except ValueError:
        return validationError("Invalid id. Please provide a valid integer.")

    # Panggil fungsi remove_data untuk menghapus data
    hasil = delete_data(id)

    if hasil.is_error:
        return ajaxNormalError()

    return {
        'data': hasil.result
    }

@app.post('/edit_data')
def editDataKaryawan():
    id = request.form.get('id')

    # Validasi id sesuai kebutuhan (contoh: pastikan id adalah integer)
    try:
        id = int(id)
    except ValueError:
        return validationError("Data yang id yang diambil harus berupa integer.")

    # Ambil data dari form
    name = request.form.get('name')
    email = request.form.get('email')
    age = request.form.get('age')
    address = request.form.get('address')

    # Validasi data sesuai kebutuhan
    schema = {
        'name': String(required=True, allow_none=False, validate=[Length(min=1, max=50)]),
        'email': String(required=True, allow_none=False, validate=[Length(min=1, max=50)]),
        'age': Integer(required=True, allow_none=False, validate=[Range(min=1, max=200)]),
        'address': String(required=True, allow_none=False, validate=[Length(min=1, max=100)])
    }

    valid = Validasi(schema, {'name': name, 'email': email, 'age': age, 'address': address})
    if valid.error:
        return validationError(valid.list_message)

    data = valid.getData()

    # Panggil fungsi edit_data untuk mengedit data
    hasil = edit_data(id, data['name'], data['email'], data['age'], data['address'])

    if hasil.is_error:
        return ajaxNormalError()

    return {
        'data': hasil.result
    }

@app.post('/insert_datafaker')
def insertDataFaker():
    # Memeriksa apakah menggunakan data faker
    use_fake_data = request.form.get('use_fake_data', 'false')

    if use_fake_data.lower() == 'true':
        # Menggunakan data faker untuk menghasilkan 1.000.000 data
        fake_data_result = insert_data_faker(50)
        return jsonify({'data': fake_data_result})

    # Jika tidak menggunakan data faker, proses seperti sebelumnya
    schema = {
        'name': String(required=True, allow_none=False, validate=[Length(min=1, max=50)]),
        'email': String(required=True, allow_none=False, validate=[Length(min=1, max=50)]),
        'age': Integer(required=True, allow_none=False, validate=[Range(min=1, max=200)]),
        'address': String(required=True, allow_none=False, validate=[Length(min=1, max=200)])
    }

    valid = Validasi(schema, request.form.to_dict())
    if valid.error:
        return validationError(valid.list_message)

    data = valid.getData()
    name, email, age, address = data['name'], data['email'], data['age'], data['address']

    hasil = insert_data_faker(name, email, age, address)

    if hasil.is_error:
        return ajaxNormalError()

    return {
        'data': hasil.result
    }
