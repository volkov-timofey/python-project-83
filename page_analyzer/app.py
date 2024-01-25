from flask import Flask, render_template


app = Flask(__name__)


@app.route("/")
def hello_world():
    return render_template(
        'main_page.html'
    )


@app.route("/urls")
def get_table_site():
    return render_template(
        'table_sites.html'
    )
