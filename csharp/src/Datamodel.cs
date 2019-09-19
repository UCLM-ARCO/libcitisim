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
                if (checker != null && !checker(value))
                    throw new ArgumentException(
                        $"invalid value '{value}' (for type '{type}')");
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

        public static Dictionary<string, Type> TransducerTypes = new Dictionary<string, Type> {
            {"LightSensor", typeof(SmartObject.AnalogSink)},
            {"TemperatureSensor", typeof(SmartObject.AnalogSink)},
            {"HumiditySensor", typeof(SmartObject.AnalogSink)},
            {"PressureSensor", typeof(SmartObject.AnalogSink)},
            {"Anemometer", typeof(SmartObject.AnalogSink)},
            {"Windvane", typeof(SmartObject.AnalogSink)},
            {"Pluviometer", typeof(SmartObject.AnalogSink)},
            {"VibrationSensor", typeof(SmartObject.AnalogSink)},
            {"VoltageSensor", typeof(SmartObject.AnalogSink)},
            {"CurrentSensor", typeof(SmartObject.AnalogSink)},
            {"PowerSensor", typeof(SmartObject.AnalogSink)},
            {"CapacitySensor", typeof(SmartObject.AnalogSink)},
            {"EnergySensor", typeof(SmartObject.AnalogSink)},
            {"ParticulateMatterSensor", typeof(SmartObject.AnalogSink)},
            {"GasSensor", typeof(SmartObject.AnalogSink)},
            {"VolumeSensor", typeof(SmartObject.AnalogSink)},
            {"RadiationSensor", typeof(SmartObject.AnalogSink)},
            {"MotorActuator", typeof(SmartObject.AnalogSink)},
            {"DimmableLightActuator", typeof(SmartObject.AnalogSink)},

            {"TwilightSensor", typeof(SmartObject.DigitalSink)},
            {"DoorSensor", typeof(SmartObject.DigitalSink)},
            {"RelayActuator", typeof(SmartObject.DigitalSink)},
        };

        public static List<string> Units = new List<string> {
            "wats",
            "celsius",
            "kWh",
            "%",
            "ppm",
        };

        public static Dictionary<string, Cast> Properties = new Dictionary<string, Cast> {
            {"units", new Cast(
                typeof(string),
                checker: (s) => Units.Exists(x => s.Equals(x)),
                desc: "units of the readings")
            }

            // "hw-range":           Cast(float, 2, desc="[min, max] allowed sensor values"),
            // "orientation":        Cast(float, 3, desc="[x, y, z]"),
            // "manufacturer":       Cast(str),
            // "deployment-date":    Cast(str,      desc="physical deployment date: 2001-01-01"),  # FXIME: add checker
            // "last-revision-date": Cast(str,      desc="maintenance last revision date: 2001-01-01"),  # FIXME: add checker
            // "sw-version":         Cast(str,      desc="running software version"),
            // "hw-version":         Cast(str,      desc="device hw version"),

            // # TO REMOVE
            // "position":           Cast(float, 3, desc="[longitude, latitude, altitude] (only if fixed)"),  # to geogash service
            // "place":              Cast(str,      desc="place textual identifier"),  # to geogash service

            // # NEW
            // "interface":          Cast(str,      desc="citisim SmartObject interface"),
            // "asset":              Cast(str,      desc="icon or shape name (e: bulb)"),
            // "magnitude":          Cast(str,      desc="physical magnitude", checker=check_enum(MAGNITUDES)),
            // "model":              Cast(str,      desc="device model"),
            // "delta":              Cast(int,      desc="number of seconds between updates"),
            // "common-channel":     Cast(str,      desc="common public topic name where event will be sent"),
            // "observable":         Cast(bool,     desc="True if a publisher implements SmartObject::Observable"),
            // "derive-from":        Cast(str,      desc="Physical sensor identity for a virtual sensor"),

            // "wiring:observers":   Cast(list,     desc="List of observer for an observable (managed by the wiring service")
        };

        public static Dictionary<string, Cast> Metadata = new Dictionary<string, Cast> {
            {"timestamp", new Cast(typeof(int))},
            {"quality", new Cast(
                typeof(int),
                checker: (s) => {
                    int v = Int32.Parse(s);
                    return (0 <= v && v <= 256);
                })
            },
            {"expiration", new Cast(
                typeof(int),
                desc: "validity for the sent value (in seconds)",
                checker: (s) => {
                    int v = Int32.Parse(s);
                    return (0 <= v && v <= Math.Pow(2, 15) - 1);
                })
            },
            {"latitude", new Cast(typeof(float))},
            {"longitude", new Cast(typeof(float))},
            {"altitude", new Cast(typeof(float))},
            {"place", new Cast(typeof(string), desc: "Standard placeID")},
            {"category", new Cast(typeof(string), desc: "Tags or categories")},
            {"citizenemail", new Cast(typeof(string), desc: "TCitizen Report user identifier")},
        };
    }
}