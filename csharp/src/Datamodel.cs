using System;
using System.Collections.Generic;

namespace LibCitisim {

    public class DataModel {

        public delegate bool Checker(string value);

        public class Cast {
            private Type type;
            private Checker checker;

            public Cast(Type type, int n=1, string desc="", Checker checker=null) {
                this.type = type;
                this.checker = checker;
            }

            public void check(string value) {
                if (!checker(value))
                    throw new ArgumentException($"'{value}' should be of type '{type}'");
            }
        }

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

        public static Dictionary<string, Cast> Metadata = new Dictionary<string, Cast> {
            // 'timestamp':  Cast(int),
            // 'quality':    Cast(int, checker=lambda x: 0 <= x <= 256),
            {"quality", new Cast(typeof(int), checker: (s) => {
                    int v = Int32.Parse(s);
                    return (0 <= v && v <= 256);
                })
            }
            // 'expiration': Cast(int,     desc='validity for the sent value (in seconds)', checker=lambda x: 0 <= x <= 2**15 - 1),
            // 'latitude':   Cast(float),
            // 'longitude':  Cast(float),
            // 'altitude':   Cast(float),
            // 'place':      Cast(str,     desc='Standard placeID'),
        };
    }
}