import numpy as np

HIST = False
DAY_BASED = False

WEEKDAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']
WEEKDAYS_DIC = {"Mo": 0, "Tu": 1, "We": 2, "Th": 3, "Fr": 4, "Sa": 5, "Su": 6}
WEEKDAYS_DIC_REV = dict(map(reversed, WEEKDAYS_DIC.items()))
# Converteer de dagen van de week naar numerieke waarden
WEEKDAYS_NUMERIC = np.array([WEEKDAYS_DIC[d] for d in WEEKDAYS])
SORTED_WEEKDAYS = np.array(WEEKDAYS)[WEEKDAYS_NUMERIC.argsort()]