from app.lib import PostgresDatabase

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
