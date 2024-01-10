"""
    Modul postgresKonektor, develop by Candra (20 Feb 2023)
    Version: 4.10 (15 September 2023).
"""

import psycopg2
from psycopg2 import OperationalError
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import execute_values, Json
from psycopg2.extensions import Diagnostics, register_adapter
import traceback
from textwrap import dedent
import sqlparse
import inspect
from typing import Dict, List, Tuple, Union
import warnings
from datetime import datetime
import os

# adapt any Python dictionary to JSON
register_adapter(dict, Json)

VOID_DIAG = Diagnostics(psycopg2.Error())
global_conn_exc = None

try:
    global_connection_pool = {
        "default": ThreadedConnectionPool(
            user="postgres",
            password="admin",
            host="localhost",
            port="5432",
            database="postgres",
            minconn=0,
            maxconn=2,
            connect_timeout=3,
        ),
    }
except OperationalError as e:
    global_connection_pool = None
    global_conn_exc = e

class PsycopgError(Exception):
    '''
        This class generalizes exceptions that can occur during database operations,
        whether they originate from psycopg2 (https://www.psycopg.org/docs/errors.html) or are other potential exceptions.
        It ensures that all exceptions have properties 'pgerror', 'pgcode', and 'diag' similar to psycopg2.Error
    '''

    def __init__(self, pgcode:str, pgerror:str, diag:Diagnostics=VOID_DIAG) -> None:
        super().__init__(pgerror)
        self.pgcode = pgcode
        self.pgerror = pgerror
        self.diag = diag

    @property
    def pgcode(self) -> None:
        return self._pgcode
    
    @pgcode.setter
    def pgcode(self, value:str) -> None:
        self._pgcode = value
    
    @property
    def pgerror(self) -> str:
        return self._pgerror
    
    @pgerror.setter
    def pgerror(self, value:str) -> None:
        self._pgerror = value

    @property
    def diag(self) -> Diagnostics:
        return self._diag
    
    @diag.setter
    def diag(self, value:Diagnostics) -> None:
        if not isinstance(value, Diagnostics):
            raise ValueError(f"{value} is not instance of <psycopg2.extensions.Diagnostics>!")
        self._diag = value

    def __str__(self) -> str:
        return f"<pgcode={self.pgcode} pgerror={self.pgerror}>"
    
    def __repr__(self) -> str:
        return self.__str__()

