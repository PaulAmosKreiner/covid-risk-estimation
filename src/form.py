from wtforms import Form, validators
from wtforms.fields.html5 import IntegerField, DecimalField as FloatField


class TheForm(Form):
    test_sensitivity = FloatField(
        label='sensitivity of the covid19 rapid test at hand (in %). 0 if none '
              'available or to be considered.',
        default=0,
        validators=[validators.NumberRange(0, 99.9)]
    )
    two_weeks_incidence_per_100k = IntegerField(
        label='the 2-weeks-incidence per 100.000 in population/community',
        default=360,
        validators=[validators.DataRequired(), validators.NumberRange(1, 2500)],
    )
    nonidentified_cases_per_official_case = FloatField(
        label='how many additional cases are estimated to exist per official '
              'case ("Dunkelziffer")',
        default=3,
        validators=[validators.DataRequired(), validators.NumberRange(0, 50)]
    )
    number_of_potential_spreaders = IntegerField(
        label='how many (non-immune) contacts would be met',
        default=1,
        validators=[validators.DataRequired(), validators.NumberRange(1, 500)]
    )
    IFR = FloatField(
        label='the expected infection fatality ratio for the individual '
              'whose risk is estimated (in %)',
        default=0.7,
        validators=[validators.DataRequired(),
                    validators.NumberRange(0.00001, 45.0)]
    )
    secondary_attack_rate = FloatField(
        label='estimation of the attack rate (how likely is an infection if '
              'an infected person is under the contacts) for the scenario'
              ' in % (sane values: 3-13 % for indoor gatherings of '
              'asymptomatic persons with little or'
              ' no cautionary measures. 1-7% with sufficient air exchange. '
              '17 % for typical households.)',
        default=3.5,
        validators=[validators.DataRequired(), validators.NumberRange(0.1, 25)]
    )
    risk_of_infection_reduced_relative_to_population = FloatField(
        label="factor by which the risk of the contacts in this scenario to be "
              "infected lower than that of the selected base population's "
              "average (0,5 = high level of risky contacts, "
              "1 = typical behaviour, 5 = very little contacts, "
              "KN95/FFP2-use etc)",
        default=1,
        validators=[validators.DataRequired(), validators.NumberRange(0.05, 50)]
    )
    second_level_days = IntegerField(
        label='days the person whose risk is estimated will be around '
              'another person whose second-level-risk is to be estimated. '
              'leave 0 if not interested in second-level estimation. 17 is max',
        default=0,
        validators=[validators.NumberRange(0, 17)]
    )
    second_level_IFR = FloatField(
        label='the expected infection fatality ratio for the second-level '
              'individual whose risk is estimated (in %)',
        default=0.7,
        validators=[validators.NumberRange(0.00001, 35.0)]
    )
    second_level_sar = FloatField(
        label='estimation of the secondary attack rate for the second-level '
              'contact scenario in % (sane values around: 16.5 %)',
        default=17.0,
        validators=[validators.NumberRange(1, 50)]
    )
