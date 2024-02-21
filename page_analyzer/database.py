import psycopg2


class DataBase:
    def __init__(self, DATABASE_URL, name_table):

        self.name_table = name_table
        self.database_url = DATABASE_URL
        self._init_tables

        try:
            conn = psycopg2.connect(self.database_url)
            with conn.cursor() as cursor:
                cursor.execute(f'SELECT * FROM {self.name_table} LIMIT 0')
                self.select_all = ', '.join([
                    row[0]
                    if row[0] != 'created_at'
                    else 'DATE(created_at)'
                    for row in cursor.description
                ])

        except ValueError:
            print('Can`t establish connection to database')

        finally:
            conn.close()

    def _init_tables(self):
        request_ = None
        if self.name_table == 'urls':
            request_ = '''
                CREATE TABLE urls (
                    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                    name varchar(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        if self.name_table == 'url_checks':
            request_ = '''
                CREATE TABLE url_checks (
                    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                    url_id bigint ,
                    status_code bigint,
                    h1 varchar(255),
                    title varchar(255),
                    description varchar(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
        try:
            conn = psycopg2.connect(self.database_url)
            with conn.cursor() as cursor:
                cursor.execute('DROP TABLE IF EXISTS urls, url_checks')
                conn.commit()
                if request_:
                    cursor.execute(request_)

        except ValueError:
            print('Can`t establish connection to database')

        finally:
            conn.commit()
            conn.close()

    def _add_where(self, clause_where):
        name_field, value = clause_where
        if name_field:
            where_request = f' WHERE {name_field}=(%s)'
            value = (value, )
            return (where_request, value)

        return ('', None)

    def _add_order(self, name_field: str):
        return f' ORDER BY {name_field} DESC' if name_field else ''

    def get_data_table(
        self,
        clause_select='*',
        clause_where: (str, str) = ('', ''),
        clause_order=None
    ):
        if not isinstance(clause_select, str):
            clause_select = ', '.join(
                [name_field for name_field in clause_select]
            )

        if clause_select == '*':
            clause_select = self.select_all

        where_request, request_params = self._add_where(clause_where)
        order_request = self._add_order(clause_order)

        request_ = f'SELECT {clause_select}' \
                   f' FROM {self.name_table}' \
                   f'{where_request}{order_request};'

        # узкое место
        try:
            conn = psycopg2.connect(self.database_url)
            with conn.cursor() as cursor:
                cursor.execute(request_, request_params)
                result = cursor.fetchall()
        except ValueError:
            print('Can`t establish connection to database')
        finally:
            conn.close()

        return result

    def change_table(self, name_fields, data_fields):
        if len(data_fields) != len(name_fields):
            raise ValueError('different count variables for inser to DB')
        req_values = ', '.join('%s' for i in name_fields)
        name_fields = ', '.join(name for name in name_fields)

        request_ = f'INSERT INTO {self.name_table} ({name_fields})' \
                   f' VALUES ({req_values});'
        # узкое место
        try:
            conn = psycopg2.connect(self.database_url)
            with conn.cursor() as cursor:
                cursor.execute(request_, data_fields)
        except ValueError:
            print('Can`t establish connection to database')

        finally:
            conn.commit()
            conn.close()

    def left_join_urls_and_url_cheks(self):

        request_ = '''
            SELECT urls.id AS id,
                urls.name AS name,
                DATE(max(url_checks.created_at)) AS last_checks,
                url_checks.status_code AS status_code
            FROM urls
            LEFT JOIN url_checks ON urls.id=url_checks.url_id
            GROUP BY urls.id, url_checks.status_code
            ORDER BY urls.id DESC;'''

        # узкое место
        try:
            conn = psycopg2.connect(self.database_url)
            with conn.cursor() as cursor:
                cursor.execute(request_)
                result = cursor.fetchall()
        except ValueError:
            print('Can`t establish connection to database')
        finally:
            conn.close()

        return result
