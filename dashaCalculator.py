from datetime import datetime, timedelta

DASHA_SEQUENCE = [
    ("Ketu", 7),
    ("Venus", 20),
    ("Sun", 6),
    ("Moon", 10),
    ("Mars", 7),
    ("Rahu", 18),
    ("Jupiter", 16),
    ("Saturn", 19),
    ("Mercury", 17)
]

NAKSHATRA_SIZE = 13.333333


def years_to_days(years):
    return int(years * 365.25)


def rotate_sequence(start_planet):

    index = [p[0] for p in DASHA_SEQUENCE].index(start_planet)

    return DASHA_SEQUENCE[index:] + DASHA_SEQUENCE[:index]


# -------------------------
# PRATYANTAR DASHA
# -------------------------
def calculate_pratyantar(antar_planet, antar_years, start_date):

    pratyantar_list = []
    current = start_date

    sequence = rotate_sequence(antar_planet)

    for planet, years in sequence:

        praty_years = (antar_years * years) / 120
        days = years_to_days(praty_years)

        end = current + timedelta(days=days)

        pratyantar_list.append({
            "planet": planet,
            "start": current.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d")
        })

        current = end

    return pratyantar_list


# -------------------------
# ANTARDASHA
# -------------------------
def calculate_antardasha(maha_planet, maha_years, start_date):

    antar_list = []
    current = start_date

    sequence = rotate_sequence(maha_planet)

    for planet, years in sequence:

        antar_years = (maha_years * years) / 120
        days = years_to_days(antar_years)

        end = current + timedelta(days=days)

        pratyantar = calculate_pratyantar(
            planet,
            antar_years,
            current
        )

        antar_list.append({
            "planet": planet,
            "start": current.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "pratyantar": pratyantar
        })

        current = end

    return antar_list


# -------------------------
# MAHADASHA
# -------------------------
def calculate_mahadasha(moon_longitude, birth_date):

    birth_date = datetime.strptime(birth_date, "%Y-%m-%d")

    nakshatra_index = int(moon_longitude / NAKSHATRA_SIZE)

    dasha_start_index = nakshatra_index % 9

    nakshatra_start = nakshatra_index * NAKSHATRA_SIZE
    position = moon_longitude - nakshatra_start
    fraction = position / NAKSHATRA_SIZE

    maha_list = []
    current = birth_date

    for i in range(9):

        planet, years = DASHA_SEQUENCE[(dasha_start_index + i) % 9]

        if i == 0:
            years = years * (1 - fraction)

        days = years_to_days(years)

        end = current + timedelta(days=days)

        antar = calculate_antardasha(
            planet,
            years,
            current
        )

        maha_list.append({
            "planet": planet,
            "start": current.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "antar": antar
        })

        current = end

    return maha_list