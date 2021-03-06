from flask import Flask, request
import time
import RPi.GPIO as GPIO
import sqlite3 as sqlite
import json

ip = "192.168.1.251"

dbConnection = sqlite.connect('./config.db')
db = dbConnection.cursor()

GPIO.setmode(GPIO.BOARD)

for pin in db.execute("SELECT valve_pin FROM valves"):
    GPIO.setup(pin[0], GPIO.OUT)
    GPIO.output(pin[0], GPIO.HIGH)

app = Flask(__name__)

def getTimes(shots, type):
    for time in db.execute("SELECT " + type + " FROM timings WHERE shot_number = " + str(shots)):
        return time[0]

def getPinFromDrink(drink):
    for pin in db.execute("SELECT valve_pin FROM valves WHERE valve_drink = " + drink):
        return pin[0]

def getPinFromValve(valve):
    for pin in db.execute("SELECT valve_pin FROM valves WHERE valve_number = " + str(valve)):
        return pin[0]

def pourDrink(alcohol, mixer, shots):
    alcoholTime = getTimes(shots, "alcohol_time")
    mixerTime = getTimes(shots, "mixer_time")
    alcoholPin = getPinFromDrink(alcohol)
    mixerPin = getPinFromDrink(mixer)

    if (alcoholPin != None):
        GPIO.output(alcoholPin, GPIO.LOW)
    GPIO.output(mixerPin, GPIO.LOW)
    time.sleep(alcoholTime)
    if (alcoholPin != None):
        GPIO.output(alcoholPin, GPIO.HIGH)
    time.sleep(mixerTime)
    GPIO.output(mixerPin, GPIO.HIGH)

def updateValveData(valve, valvePin, valveDrink, valveType):
    if (valvePin and valvePin != "''"):
        db.execute("UPDATE valves SET valve_pin = " + valvePin + " WHERE valve_number = " + str(valve))
        dbConnection.commit()
    if (valveDrink and valveDrink != "''"):
        db.execute("UPDATE valves SET valve_drink = " + valveDrink + " WHERE valve_number = " + str(valve))
        dbConnection.commit()
    if (valveType and valveType != "''"):
        db.execute("UPDATE valves SET valve_type = " + valveType + " WHERE valve_number = " + str(valve))
        dbConnection.commit()

def updateTimings(shots, alcoholTime, mixerTime):
    if (alcoholTime):
        db.execute("UPDATE timings SET alcohol_time="+ str(alcoholTime) + " WHERE shot_number = " + str(shots))
        dbConnection.commit()
    if (mixerTime):
        db.execute("UPDATE timings SET mixer_time="+ str(mixerTime) + " WHERE shot_number = " + str(shots))
        dbConnection.commit()

def flushValve(valve):
    flushPin = getPinFromValve(valve)
    GPIO.output(flushPin, GPIO.LOW)
    time.sleep(10)
    GPIO.output(flushPin, GPIO.HIGH)

@app.route("/pour/<shots>", methods=["POST"])
def pour(shots):
    pourDrink(request.args.get('alcohol'), request.args.get('mixer'), shots)
    if ((shots != '0') or (request.args.get('alcohol') != "'None'")):
        return "Your "+shots+" "+request.args.get("alcohol")+" and "+request.args.get("mixer")+" is ready"
    else:
        return "Your "+request.args.get("mixer")+" is ready"


@app.route("/pour/<shots>", methods=["PATCH"])
def updateTime(shots):
    updateTimings(shots, request.args.get('alcoholTime'), request.args.get('mixerTime'))
    return "The update has been made"

@app.route("/drinks", methods=["GET"])
def getDrinks():
    alcoholArr = []
    mixerArr = []
    for drink in db.execute("SELECT valve_drink FROM valves WHERE valve_type = 'alcohol'"):
        alcoholArr.append(drink[0])
    for drink in db.execute("SELECT valve_drink FROM valves WHERE valve_type = 'mixer'"):
        mixerArr.append(drink[0])
    drinksDict = {'alcohol':alcoholArr,'mixer':mixerArr}
    return json.dumps(drinksDict)

@app.route("/<valve>", methods=["PATCH"])
def updateValve(valve):
    updateValveData(valve, request.args.get('valvePin'), request.args.get('valveDrink'), request.args.get('valveType'))
    return "The update has been made"

@app.route("/<valve>", methods=["POST"])
def flush(valve):
    flushValve(valve)
    return "Flushed "+valve

if __name__ == "__main__":
    app.run(host=ip)
