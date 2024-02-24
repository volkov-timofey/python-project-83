import os
import requests

from bs4 import BeautifulSoup
from flask import Flask, render_template, request, flash, redirect, url_for
from urllib.parse import urlsplit
from dotenv import load_dotenv

from page_analyzer.database import DataBase
from page_analyzer.utils import custom_validators_url


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL')

# create_tables(app.config['DATABASE_URL']) , create_tables

urls_table = DataBase(app.config['DATABASE_URL'], 'urls')
url_checks = DataBase(app.config['DATABASE_URL'], 'url_checks')


@app.route("/")
def index(current_url=''):
    if request.args.get('current_url'):
        current_url = request.args.get('current_url')
    return render_template(
        'main_page.html',
        current_url=current_url,
    )


@app.route("/urls", methods=['GET', 'POST'])
def get_urls():
    if request.method == 'POST':
        url = request.form.get('url')

        if not custom_validators_url(url):
            flash('Некорректный URL')
            return redirect(url_for('index', current_url=url))

        normalized_url = f'{urlsplit(url).scheme}://{urlsplit(url).netloc}'
        clause_where = ('name', normalized_url)
        response = urls_table.get_data_table(clause_where=clause_where)

        if response:
            flash('Страница уже существует')
            id, name, date_created = next(iter(response))
            return redirect(url_for('get_table_id',
                                    id=id,
                                    name=name,
                                    date_created=date_created,
                                    )
                            )

        urls_table.change_table(('name', ), (normalized_url, ))
        response = urls_table.get_data_table(clause_where=clause_where)
        id, name, date_created = next(iter(response))
        flash('Страница успешно добавлена')
        return redirect(url_for('get_table_id',
                                id=id,
                                name=name,
                                date_created=date_created,
                                )
                        )

    if request.method == 'GET':
        response = urls_table.left_join_urls_and_url_cheks()
        return render_template(
                'table_sites.html',
                urls=response,
            )


@app.route("/urls/<int:id>")
def get_table_id(id):
    clause_where = ('id', id)
    response = urls_table.get_data_table(clause_where=clause_where)
    url_information = next(iter(response))

    table_checks = url_checks.get_data_table(
            clause_where=('url_id', id),
            clause_order='created_at'
        )
    return render_template(
                'url_page.html',
                url_information=url_information,
                table_checks=table_checks,
            )


@app.route("/urls/<int:id>/checks", methods=['POST'])
def checks_url(id):
    clause_where = ('id', id)
    response = urls_table.get_data_table(clause_where=clause_where)

    id, name, _ = next(iter(response))

    # узкое место
    try:
        r = requests.get(name)
    except OSError:
        flash('Произошла ошибка при проверке')
        return redirect(url_for('get_table_id', id=id,))

    status = r.status_code

    if status not in [200, 302]:
        flash('Произошла ошибка при проверке')
        return redirect(url_for('get_table_id', id=id,))

    soup = BeautifulSoup(r.content, 'html.parser')
    h1 = soup.find("h1").string if soup.find("h1") else ''
    title = soup.find("title").string if soup.find("title") else ''
    description = soup.find(attrs={"name": "description"}).get('content') \
        if soup.find(attrs={"name": "description"}) \
        else ''

    url_checks.change_table(
        ('url_id', 'status_code', 'h1', 'title', 'description'),
        (id, status, h1, title, description)
    )

    flash('Страница успешно проверена')
    return redirect(url_for('get_table_id', id=id))
