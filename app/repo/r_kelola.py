from app.lib import PostgresDatabase
from faker import Faker

def insert_data(name:str, email:str, age:int, address:str):
    db = PostgresDatabase()
    query = '''
        INSERT INTO datadummykaryawan (name, email, age, address)
        VALUES (%(name)s, %(email)s, %(age)s, %(address)s)
        RETURNING id;
    '''
    param = {
        'name': name,
        'email': email,
        'age': age,
        'address': address
    }

    return db.execute(query, param, print_query=True)

def delete_data(id: int):
    db = PostgresDatabase()
    query = '''
        DELETE FROM datadummykaryawan
        WHERE id = %(id)s;
    '''
    param = {
        'id': id
    }

    return db.execute(query, param, print_query=True)

def edit_data(id: int, name: str, email: str, age: int, address: str):
    db = PostgresDatabase()
    query = '''
        UPDATE datadummykaryawan
        SET
            name = %(name)s,
            email = %(email)s,
            age = %(age)s,
            address = %(address)s
        WHERE
            id = %(id)s;
    '''
    param = {
        'id': id,
        'name': name,
        'email': email,
        'age': age,
        'address': address
    }

    return db.execute(query, param, print_query=True)

fake = Faker()
def generate_fake_data():
    name = fake.name()
    email = fake.email()
    age = fake.random_int(min=18, max=60)
    address = fake.address()
    return name, email, age, address

def insert_data_faker(num_entries):
    db = PostgresDatabase()
    fake_data_list = [generate_fake_data() for _ in range(num_entries)]
    result_list = []

    for fake_data in fake_data_list:
        name, email, age, address = fake_data
        query = '''
            INSERT INTO datadummykaryawan (name, email, age, address)
            VALUES (%(name)s, %(email)s, %(age)s, %(address)s)
            RETURNING id;
        '''
        param = {
            'name': name,
            'email': email,
            'age': age,
            'address': address
        }
        hasil = db.execute(query, param, print_query=True)
        
        if not hasil.is_error:
            result_list.append(hasil.result)
            
    return result_list