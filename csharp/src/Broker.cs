
using System;
using System.Collections.Generic;

namespace LibCitisim {

  	public delegate void AnalogSubscriber(
        float value, string source, Dictionary<string, string> meta
    );

    public class Broker {

        public Broker() {
        }

        public void Subscribe(string topicName, AnalogSubscriber callback) {
            var proxy = _GetServantProxy(topicName, callback);
        }

        private Ice.ObjectPrx _GetServantProxy(string topicName, AnalogSubscriber callback) {
            Type type;
            if (!DataModel.TopicTypes.TryGetValue(topicName, out type)) {
                throw new ArgumentException("Invalid topic name: '" + topicName + "'");
            }
            return null;
        }
    }
}