from app.lib import PostgresDatabase

def dt_dashboardData(search:str, offset:int = 0):
    search = f"%{search.upper()}%"

    db = PostgresDatabase()
    query = '''
        SELECT
            id,
            name,
            email,
            age,
            address
        FROM
            datadummykaryawan
        WHERE
            UPPER(name) LIKE %(search)s
        ORDER BY id;
    '''
    param = {
        'offset': offset,
        'search': search
    }

    return db.execute_dt(query, param, print_query=True)

def cari_data_dummy(name:str):
    name = f"%{name.upper()}%"
    db = PostgresDatabase()
    query = '''
        SELECT
            name
        FROM
            datadummykaryawan
        WHERE
            UPPER(name) LIKE %(name)s
        LIMIT 1;
    '''
    param = {
        'name': name
    }

    return db.execute(query, param)