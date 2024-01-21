from flask import Flask, render_template, request, redirect, flash, get_flashed_messages
import json

# Это callable WSGI-приложение
app = Flask(__name__)


@app.route('/')
def hello_world():
    return 'Hello champion!'