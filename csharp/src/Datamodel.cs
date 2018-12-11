using System;
using System.Collections.Generic;

namespace LibCitisim {

    public class DataModel {

        public static Dictionary<string, Type> TopicTypes = new Dictionary<string, Type> {
            {"ActivePower", typeof(SmartObject.AnalogSink)},
            {"AirPollutants1", typeof(SmartObject.AnalogSink)},
            {"AirPollutants2", typeof(SmartObject.AnalogSink)},
            {"Anemometer", typeof(SmartObject.AnalogSink)},
            {"Battery", typeof(SmartObject.AnalogSink)},
            {"CarbonDioxide", typeof(SmartObject.AnalogSink)},
            {"CarbonMonoxide", typeof(SmartObject.AnalogSink)},
            {"Dioxygen", typeof(SmartObject.AnalogSink)},
            {"Energy", typeof(SmartObject.AnalogSink)},
            {"HydrocarbonsVOC", typeof(SmartObject.AnalogSink)},
            {"Humidity", typeof(SmartObject.AnalogSink)},
            {"NitrogenDioxide", typeof(SmartObject.AnalogSink)},
            {"Ozone", typeof(SmartObject.AnalogSink)},
            {"ParticulateMatter1um", typeof(SmartObject.AnalogSink)},
            {"ParticulateMatter2.5um", typeof(SmartObject.AnalogSink)},
            {"ParticulateMatter10um", typeof(SmartObject.AnalogSink)},
            {"PluviometerCurrent", typeof(SmartObject.AnalogSink)},
            {"PluviometerLastDay", typeof(SmartObject.AnalogSink)},
            {"PluviometerLastHour", typeof(SmartObject.AnalogSink)},
            {"Power", typeof(SmartObject.AnalogSink)},
            {"Pressure", typeof(SmartObject.AnalogSink)},
            {"SoilMoisture", typeof(SmartObject.AnalogSink)},
            {"SoilTemperature", typeof(SmartObject.AnalogSink)},
            {"SolarRadiation", typeof(SmartObject.AnalogSink)},
            {"StemDiameter", typeof(SmartObject.AnalogSink)},
            {"Temperature", typeof(SmartObject.AnalogSink)},
            {"Vibration", typeof(SmartObject.AnalogSink)},
            {"WindVane", typeof(SmartObject.AnalogSink)},

            {"Unconfigured", typeof(SmartObject.AnalogSink)},

            {"Twilight", typeof(SmartObject.DigitalSink)},
        };
    }
}