class DBResponse:
    def __init__(self, pgcode:str, pgerror:str, diag:Diagnostics, result: List = [], notices: List = None) -> None:
        self.pgcode = pgcode
        self.pgerror = pgerror
        self.diag = diag
        self.result = result
        self.notices = notices

    @property
    def pgcode(self) -> str:
        '''
            pgcode: berisi error code dari postgres, sumber: https://www.postgresql.org/docs/current/errcodes-appendix.html#ERRCODES-TABLE
        '''
        return self._pgcode

    @pgcode.setter
    def pgcode(self, value:str) -> None:
        self._pgcode = value

    @property
    def pgerror(self) -> str:
        '''
            pgerror: berisi detail pesan error, None jika tidak ada error.
        '''
        return self._pgerror

    @pgerror.setter
    def pgerror(self, value:str) -> None:
        self._pgerror = value

    @property
    def diag(self) -> Diagnostics:
        '''
            diag: untuk mendiagnosa error lebih dalam,
            sumber: https://www.psycopg.org/docs/extensions.html#psycopg2.extensions.Diagnostics.
        '''
        return self._diag
    
    @diag.setter
    def diag(self, value:Diagnostics) -> None:
        if not isinstance(value, Diagnostics):
            raise ValueError("not instance of <psycopg2.extensions.Diagnostics>!")
        self._diag = value

    @property
    def result(self) -> List:
        '''
            result: berisi List[Dict] dari hasil query, jika error akan berisi List kosong
        '''
        return self._result

    @result.setter
    def result(self, value:List) -> None:
        if not isinstance(value, list):
            raise ValueError("prop result bertipe list!")
        self._result = value

    @property
    def notices(self) -> List:
        '''
            notices: berisi List[str] dari database output / messages.
            Misal di-query ada code "RAISE NOTICE 'hallo dunia'", maka akan ditampung di-sini.
        '''
        if self._notices is None:
            raise ValueError("Notices belum disetting!")
        return self._notices

    @notices.setter
    def notices(self, value:List) -> None:
        self._notices = value

    @property
    def dt_total(self) -> int:
        '''
            Untuk prop 'recordsFiltered' pada DataTables Server (dt_server)
        '''
        return self._dt_total

    @dt_total.setter
    def dt_total(self, value:int) -> None:
        if not isinstance(value, int):
            raise ValueError("Hanya boleh integer!")
        self._dt_total= value

    @property
    def status(self) -> bool:
        '''
            Bernilai Ture bila operasi DB sukses (pgcode == '00000'), False jika terjadi error
        '''
        return self.pgcode == '00000'

    @property
    def is_error(self) -> bool:
        '''
            Bernilai True bila terjadi error (pgcode != '00000'), False jika tidak ada error
        '''
        return self.pgcode != '00000'

    @property
    def is_empty(self) -> bool:
        '''
            Bernilai True bila result DB panjangnya 0 (len(self.result) == 0), False jika panjang result > 0
        '''
        if self.is_error:
            raise ValueError("is_empty hanya bisa dipanggil jika tidak ada error (pgcode == '00000')")
        return len(self.result) == 0

    @property
    def first(self) -> dict:
        '''
            Ambil result index ke-0 (dict)
        '''
        if self.is_error:
            raise ValueError("first hanya bisa dipanggil jika tidak ada error (pgcode == '00000')")
        return self.result[0] if len(self.result) > 0 else {}

    @property
    def sqlclient_unable_to_establish_sqlconnection(self) -> bool:
        '''
            Bernilai True jika pgcode == '08001', yaitu:
                - Data user / password / port / host / database salah.
                - Server DB / VPN mati.
                - Connection Timeout, dll.
        '''
        return self.pgcode == '08001'
    
    @property
    def unique_violation(self) -> bool:
        '''
            Bernilai True jika error disebabkan karena melanggar unique constraint (pgcode == '23505')
        '''
        return self.pgcode == '23505'
    
    @property
    def foreign_key_violation(self) -> bool:
        '''
            Bernilai True jika error disebabkan karena melanggar foreign_key constraint (pgcode == '23503')
        '''
        return self.pgcode == '23503'
    
    @property
    def raise_exception(self) -> bool:
        '''
            Bernilai True jika error disebabkan karena ada 'RAISE EXCEPTION' pada PL/pgSQL (pgcode == 'P0001').
            Untuk ambil pesan error-nya pakai property diag.message_primary
        '''
        return self.pgcode == 'P0001'

    def __str__(self) -> str:
        return f"<pgcode={self.pgcode}, pgerror={self.pgerror}, result={self.result}>"
    
    def __repr__(self) -> str:
        return self.__str__()

    def to_string(self) -> str:
        return self.__str__()

    def to_dict(self) -> dict:
        '''
            Convert pgcode, pgerror, and result into dict
        '''
        return {
            'pgcode': self.pgcode,
            'pgerror': self.pgerror,
            'result': self.result
        }

