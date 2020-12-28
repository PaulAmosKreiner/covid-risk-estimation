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
        out_html += "<p>DISCLAIMER: This tool is meant to be used with at " \
                    "least basic knowledge of covid 19 / SARS-Cov-2. stay " \
                    "safe and always err on the side of caution. feedback on " \
                    "<a href=" \
                    "https://github.com/PaulAmosKreiner/covid-risk-estimation" \
                    ">github</a></p>"

        test_n_day_before_contagious_sensitivity = {
            1: 0.85,
            2: 0.6,
            3: 0.3,
            4: 0.1
        }

        official_prevalence = form.two_weeks_incidence_per_100k.data / 100000
        prevalence_base = official_prevalence * \
                          (form.nonidentified_cases_per_official_case.data + 1)
        out_html += "<p>" + "prevalence in population: " + str(round(prevalence_base * 100, 1)) + "%" + "</p>"

        risk_infected = prevalence_base / \
                        form.risk_of_infection_reduced_relative_to_population.data

        # assuming ~30 % asymptomatic transmissions in total (~20% who have
        # asymptomatic covid plus the one's that spread pre-symptoms)
        # https://doi.org/10.3138/jammi-2020-0030 (2020)
        # assuming around 10% SAR at most when without symptoms
        # 0.7% found in this metastudy (with very limited data though)
        # https://jamanetwork.com/journals/jamanetworkopen/fullarticle/2774102

        n_infected = form.number_of_potential_spreaders.data * risk_infected

        n_contagious = n_infected # * \
        #               (form.contagious_part_of_infection.data / 100)
        # TODO korrekterweise müsstest du hier die probs anders verrechnen
        risk_contagion = n_contagious * (form.secondary_attack_rate.data / 100)
        risk_death = risk_contagion * (form.IFR.data / 100)

        # second-level risk
        second_level_estimation = form.second_level_days.data != 0
        if second_level_estimation:
            incubation_cum = {
                1: 0.01,
                2: 0.03,
                3: 0.1,
                4: 0.28,
                5: 0.53,
                6: 0.65,
                7: 0.77,
                8: 0.84,
                9: 0.92,
                10: 0.95,
                11: 0.96,
                12: 0.97,
                13: 0.98,
                14: 0.99,
                15: 0.995,
                16: 0.998,
                17: 1.0
            }
            # https://pubmed.ncbi.nlm.nih.gov/32150748/
            infected_on_time = risk_contagion * \
                               incubation_cum[form.second_level_days.data]
            second_level_contagion = infected_on_time * \
                                     (form.second_level_sar.data / 100)
            second_level_death = second_level_contagion * \
                                 (form.second_level_IFR.data / 100)

        false_negative_rate = 1 - (form.test_sensitivity.data / 100)
        reduction_through_test = 1 / false_negative_rate

        out_html += "<p>" + "risk that one of the contacts with given risk " \
                    "profile is infected: " + _odds(n_infected) + "</p>"
        #out_html += "<p>risk of one being contagious: " + \
        #            _odds(n_contagious) + "</p>"

        # sanity check of the SAR
        # assumptions
        asymptomatic_share_transmission = 0.2
        asymptomatic_share_infected = 0.5
        # calc
        infected_per_100k = (
                form.two_weeks_incidence_per_100k.data *
                (form.nonidentified_cases_per_official_case.data + 1)
        )
        daily_transmissions_pop = infected_per_100k / 14
        asymptomatic_daily = daily_transmissions_pop * \
                             asymptomatic_share_transmission
        infected_per_meeting = (form.secondary_attack_rate.data / 100) * \
                               (form.number_of_potential_spreaders.data + 1)
        daily_situations_pop = asymptomatic_daily / infected_per_meeting
        daily_situations_per_asymptomatic = daily_situations_pop / (
                asymptomatic_share_infected * infected_per_100k)
        out_html += "<p>secondary attack rate plausibility check: your " \
                    "scenario would have to happen " + \
                    str(math.floor(daily_situations_per_asymptomatic * 7)) + \
                    " to " + \
                    str(math.ceil(daily_situations_per_asymptomatic * 7)) + \
                    " times per currently asymptomatic infected individual " \
                    "per week if made to explain " + \
                    str(round(asymptomatic_share_transmission * 100)) + "% of" \
                    " the weekly covid transmissions in this population " \
                    "(which is in the right ballpark for asymptomatic " \
                    "transmissions as a share of total transmissions).</p>"

        data = pd.DataFrame({
            "without testing": [
                risk_contagion,
                risk_death
            ]
        }, index=[
            "contagion occurs",
            "covid19-related death occurs"
        ])

        if second_level_estimation:
            data = data.append(pd.DataFrame(
                {"without testing": [second_level_contagion, second_level_death]},
                index=["second-level contagion occurs","second-level death occurs"]
            ))

        test_part = form.test_sensitivity.data != 0

        if test_part:

            data["after negative test"] = data["without testing"] / reduction_through_test

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
                        "sensitivity and listed freshness:</p>"
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
    return "test " + str(day) + " " + day_or_days + " old"


app.secret_key = "11da5693c179bef62dcb13c9edab32f5c4f2aa765e523a2b"
