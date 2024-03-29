import os

from flask import Flask, render_template, request, flash, \
    redirect, url_for, make_response, get_flashed_messages
from urllib.parse import urlsplit
from dotenv import load_dotenv

from page_analyzer.database import DataBase
from page_analyzer.utils import is_valid_url
from page_analyzer.html_parser import parsing_html


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')


@app.route("/")
def index(current_url=''):

    messages = get_flashed_messages(with_categories=True)

    if request.args.get('current_url'):
        current_url = request.args.get('current_url')

    return render_template('index.html',
                           current_url=current_url,
                           messages=messages)


@app.post("/urls")
def add_url():

    db = DataBase(app.config['DATABASE_URL'])
    url = request.form.get('url')
    name_table = 'urls'

    if not is_valid_url(url):
        flash('Некорректный URL', 'error')
        messages = get_flashed_messages(with_categories=True)
        return make_response(render_template('index.html',
                                             current_url=url,
                                             messages=messages), 422)

    normalized_url = f'{urlsplit(url).scheme}://{urlsplit(url).netloc}'
    clause_where = ('name', normalized_url)
    response = db.get_data_table(name_table, clause_where=clause_where)

    if response:
        flash('Страница уже существует', 'info')
        id, name, date_created = next(iter(response))
        return redirect(url_for('get_table_id',
                                id=id,
                                name=name,
                                date_created=date_created,))

    db.change_table(name_table, ('name', ), (normalized_url, ))
    response = db.get_data_table(name_table, clause_where=clause_where)
    id, name, date_created = next(iter(response))
    flash('Страница успешно добавлена', 'success')
    return redirect(url_for('get_table_id',
                            id=id,
                            name=name,
                            date_created=date_created,))


@app.get("/urls")
def get_urls():

    db = DataBase(app.config['DATABASE_URL'])
    response = db.left_join_urls_and_url_cheks()

    return render_template('urls.html', urls=response)


@app.route("/urls/<int:id>")
def get_table_id(id):
    messages = get_flashed_messages(with_categories=True)

    db = DataBase(app.config['DATABASE_URL'])

    clause_where = ('id', id)
    response = db.get_data_table(name_table='urls', clause_where=clause_where)
    url_information = next(iter(response))

    table_checks = db.get_data_table(name_table='url_checks',
                                     clause_where=('url_id', id),
                                     clause_order='created_at')

    return render_template('urls_id.html',
                           url_information=url_information,
                           table_checks=table_checks,
                           messages=messages)


@app.post("/urls/<int:id>/checks")
def checks_url(id):

    db = DataBase(app.config['DATABASE_URL'])
    clause_where = ('id', id)
    response = db.get_data_table(name_table='urls', clause_where=clause_where)

    id, name, _ = next(iter(response))

    tags_information = parsing_html(name)
    if not tags_information:
        flash('Произошла ошибка при проверке', 'error')
        return redirect(url_for('get_table_id', id=id,))

    tags_information['url_id'] = id
    name_fields = tuple(tag for tag in tags_information)
    values_fields = tuple(value for value in tags_information.values())
    db.change_table('url_checks', name_fields, values_fields)

    flash('Страница успешно проверена', 'success')
    return redirect(url_for('get_table_id', id=id))
