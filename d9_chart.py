ZODIAC_SIGNS = [
"Aries","Taurus","Gemini","Cancer",
"Leo","Virgo","Libra","Scorpio",
"Sagittarius","Capricorn","Aquarius","Pisces"
]

def generate_d9_chart(planets, lagna_sign):

    chart = {str(i): [] for i in range(1,13)}

    lagna_num = ZODIAC_SIGNS.index(lagna_sign)

    for planet,data in planets.items():

        sign = data["sign"]
        degree = data["degree"]

        sign_index = ZODIAC_SIGNS.index(sign)

        navamsa = int(degree / (30/9))

        d9_sign = (sign_index * 9 + navamsa) % 12

        house = (d9_sign - lagna_num + 12) % 12 + 1

        chart[str(house)].append(planet)

    return chart