class PostgresDatabase:
    @property
    def notices(self) -> bool:
        return self.__notices

    @notices.setter
    def notices(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValueError("Setting notices hanya boleh bool (True / False)!")
        self.__notices = value

    def __init__(self, connection_key: str = "default") -> None:
        self.__notices = False
        self.__connection_key = connection_key
        self.__preserveConn = None

    def __establish_connection(self) -> DBResponse:
        # TODO: buat logic jika gunicorn kirim signal 'SIGABRT' maka tetap lanjutkan return 'ec' (untuk menghindari 'ec' UnboundLocalError)
        self.__connection_pool = self.__connection = self.__cursor = None
        try:
            if global_connection_pool is None:
                raise global_conn_exc

            # ambil koneksi yang dipilih lewat connection_key, jika tidak ada maka isi dgn None
            self.__connection_pool = global_connection_pool.get(
                self.__connection_key, None
            )

            if self.__connection_pool is not None:
                # jika koneksi yang diminta ada, lanjutkan proses
                self.__connection = self.__connection_pool.getconn()
                self.__cursor = self.__connection.cursor()

                return self.__response('00000', None)
            else:
                raise KeyError(
                    f"connection_key: {self.__connection_key} tidak ada!. Berikut key yg ada: {global_connection_pool.keys()}"
                )
        except psycopg2.pool.PoolError as e:
            '''
                Jika terjadi PoolError, artinya:
                    - connection pool abis (naikan nilai maxconn!)
                    - ada koneksi yg menggantung (lupa commit / release ketika pakai method dgn suffix _preserve)
                Sehingga return 08003 - connection_does_not_exist
            '''
            e = self.__serialize_exception(e)
            self.__logprint_exception(e, dept_level=4)

            return self.__response('08003', e.pgerror)
        except psycopg2.OperationalError as e:
            '''
                Jika terjadi OperationalError, artinya:
                    - Data user / password / port / host / database salah.
                    - Server DB / VPN mati.
                    - Connection Timeout, dll.
                Sehingga return 08001 - sqlclient_unable_to_establish_sqlconnection 
            '''

            '''
                Timing terjadinya OperationalError ada 2:
                    1. Ketika aplikasi PERTAMAKALI dijalankan (ambil dari global_conn_exc)
                    2. Ketika aplikasi SUDAH berjalan (ambil dari current exception obj)
            '''
            selected_exception = e if global_conn_exc is None else global_conn_exc
            e = self.__serialize_exception(selected_exception)

            self.__logprint_exception(e, dept_level=4)

            return self.__response('08001', e.pgerror)
        except Exception as e:
            '''
                Untuk exception lain, return 08000 - connection_exception
            '''
            e = self.__serialize_exception(e)
            self.__logprint_exception(e, dept_level=4)

            return self.__response('08000', e.pgerror)

    def __release_connection(self) -> None:
        try:
            self.__cursor.close()
            self.__connection_pool.putconn(self.__connection)
        except Exception:
            warnings.warn(f"Gagal ketika hendak release connection!", Warning)
    
    def __generate_preserve_conn(self) -> Tuple[bool, DBResponse]:
        '''
            Establish a connection that will be preserved so it can be used again.
            The connection will be closed only when we call the commit_connection(), rollback_connection() or release_connection() method.

            Returns Tuple: status: bool(True if success), DBResponse obj (if status is True)
        '''
        if self.__preserveConn is None:
            ec = self.__establish_connection()
            if ec.is_error:
                return False, ec
            self.__preserveConn = self.__connection
        else:
            self.__connection = self.__preserveConn
            self.__cursor = self.__connection.cursor()

        return True, None

    def __response(self, pgcode:str, pgerror:str, diag:Diagnostics=VOID_DIAG) -> DBResponse:
        res = DBResponse(pgcode, pgerror, diag, self.__get_result_set())
        if self.__notices:
            res.notices = self.__get_notices()

        return res

    def __get_caller(self, dept_level:int) -> Dict:
        '''
            dept_level: inspect dept level
                - 2: current_frame (postgresKonektor.py)
                - 3: postgresKonektor.py caller (biasanya file DAO)
        '''

        caller_frame = inspect.currentframe()
        for i in range(dept_level):
            caller_frame = caller_frame.f_back

        caller_name = caller_frame.f_code.co_name
        caller_filename = caller_frame.f_code.co_filename
        caller_lineno = caller_frame.f_lineno
        caller_info = f'File "{caller_filename}", line {caller_lineno}, in {caller_name}'

        return {
            'name': caller_name,
            'filename': caller_filename,
            'lineno': caller_lineno,
            'info': caller_info
        }

    def __get_query_aktual(self) -> str:
        '''
            Untuk generate query aktual yg dikirm ke server
            :param print_query: Jika True maka pakan print ke console, jika False maka tidak akan print ke console
            return: query_aktual (str)
        '''
        try:
            query_aktual = self.__cursor.query if self.__cursor is not None else b'NULL'
            if isinstance(query_aktual, bytes):
                query_aktual = query_aktual.decode("utf-8")
                query_aktual = dedent(query_aktual)

                # format & parse query
                query_aktual = sqlparse.format(
                    sql=query_aktual,
                    keyword_case="upper",
                    identifier_case="lower",
                    indent_width=4,
                    reindent=True,
                    encoding="utf-8",
                    use_space_around_operators=True,
                ).strip()
            else:
                # TODO: compare & tampilkan key (bind_param) yg dikirm dan yg dibutuhkan agar programmer tau kurang / salah apa.
                query_aktual = "Gagal build Query Aktual. Coba cek bind param-nya udah cocok dan sesuai belum sama yang di query?"
        except Exception:
            traceback.print_exc()

            self.__release_connection()
            query_aktual = "NULL"

        return query_aktual

    def __print_query_aktual(self) -> None:
        query_aktual = self.__get_query_aktual()
        # construct message info
        time = datetime.now().strftime("[%d-%m-%Y %H:%M:%S]")
        caller = self.__get_caller(3)
        info_header = f"{time} [QUERY]:\n{caller['info']}:\n"

        print(info_header + query_aktual)

    def __get_notices(self) -> List[str]:
        """
        Retrieves the notices generated during a query or PL/pgSQL execution.

        In SQL queries or PL/pgSQL, it is common to use syntax like "RAISE NOTICE ..." or "RAISE WARNING ...".
        Sometimes, there is a need to capture and retrieve these output messages.
        This function is designed to handle such situations and retrieve the generated notices.

        Returns:
            List[str]: A list containing the notices generated during the query or PL/pgSQL execution.
                    Each notice is represented as a string in the list.
        """
        if not self.__connection or self.__connection.notices is None:
            return []

        # bersihkan data: ['NOTICE:  notice_message\n', 'WARNING:  warning_message\n'] -> ['notice_message', 'warning_message']
        return [
            n.split(': ')[-1].strip()
            for n
            in self.__connection.notices
        ]

    def __get_result_set(self) -> List[Dict]:
        # jika desc kosong atau cursor sudah ditutup maka return list kosong
        if not self.__cursor or self.__cursor.description is None:
            return []

        '''
            cursor.description berisi meta-data table dalam bentuk tuple, index ke-0 adalah nama kolom,
            sehingga kita loop index-0. Contoh isi dari columns -> ('NIM', 'NAMA')
            kita zip record dgn columns dan masukan dalam list result_set.
            contoh isi dari record -> ('672018259', 'CANDRA WIJAYANTO')
            contoh ouput dict(zip(columns, record)) -> {'NIM': '672018259', 'NAMA': 'CANDRA WIJAYANTO'}
        '''
        columns = [i[0] for i in self.__cursor.description]
        return [dict(zip(columns, record)) for record in self.__cursor]

    def __serialize_exception(self, e: Exception) -> PsycopgError:
        '''
        Serialize an Exception to ensure that all exceptions have properties 'pgerror', 'pgcode', 'diag' similar to psycopg2.Errors.

        :param e: The Exception object to serialize.
        '''

        if not isinstance(e, Exception):
            e = PsycopgError(
                pgcode="",
                pgerror="Error pada eksekusi DB",
            )
        elif isinstance(e, psycopg2.Error):
            if None in {e.pgcode, e.pgerror}:
                e = PsycopgError(
                    pgcode="",
                    pgerror=f"{type(e).__name__}: {e.__str__()}",
                )
            else:
                e = PsycopgError(e.pgcode, e.pgerror, e.diag)
        elif not isinstance(e, psycopg2.Error):
            e = PsycopgError(
                pgcode="",
                pgerror=f"{type(e).__name__}: {e.__str__()}"
            )

        return e

    def __handleTypeErrorException(self, query) -> DBResponse:
        """
        Handles "TypeError: dict is not a sequence" that occurs when using '%' in a Python query string,
        in order to include a literal % in the query you can use the %% string
        https://www.psycopg.org/docs/usage.html#passing-parameters-to-sql-queries

        :param query: The Python query string containing '%' characters.
        """
        traceback.print_exc()
        if "%" in query:
            pgerror = "01000 - Warning: Apakah pada query anda ada single '%'?, jika iya coba ubah jadi double '%%'"
            print(pgerror)
            return self.__response('01000', pgerror)
        else:
            raise Exception("58000 - system_error: Waduh, ada error baru yang belum pernah ditemui, semangat!")

    def __logprint_exception(self, e:PsycopgError, dept_level:int = 3) -> None:
        """
        Log the Exception and print it to the console for better readability.

        :param e:  The Exception object to log and print.
        """
        caller = self.__get_caller(dept_level)
        time = datetime.now().strftime("[%d-%m-%Y %H:%M:%S]")
        error_time = f"{time} [ERROR]:"

        query_aktual = self.__get_query_aktual()

        print(f"{error_time}\n{caller['info']}\n{e.pgerror}QUERY:\n{query_aktual}")

    def execute(self, query: str, param: dict = {}, print_query: bool = False) -> DBResponse:
        param = {} or param
        try:
            ec = self.__establish_connection()
            if ec.is_error:
                return ec

            self.__cursor.execute(query, param)
            self.__connection.commit()

            if print_query:
                self.__print_query_aktual()

            return self.__response('00000', None)
        except TypeError:
            return self.__handleTypeErrorException(query)
        except Exception as e:
            e = self.__serialize_exception(e)
            self.__logprint_exception(e)

            return self.__response(e.pgcode, e.pgerror, e.diag)
        finally:
            if ec.status:
                self.__release_connection()

    def execute_dt(self, query: str, param: dict = {}, limit: int = 10, print_query: bool = False) -> DBResponse:
        """
        Digunakan untuk get data DataTable yang secara "server side",
        karena secara "server side" maka baiknya ada pagination, sehingga wajib ada limit & offset
        NOTE: Pagination baiknya tidak menggunakan offset: https://use-the-index-luke.com/no-offset, namun
        implement pagination using 'seek method or keyset' https://use-the-index-luke.com/sql/partial-results/fetch-next-page
        """
        param = {} or param
        try:
            ec = self.__establish_connection()
            if ec.is_error:
                return ec

            # validasi bind param wajib memiliki attribut 'offset'
            if not "offset" in param:
                pesan = f"'bind param' wajib menyertakan 'offset'"
                print("ERROR - 22010:", pesan)
                hasil_error = self.__response("22010", pesan)
                # khusus dataTable ada tambahan 'total'
                hasil_error.dt_total = 0
                return hasil_error

            # netralisasi parameter 'query' & build query_count
            query = query.replace("limit", "LIMIT").replace(";", "")
            splitQuery = query.split("LIMIT")[0].strip()
            query_count = f"SELECT COUNT(*) AS total FROM ({splitQuery}) AS total;"

            # Karena DT server side maka baiknya (wajib sih) ada limit & offset
            if query.find("LIMIT") < 0:
                query = f"{query} LIMIT {limit} OFFSET %(offset)s;"

            # select data untuk atribut "data" atau "aaData" pada DataTable
            self.__cursor.execute(query, param)

            if print_query:
                self.__print_query_aktual()
            
            # tampung hasil select
            hasil = self.__response('00000', None)

            # select count untuk atribut "recordsFiltered" atau "iTotalRecords" atau "iTotalDisplayRecords" pada DataTable
            self.__cursor.execute(query_count, param)
            result_count = self.__get_result_set()
            result_count = result_count[0]["total"]

            # khusus untuk execute_dt ada tambahan prop dt_total
            hasil.dt_total = result_count

            return hasil
        except TypeError:
            return self.__handleTypeErrorException(query)
        except Exception as e:
            e = self.__serialize_exception(e)
            self.__logprint_exception(e)

            return self.__response(e.pgcode, e.pgerror, e.diag)
        finally:
            if ec.status:
                self.__release_connection()

    def execute_many(self, query: str, listData: list, print_query: bool = False) -> DBResponse:
        """
        Method ini digunakan untuk execute query dgn multiple values/parameter
        https://www.psycopg.org/docs/cursor.html#cursor.executemany
        example::

            def insert_data(listData):
                db = PostgresDatabase()
                listData = [('candra', 'pisang'), ('wijayanto', 'melon')]
                query = 'INSERT INTO its_ms_user (nama, buah_favorit) VALUES %s'
                return db.execute_many(query, listData)
        """
        listData = [] or listData
        try:
            ec = self.__establish_connection()
            if ec.is_error:
                return ec

            execute_values(
                self.__cursor, query, listData, template=None, page_size=1000
            )
            self.__connection.commit()

            if print_query:
                self.__print_query_aktual()

            return self.__response("00000", None)
        except TypeError:
            return self.__handleTypeErrorException(query)
        except ValueError as e:
            print("Error di execute_many:", e)
            print("Hint: execute_many pakai %s untuk param-nya: 'INSERT INTO table_x VALUES %s;")
            return self.__response('58000', e)
        except Exception as e:
            self.__connection.rollback()
            e = self.__serialize_exception(e)
            self.__logprint_exception(e)

            e = self.__serialize_exception(e)
            return self.__response(e.pgcode, e.pgerror, e.diag)
        finally:
            if ec.status:
                self.__release_connection()

    def execute_preserve(self, query: str, param: dict = {}, print_query: bool = False) -> DBResponse:
        '''
        NOTE:
            - khusus untuk method execute_preserve & execute_many_preserve WAJIB commit() diakhir,
            - juga WAJIB pakai try finally. example::

            def simpan_user(nik, nama):
                try:
                    db = PostgresDatabase()
                    query = 'INSERT INTO ms_user VALUES (%(nik)s, %(nama)s);'
                    param = {'nik': nik, 'nama': nama}
                    hasil = db.execute_preserve(query, param)
                    if hasil.is_error:
                        return hasil
                    return hasil.commit()
                finally:
                    db.release_connection()
        '''
        param = {} or param
        try:
            status, ec = self.__generate_preserve_conn()
            if not status:
                return ec

            self.__cursor.execute(query, param)

            if print_query:
                self.__print_query_aktual()

            return self.__response("00000", None)
        except TypeError:
            self.__release_connection()
            return self.__handleTypeErrorException(query)
        except Exception as e:
            e = self.__serialize_exception(e)
            self.__logprint_exception(e)

            self.__release_connection()
            return self.__response(e.pgcode, e.pgerror, e.diag)

    def execute_many_preserve(self, query, listData, print_query: bool = False) -> DBResponse:
        '''
        NOTE:
            - khusus untuk method execute_preserve & execute_many_preserve WAJIB commit() diakhir,
            - juga WAJIB pakai try finally release_connection(). example::

            def simpan_user(list_data_user):
                try:
                    db = PostgresDatabase()
                    query = 'INSERT INTO ms_user VALUES %s;'
                    hasil = db.execute_many_preserve(query, list_data_user)
                    if hasil.is_error:
                        return hasil
                    return hasil.commit()
                finally:
                    db.release_connection()
        '''
        listData = [] or listData
        try:
            status, ec  = self.__generate_preserve_conn()
            if not status:
                return ec

            execute_values(
                self.__cursor, query, listData, template=None, page_size=1000
            )

            if print_query:
                self.__print_query_aktual()

            return self.__response("00000", None)
        except TypeError:
            self.__release_connection()
            return self.__handleTypeErrorException(query)
        except ValueError as e:
            print("Error di execute_many:", e)
            print("Hint: execute_many pakai %s untuk param-nya: 'INSERT INTO table_x VALUES %s;")
            self.__release_connection()
            return self.__response('58000', e)
        except Exception as e:
            e = self.__serialize_exception(e)
            self.__logprint_exception(e)

            self.__release_connection()
            return self.__response(e.pgcode, e.pgerror, e.diag)

    def commit(self) -> DBResponse:
        try:
            if self.__preserveConn is None:
                raise Exception("Tidak ada koneksi yang disimpan!")

            self.__connection = self.__preserveConn
            self.__connection.commit()

            return self.__response('00000', None)
        except Exception as e:
            e = self.__serialize_exception(e)
            self.__logprint_exception(e)

            return self.__response(e.pgcode, e.pgerror, e.diag)
        finally:
            # setelah commit conn maka conn sudah tidak diperlukan, sehingga kita close / release
            self.__preserveConn = None
            self.__release_connection()

    def rollback(self) -> None:
        '''
            Dipakai ketika hendak rollback connection setelah memanggil atau pakai method execute_no_commit() / execute_many_no_commit()
        '''
        try:
            if self.__preserveConn is None:
                raise Exception("Tidak ada koneksi yang disimpan!")
            
            self.__connection = self.__preserveConn
            self.__connection.rollback()
        except Exception as e:
            e = self.__serialize_exception(e)
            self.__logprint_exception(e)
        finally:
            self.__preserveConn = None
            self.__release_connection()
    
    def release_connection(self) -> None:
        '''
            WAJIB dipakai pada try finally ketika pakai method dgn suffix '_preserve'. example::

                def simpan_user(nik, nama):
                    try:
                        db = PostgresDatabase()
                        query = 'INSERT INTO ms_user VALUES (%(nik)s, %(nama)s);'
                        param = {'nik': nik, 'nama': nama}
                        hasil = db.execute_preserve(query, param)
                        if hasil.is_error:
                            return hasil
                        return hasil.commit()
                    finally:
                        db.release_connection()
        '''
        try:
            self.__connection = self.__preserveConn
            self.__connection_pool.putconn(self.__connection)
        except Exception:
            pass
        finally:
            self.__preserveConn = None

    def get_conn_pool(self) -> Union[ThreadedConnectionPool, None]:
        # NOTE: beta - belum pernah di test, harusnya error wkwk;
        '''
        Method ini mungkin dibutuhkan ketika menemukan "special case" yang tidak bisa di-solve oleh regular method yang disediakan.
        NOTE: jika pakai method ini, wajib tutup / release connection dan cursor secara manual!
        '''
        ec = self.__establish_connection()
        if not ec.status:
            return None

        return self.__connection_pool