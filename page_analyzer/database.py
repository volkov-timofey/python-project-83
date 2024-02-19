import psycopg2


class DataBase:
    def __init__(self, DATABASE_URL, name_table):
        try:
            self.conn = psycopg2.connect(DATABASE_URL)
        except ValueError:
            print('Can`t establish connection to database')

        self.name_table = name_table
        self.cursor = self.conn.cursor()

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
            self.cursor.execute(f'SELECT * FROM {self.name_table} LIMIT 0')
            clause_select = ', '.join([
                row[0]
                if row[0] != 'created_at'
                else 'DATE(created_at)'
                for row in self.cursor.description
            ])

        where_request, request_params = self._add_where(clause_where)
        order_request = self._add_order(clause_order)

        request_ = f'SELECT {clause_select}' \
                   f' FROM {self.name_table}' \
                   f'{where_request}{order_request};'
        self.cursor.execute(request_, request_params)

        return self.cursor.fetchall()

    def change_table(self, name_fields, data_fields):
        if len(data_fields) != len(name_fields):
            raise ValueError('different count variables for inser to DB')
        req_values = ', '.join('%s' for i in name_fields)
        name_fields = ', '.join(name for name in name_fields)

        request_ = f'INSERT INTO {self.name_table} ({name_fields})' \
                   f' VALUES ({req_values});'
        self.cursor.execute(request_, data_fields)
        self.conn.commit()

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

        self.cursor.execute(request_)
        return self.cursor.fetchall()
