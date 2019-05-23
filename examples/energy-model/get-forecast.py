#!/usr/bin/python3

from datetime import datetime, timedelta
from libcitisim import Broker

if __name__ == "__main__":
    broker = Broker("libcitisim.config")

    start_date = datetime.now().strftime('%d-%m-%Y')
    end_date = (datetime.now() + timedelta(days=7)).strftime('%d-%m-%Y')

    forecast = broker.energy_model.getEnergyForecast(
        "ITSI", start_date, end_date)
    print("Forecast for next week: {}".format(forecast))

