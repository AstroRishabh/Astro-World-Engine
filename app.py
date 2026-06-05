from flask import Flask, request, jsonify
from flask_cors import CORS
from dashaCalculator import calculate_mahadasha
from d4_chart import generate_d4_chart
from d9_chart import generate_d9_chart
import swisseph as swe

app = Flask(__name__)
CORS(app)

# Path to ephemeris files
swe.set_ephe_path('.')

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]
NAKSHATRA_LIST = [
"Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
"Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni",
"Uttara Phalguni","Hasta","Chitra","Swati","Vishakha",
"Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha",
"Shravana","Dhanishta","Shatabhisha","Purva Bhadrapada",
"Uttara Bhadrapada","Revati"
]

NAKSHATRA_LORDS = [
"Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
"Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
"Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"
]
NAKSHATRA_SIZE = 13.333333
def calculate_nakshatra(moon_longitude):

    index = int(moon_longitude / NAKSHATRA_SIZE)

    nakshatra_name = NAKSHATRA_LIST[index]
    
    lord = NAKSHATRA_LORDS[index]

    pada = int(((moon_longitude % NAKSHATRA_SIZE) / (NAKSHATRA_SIZE / 4))) + 1

    return {
        "nakshatra": nakshatra_name,
        "pada": pada,
        "lord":lord
    }

SUN_COMBUST_LIMITS = {
"Mercury":14,
"Venus":10,
"Mars":17,
"Jupiter":11,
"Saturn":15
}

EXALTATION = {
"Sun":"Aries",
"Moon":"Taurus",
"Mars":"Capricorn",
"Mercury":"Virgo",
"Jupiter":"Cancer",
"Venus":"Pisces",
"Saturn":"Libra"
}

DEBILITATION = {
"Sun":"Libra",
"Moon":"Scorpio",
"Mars":"Cancer",
"Mercury":"Pisces",
"Jupiter":"Capricorn",
"Venus":"Virgo",
"Saturn":"Aries"
}
        
@app.route("/")
def home():
    return "Flask Vedic API Running"



@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        data = request.json
        date = data["date"]
        time = data["time"]
        lat = float(data["latitude"])
        lon = float(data["longitude"])

        year, month, day = map(int, date.split("-"))
        hour, minute = map(int, time.split(":"))

        # Timezone Correction (Assuming IST +5.5)
        ut = hour + minute / 60.0 - 5.5
        jd = swe.julday(year, month, day, ut)

        # 1. SET LAHIRI AYANAMSA
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        # 2. CALCULATE LAGNA (ASCENDANT)
        # Using houses_ex with SIDEREAL flag and 'W' for Whole Sign
        cusps, ascmc = swe.houses_ex(jd, lat, lon, b'W', swe.FLG_SIDEREAL)
        lagna_degree = ascmc[0]
        lagna_sign_idx = int(lagna_degree / 30)

        planets_map = {
            "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS,
            "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER,
            "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE
        }

        chart = {str(i): [] for i in range(1, 13)}
        detailed_planets = {}

        for name, pid in planets_map.items():
            # 3. CALCULATE PLANET WITH SIDEREAL FLAG
            res = swe.calc_ut(jd, pid, swe.FLG_SIDEREAL | swe.FLG_SPEED)
            p_deg = res[0][0]
            speed = res[0][3]

            retrograde = speed < 0
            
            p_sign_idx = int(p_deg / 30)
            
            # WHOLE SIGN LOGIC: House = (Sign - Lagna_Sign + 12) % 12 + 1
            p_house = (p_sign_idx - lagna_sign_idx + 12) % 12 + 1

            chart[str(p_house)].append(name)
            detailed_planets[name] = {
                "degree": round(p_deg % 30, 2),
                "longitude": p_deg,
                "sign": ZODIAC_SIGNS[p_sign_idx],
                "house": p_house,
                "retrograde": retrograde
                
            }


        # Ketu Calculation (Opposite to Rahu)
        rahu_sign_idx = int(swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)[0][0] / 30)
        ketu_sign_idx = (rahu_sign_idx + 6) % 12
        ketu_house = (detailed_planets["Rahu"]["house"] + 6 - 1) % 12 + 1
        
        detailed_planets["Ketu"] = {
            "degree": detailed_planets["Rahu"]["degree"],
            "sign": ZODIAC_SIGNS[ketu_sign_idx],
            "house": ketu_house,
            "retrograde":True
        }
        chart[str(ketu_house)].append("Ketu")
        
        
        #Dasha Calculation
        
        moon_longitude = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
        dasha = calculate_mahadasha(moon_longitude, data["date"])
        nakshatra = calculate_nakshatra(moon_longitude)
        
        lagna_sign = ZODIAC_SIGNS[lagna_sign_idx]

        d4_chart = generate_d4_chart(detailed_planets, lagna_sign)
        d9_chart = generate_d9_chart(detailed_planets, lagna_sign)
        
        #Asth Planets Logic
        sun_long = detailed_planets["Sun"]["longitude"]

        for planet,data in detailed_planets.items():

            if planet in SUN_COMBUST_LIMITS:

                diff = abs(data["longitude"] - sun_long)

                if diff > 180:
                    diff = 360 - diff

                data["combust"] = diff < SUN_COMBUST_LIMITS[planet]
                
        #UCH/NEECH
        for planet,data in detailed_planets.items():

            sign = data["sign"]

            data["exalted"] = sign == EXALTATION.get(planet)
            data["debilitated"] = sign == DEBILITATION.get(planet)

        
        return jsonify({
            "lagna": {
            "sign": ZODIAC_SIGNS[lagna_sign_idx],
            "degree": round(lagna_degree % 30, 2)
            },
            "planets": detailed_planets,
            "north_indian_chart": chart,
            "d4_chart": d4_chart,
            "d9_chart": d9_chart,
            "nakshatra": nakshatra,
            "dasha": dasha,
            
        })


    except Exception as e:
        return jsonify({"error": str(e)}), 400
@app.post("/dasha")
def get_dasha(data: dict):
    moon_longitude = data["moonLongitude"]
    date = data["date"]

    dasha = calculate_mahadasha(moon_longitude, date)

    return {
        "dasha": dasha
    }
@app.post("/d4")
def d4_chart(data: dict):

    planets = data["planets"]

    d4 = generate_d4_chart(planets)

    return {"d4_chart": d4}
@app.post("/d9")
def navamsa_chart(data: dict):

    planets = data["planets"]

    d9 = generate_d9_chart(planets)

    return {"d9_chart": d9}


        
if __name__ == "__main__":
    app.run(port=5001, debug=True)