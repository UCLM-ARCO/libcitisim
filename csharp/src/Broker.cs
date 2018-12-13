
using System;
using System.Collections.Generic;
using Ice;
using SmartObject;

using Metadata = System.Collections.Generic.Dictionary<SmartObject.MetadataField, string>;

namespace LibCitisim {

    public class Logger {
        private string _name;

        public Logger(string name) {
            _name = name;
        }

        public void info(string message) {
            Console.WriteLine("[{0}/info]: {1}", _name, message);
        }
    }

  	public delegate void AnalogSubscriber(
        float value, string source, Dictionary<string, string> meta
    );

    public class AnalogSinkI : SmartObject.AnalogSinkDisp_ {

        private string _topicName;
        private AnalogSubscriber _callback;

        public AnalogSinkI(string topicName, AnalogSubscriber callback) {
            _topicName = topicName;
            _callback = callback;
        }

        public override void notify(float value, string source, Metadata meta, Current current = null) {
            throw new NotImplementedException();
        }
    }

    public class Broker {

        private static Dictionary<Type, Type> ServantTypes = new Dictionary<Type, Type> {
            {typeof(SmartObject.AnalogSink), typeof(AnalogSinkI)}
        };

        private Ice.Communicator _ic;
        private Ice.ObjectAdapter _adapter;
        private Ice.Properties _props;
        private bool _isBidir;
        private Logger _logger;

        public Broker(string config, Ice.Communicator ic=null) :
            this(new string[] {"", "--Ice.Config=" + config}, ic) {
        }

        public Broker(string[] args, Ice.Communicator ic=null) {
            _ic = ic;
            if (_ic == null)
                _ic = Ice.Util.initialize(ref args);

            _props = _ic.getProperties();
            _isBidir = _props.getProperty("LibCitisim.UseBiDir").Equals("True");
            _logger = new Logger("libcitisim");
        }

        ~Broker() {
            if (_adapter != null)
                _adapter.deactivate();
            _ic.destroy();
        }

        public ObjectAdapter Adapter {
            get {
                if (_adapter != null)
                    return _adapter;

                string adapterName = "";
                if (_isBidir)
                    _logger.info("using bi-dir connections");
                else {
                    adapterName = "Adapter";
                    string endpoints = _props.getProperty("Adapter.Endpoints");
                    if (String.IsNullOrEmpty(endpoints))
                        throw new ArgumentException(
                            "You must provide the 'Adapter.Endpoints' configuration property.");
                    _logger.info("creating adapter with endpoints: '" + endpoints + "'");
                }

                _adapter = _ic.createObjectAdapter(adapterName);
                _adapter.activate();
                return _adapter;
            }
        }

        public void Subscribe(string topicName, AnalogSubscriber callback) {
            var proxy = _GetServantProxy(topicName, callback);
        }

        private Ice.ObjectPrx _GetServantProxy(string topicName, AnalogSubscriber callback) {
            Type type;
            if (!DataModel.TopicTypes.TryGetValue(topicName, out type)) {
                throw new ArgumentException("Unknown topic name: '" + topicName + "'");
            }

            Ice.Object servant = (Ice.Object)Activator.CreateInstance(
                ServantTypes[type], topicName, callback);
            var proxy = Adapter.addWithUUID(servant);
            if (proxy.ice_isTwoway())
                proxy = proxy.ice_oneway();
            return proxy;
        }
    }
}