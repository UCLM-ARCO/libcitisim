using System;
using System.Collections.Generic;

using StringDict = System.Collections.Generic.Dictionary<string, string>;
using Metadata = System.Collections.Generic.Dictionary<SmartObject.MetadataField, string>;

namespace LibCitisim {

    public class AnalogEventsMixin : EventsFixture {

        // FIXME: this list will eventually get deprecated!
        protected List<string> knownTopics = new List<string> {
            "ActivePower",
            "AirPollutants1",
            "AirPollutants2",
            "Anemometer",
            "Battery",
            "CarbonDioxide",
            "CarbonMonoxide",
            "Dioxygen",
            "Energy",
            "HydrocarbonsVOC",
            "Humidity",
            "NitrogenDioxide",
            "Ozone",
            "ParticulateMatter1um",
            "ParticulateMatter2.5um",
            "ParticulateMatter10um",
            "PluviometerCurrent",
            "PluviometerLastDay",
            "PluviometerLastHour",
            "Power",
            "Pressure",
            "SoilMoisture",
            "SoilTemperature",
            "SolarRadiation",
            "StemDiameter",
            "Temperature",
            "Vibration",
            "WindVane"
        };

        protected void PublishEvent(string topicName, string source="", StringDict meta=null) {
            var topic = GetTopic(topicName);
            var prx = topic.getPublisher();
            Metadata meta_ = new Metadata();
            if (meta != null)
                 meta_ = MetadataUtil.FromDict(meta);
            SmartObject.AnalogSinkPrx publisher =
                SmartObject.AnalogSinkPrxHelper.uncheckedCast(prx);
            publisher.notify(123.4f, "Test", meta_);
            Console.WriteLine(">>> event published (using: {0})", publisher);
        }
    }
}