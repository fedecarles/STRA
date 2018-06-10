#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Aplicación de Flask para graficar las series de tiempo de la
api del Ministerio de Hacienda de la República Argentina"""

import time
import json
import urllib.request
import pandas as pd
from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import TextField, SelectField, IntegerField, validators


APP = Flask(__name__)
APP.config['SECRET_KEY'] = 'you-will-never-guess'

SERIES = 'http://infra.datos.gob.ar/catalog/modernizacion/dataset/1/distribution/1.2/download/series-tiempo-metadatos.csv'
BASE_URL = "http://apis.datos.gob.ar/series/api/series?ids="
COLNAMES = ['serie_id', 'serie_descripcion']
SERIES_DATA = pd.read_csv(SERIES, usecols=COLNAMES)
SERIES_DATA.columns = ['value', 'label']
CURRENT_YEAR = int(time.strftime("%Y"))
ALL_YEARS = [""] + sorted(list(range(1900, CURRENT_YEAR+1)), reverse=True)


class SearchForm(FlaskForm):
    """
        Search Form
    """

    autocomp = TextField('autocomp', id='auto_complete')
    start_date = SelectField('start_date', id='start_date',
                             choices=[(str(y), str(y)) for y in ALL_YEARS])
    end_date = SelectField('end_date', id='end_date',
                           choices=[(str(y), str(y)) for y in ALL_YEARS])
    limit = IntegerField('limit', [validators.NumberRange(min=100, max=1000)],
                         default=100)
    representation_mode = SelectField('representation_mode',
                                      id='representation_mode',
                                      choices=[('value', 'valor'),
                                               ('change', 'v(t) - v(t-1)'),
                                               ('percent_change',
                                                '%(t) - %(t-1)'),
                                               ('percent_change_a_year_ago',
                                                '%(año) - %(año-1)')])
    collapse = SelectField('collapse',
                           id='collapse',
                           choices=[('', ''),
                                    ('year', 'anual'),
                                    ('quarter', 'trimestral'),
                                    ('month', 'mensual'),
                                    ('week', 'semanal'),
                                    ('day', 'diaria')])
    collapse_aggregation = SelectField('collapse_aggregation',
                                       id='collapse_aggregation',
                                       choices=[('', ''),
                                                ('avg', 'promedio'),
                                                ('sum', 'suma'),
                                                ('end_of_period',
                                                 'último valor'),
                                                ('min', 'mínimo'),
                                                ('max', 'máximo')])


@APP.route('/', methods=['GET', 'POST'])
def index():

    """
        Index page with chart data.
    """

    form = SearchForm()
    api_data = []

    if form.validate_on_submit():
        s_id = request.form.get("autocomp", "").split(', ')
        l_lim = "&limit=" + request.form.get("limit", "")
        s_date = "&start_date=" + request.form.get("start_date", "")
        e_date = "&end_date=" + request.form.get("end_date", "")
        r_mode = "&representation_mode=" + request.form.get(
            "representation_mode", "")
        c_freq = "&collapse=" + request.form.get("collapse", "")
        agg = request.form.get("collapse_aggregation", "")

        if agg == "":
            c_agg = ""
        else:
            c_agg = ":" + agg

        params = c_agg + s_date + e_date + r_mode + c_freq + l_lim +\
            "&format=json&sort=desc"

        full_url = [BASE_URL + ser + params for ser in s_id if ser != '']

        for url in full_url:
            with urllib.request.urlopen(url) as api_request:
                api_data.append(json.loads(api_request.read().decode()))
                time.sleep(2)

    api_data = json.dumps(api_data)
    series_list = SERIES_DATA.to_json(orient='records')

    return render_template('index.html', form=form, api_data=api_data,
                           series_list=series_list)


if __name__ == '__main__':
    APP.run(debug=True)
