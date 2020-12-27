import math

import pandas as pd
from flask import Flask, request, render_template, flash

from src.form import TheForm

app = Flask(__name__)


@app.route('/', methods=["POST", "GET"])
def risk_estimator():
    form = TheForm(request.form)
    if request.method == 'POST' and form.validate():

        out_html = open("src/templates/head.html").read()

        test_n_day_before_contagious_sensitivity = {
            1: 0.85,
            2: 0.6,
            3: 0.3,
            4: 0.1
        }

        official_prevalence = form.two_weeks_incidence_per_100k.data / 100000
        prevalence_base = official_prevalence * \
                          form.nonidentified_cases_per_official_case.data
        out_html += "<p>" + "prevalence in population: " + str(round(prevalence_base * 100, 1)) + "%" + "</p>"

        risk_infected = prevalence_base / \
                        form.risk_of_infection_reduced_relative_to_population.data
        n_infected = form.number_of_potential_spreaders.data * risk_infected
        n_contagious = n_infected * \
                       (form.contagious_part_of_infection.data / 100)
        # TODO korrekterweise müsstest du hier die probs anders verrechnen
        risk_contagion = n_contagious * (form.secondary_attack_rate.data / 100)
        risk_death = risk_contagion * (form.IFR.data / 100)

        false_negative_rate = 1 - (form.test_sensitivity.data / 100)
        reduction_through_test = 1 / false_negative_rate

        out_html += "<p>" + "risk that one of the contacts with given risk " \
                    "profile is infected: " + _odds(n_infected) + "</p>"
        out_html += "<p>risk of one being contagious: " + \
                    _odds(n_contagious) + "</p>"

        data = pd.DataFrame({
            "without testing": [
                risk_contagion,
                risk_death
            ]
        }, index=[
            "contagion occurs",
            "covid19-related death occurs"
        ])

        test_part = form.test_sensitivity.data != 0

        if test_part:

            data["after negative test"] = [
                risk_contagion / reduction_through_test,
                risk_death / reduction_through_test
            ]

            calculate_n_days = 15
            calc_day_range = range(1, calculate_n_days)
            for day in calc_day_range:
                try:
                    non_contagious_test_sensitivity = \
                        test_n_day_before_contagious_sensitivity[day]
                except:  # noqa
                    non_contagious_test_sensitivity = 0.0
                if day == 1:
                    data[_day_col_string(day)] = \
                        data["after negative test"] + \
                        (data["without testing"] / 20) * \
                        (1 - non_contagious_test_sensitivity)
                else:
                    data[_day_col_string(day)] = \
                        data[_day_col_string(day - 1)] + \
                        (data["without testing"] / 20) * \
                        (1 - non_contagious_test_sensitivity)

            showing_days = [1, 2, 3, 7, 10, 14]
            removing_days = [day for day in calc_day_range if
                             day not in showing_days]
            data = data.drop(
                columns=[_day_col_string(day) for day in removing_days])

        out_html += "<p>" + "as a general life risk comparison: death risk " \
                    "due to 3000km drive in germany, austria, italy, france" \
                    " is about " + _odds((2 / 1e9) * 3000) + "</p>"
        # https://www.allianz-pro-schiene.de/themen/sicherheit/unfallrisiko-im-vergleich/
        # https://injuryfacts.nsc.org/all-injuries/preventable-death-overview/odds-of-dying/

        if test_part:
            out_html += "<p>risk of contagion and covid-related death for one" \
                        " person in the given contact scenario – without " \
                        "testing and after a negative test with given " \
                        "sensitivity:</p>"
        else:
            out_html += "<p>risk of contagion and covid-related death for one" \
                        " person in the given contact scenario:</p>"

        odds_html = data.applymap(_odds).to_html()
        return out_html + odds_html

    if request.method == "POST" and not form.validate():
        flash("please provide sane values for every field. reload page for "
              "defaults.")

    return render_template('main.html', form=form)


def _round_human(number):
    if pd.isna(number):
        return number
    as_int = max(1, int(number))
    digits = len(str(as_int))
    if digits > 4:
        return _millify(as_int)
    how_many_should_be_nonzero = 1 if digits > 4 else 2
    round_away = digits - how_many_should_be_nonzero
    return str(round(as_int, -round_away))


def _odds(ratio):
    return "1 to " + _round_human(1 / ratio)


millnames = ['', 'k', 'm', 'b', 't']


def _millify(n):
    n = float(n)
    millidx = max(0, min(len(millnames) - 1,
                         int(math.floor(
                             0 if n == 0 else math.log10(abs(n)) / 3))))
    return '{:.0f}{}'.format(n / 10 ** (3 * millidx), millnames[millidx])


def _day_col_string(day):
    day_or_days = "day" if day == 1 else "days"
    return str(day) + " " + day_or_days + " after"

app.secret_key = "11da5693c179bef62dcb13c9edab32f5c4f2aa765e523a2b"
