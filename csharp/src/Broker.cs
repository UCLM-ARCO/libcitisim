
using System;
using System.Collections.Generic;
using Ice;
using IceStorm;
using Newtonsoft.Json;
using PropertyService;
using SmartObject;

using Metadata = System.Collections.Generic.Dictionary<SmartObject.MetadataField, string>;
using StringDict = System.Collections.Generic.Dictionary<string, string>;

namespace LibCitisim {

    internal class Constants {
        internal static readonly string PROP_WIRING_SERVER_PROXY =
            "Welcome.Proxy";
        internal static readonly string PROP_TOPIC_MANAGER_PROXY =
            "TopicManager.Proxy";
        internal static readonly string PROP_PROPERTY_SERVER_PROXY =
            "PropertyService.Proxy";
        internal static readonly string PROP_WELCOME_SERVER_PROXY =
            "WiringServer.Proxy";

        internal static readonly Dictionary<string, string> defaultConfig =
            new Dictionary<string, string> {
                {PROP_TOPIC_MANAGER_PROXY, "IceStorm/TopicManager"},
                {PROP_PROPERTY_SERVER_PROXY, "PropertyServer"},
                {PROP_WELCOME_SERVER_PROXY, "WelcomeServer"},
                {PROP_WIRING_SERVER_PROXY, "WiringServer"}
        };
    }

    public class Logger {
        private string name;
        private int level = 6;
        private static Dictionary<string, Logger> instances = new Dictionary<string, Logger>();

        Logger(string name) {
            this.name = name;
        }

        public void SetLevel(string level) {
            this.level = new Dictionary<string, int> {
                {"debug", 10},
                {"info", 8},
                {"warning", 6},
                {"error", 4},
            }[level];
        }

        public static Logger GetLogger(string name) {
            Logger retval;
            if (!instances.TryGetValue(name, out retval)) {
                retval = new Logger(name);
                instances[name] = retval;
            }
            return retval;
        }

        public void Debug(string message) {
            if (level >= 10)
                Console.WriteLine($"[{name}/debug]: {message}");
        }

        public void Info(string message) {
            if (level >= 8)
                Console.WriteLine($"[{name}/info]: {message}");
        }

        public void Error(string message) {
            if (level >= 4)
                Console.WriteLine($"[{name}/ERROR]: {message}");
        }
    }

    public class MetadataUtil {

        private static Dictionary<string, MetadataField> NamedFields =
            new Dictionary<string, MetadataField> {
                {"timestamp",  MetadataField.Timestamp},
                {"quality",    MetadataField.Quality},
                {"expiration", MetadataField.Expiration},
                {"latitude",   MetadataField.Latitude},
                {"longitude",  MetadataField.Longitude},
                {"altitude",   MetadataField.Altitude},
                {"place",      MetadataField.Place},
            };

        public static StringDict FromMetadata(Metadata meta) {
            var fields = new StringDict();
            foreach (var item in meta) {
                string key = item.Key.ToString().ToLower();
                fields[key] = item.Value;
            }
            return fields;
        }

        public static Metadata FromDict(StringDict dict) {
            var meta = new Metadata();
            var args = new StringDict(dict);

            foreach (var item in DataModel.Metadata) {
                string value;
                if (!dict.TryGetValue(item.Key, out value))
                    continue;

                var cast = item.Value;
                cast.check(value);
                meta[NamedFields[item.Key]] = value;
                args.Remove(item.Key);
            }

            if (args.Count > 0) {
                string invalid = "";
                foreach(var a in args)
                    invalid += $"{a.Key},";
                throw new ArgumentException($"invalid meta fields: {invalid}");
            }
            return meta;
        }
    }

    public delegate void ADSubscriber(
        dynamic value, string source, Dictionary<string, string> meta
    );

    internal class EventWithValue {

        private string topicName;
        private ADSubscriber callback;
        private Logger logger;

        public EventWithValue(string topicName, ADSubscriber callback) {
            this.topicName = topicName;
            this.callback = callback;
            logger = Logger.GetLogger("libcitisim");
        }

        public void notify(dynamic value, string source, Metadata meta, Current current=null) {
            try {
                string strmeta = "{";
                foreach (var i in meta)
                    strmeta += $"{i.Key}: '{i.Value}',";
                strmeta += "}";
                logger.Debug(string.Format(
                    "event arrived on '{0}, value: {1}, source: {2}, meta: {3}",
                    topicName, value, source, strmeta
                ));

                var dictmeta = MetadataUtil.FromMetadata(meta);
                callback(value, source, dictmeta);
            }
            catch (ArgumentException e) {
                logger.Error(e.ToString());
                logger.Error("there were some error on provided callback!");
            }
        }
    }

    public class AnalogSinkI : SmartObject.AnalogSinkDisp_ {

        private EventWithValue instance;

        public AnalogSinkI(string topicName, ADSubscriber callback) {
            instance = new EventWithValue(topicName, callback);
        }

        public override void notify(float value, string source, Metadata meta, Current current=null) {
            instance.notify(value, source, meta, current);
        }
    }

    public class DigitalSinkI : SmartObject.DigitalSinkDisp_ {

        private EventWithValue instance;

        public DigitalSinkI(string topicName, ADSubscriber callback) {
            instance = new EventWithValue(topicName, callback);
        }

        public override void notify(bool value, string source, Metadata meta, Current current=null) {
            instance.notify(value, source, meta, current);
        }
    }

    public class ADPublisher {
        private Logger logger = Logger.GetLogger("libcitisim");

        private Broker broker;
        private string topicName;
        private string source;
        private StringDict meta;
        private Type type;
        private dynamic publisher;

        public ADPublisher(Broker broker, string topicName, string source="", StringDict meta=null) {
            if (string.IsNullOrEmpty(source))
                source = Guid.NewGuid().ToString("N").Substring(0, 8);
            if (meta == null)
                meta = new StringDict();

            this.broker = broker;
            this.topicName = topicName;
            this.source = source;
            this.meta = meta;

            if (!DataModel.TopicTypes.TryGetValue(topicName, out type))
                throw new ArgumentException($"Unknown topic name: '{topicName}'");
        }

        public void Publish(dynamic value, string source=null, StringDict meta=null) {
            if (publisher is null)
                RetrievePublisher();
            if (source is null)
                source = this.source;
            if (meta is null)
                meta = this.meta;

            // if there is "timestamp" but explicitly set to None, then
            // remove ts from meta, otherwise (there is no "timestamp" key
            // in meta), set it as now
            if (! meta.ContainsKey("timestamp"))
                meta["timestamp"] = ((DateTimeOffset)DateTime.Now).ToUnixTimeSeconds().ToString();
            else if (meta["timestamp"] is null)
                meta.Remove("timestamp");

            var meta_ = MetadataUtil.FromDict(meta);
            publisher.notify(value, source, meta_);

            string strmeta = "{";
            foreach (var i in meta_)
                strmeta += $"{i.Key}: '{i.Value}',";
            strmeta += "}";
            logger.Debug(
                $"publish event on '{topicName}', value: {value}, source: {source}, meta: {strmeta}"
            );
        }

        private void RetrievePublisher() {
            var topic = broker.GetTopic(topicName);
            var publisher = topic.getPublisher();
            ProxyCasting cast = Broker.ProxyTypes[type];
            this.publisher = cast(publisher);
        }
    }

    public delegate dynamic ProxyCasting(Ice.ObjectPrx value);

    public class Broker {

        private Ice.ObjectAdapter _adapter;
        private IceStorm.TopicManagerPrx _topicManager;
        private PropertyServerPrx _propertyManager;

        private Ice.Communicator ic;
        private Ice.Properties props;
        private bool isBidir;
        private Logger logger;

        private static Dictionary<Type, Type> ServantTypes =
            new Dictionary<Type, Type> {
                {typeof(SmartObject.AnalogSink), typeof(AnalogSinkI)},
                {typeof(SmartObject.DigitalSink), typeof(DigitalSinkI)}
            };

        internal static Dictionary<Type, ProxyCasting> ProxyTypes =
            new Dictionary<Type, ProxyCasting> {
                {typeof(SmartObject.AnalogSink), (prx) => {
                    return SmartObject.AnalogSinkPrxHelper.uncheckedCast(prx);
                }},
                {typeof(SmartObject.DigitalSink), (prx) => {
                    return SmartObject.DigitalSinkPrxHelper.uncheckedCast(prx);
                }},
            };

        public Broker(string config, Ice.Communicator ic=null) :
            this(new string[] {"", "--Ice.Config=" + config}, ic) {
        }

        public Broker(string[] args, Ice.Communicator ic=null) {
            this.ic = ic;
            if (this.ic == null)
                this.ic = Ice.Util.initialize(ref args);

            props = this.ic.getProperties();
            isBidir = props.getProperty("LibCitisim.UseBiDir").Equals("True");
            logger = Logger.GetLogger("libcitisim");

            // enable logging, if specified to do so
            if (GetIceProperty("LibCitisim.Debug", false) == "True") {
                logger.SetLevel("debug");
                logger.Debug("debug mode active");
            }

            SetDefaultProperties();
        }

        ~Broker() {
            if (_adapter != null)
                _adapter.deactivate();
            ic.destroy();
        }

        private string GetIceProperty(string key, bool required=true) {
            string value = props.getProperty(key);
            if (required && string.IsNullOrEmpty(value))
                throw new ArgumentException($"missing configuration property: {key}");
            return value;
        }

        private void SetDefaultProperties() {
            foreach(var i in Constants.defaultConfig) {
                if (String.IsNullOrEmpty(props.getProperty(i.Key))) {
                    logger.Info($"Setting default value for property '{i.Key}' = '{i.Value}'");
                    props.setProperty(i.Key, i.Value);
                }
            }
        }

        public ObjectAdapter adapter {
            get {
                if (_adapter != null)
                    return _adapter;

                string adapterName = "";
                if (isBidir)
                    logger.Info("using bi-dir connections");
                else {
                    adapterName = "Adapter";
                    string endpoints = GetIceProperty("Adapter.Endpoints");
                    logger.Info($"creating adapter with endpoints: '{endpoints}'");
                }

                _adapter = ic.createObjectAdapter(adapterName);
                _adapter.activate();
                return _adapter;
            }
        }

        // FIXME: adapter_add() goes here

        // FIXME: welcome_server property goes here

        // FIXME: wiring_server property goes here

        // FIXME: hello() goes here

        public void Subscribe(string topicName, ADSubscriber callback) {
            Ice.ObjectPrx proxy = GetServantProxy(topicName, callback);
            IceStorm.TopicPrx topic = GetTopic(topicName);

            if (isBidir)
                topic.ice_getConnection().setAdapter(_adapter);
            topic.subscribeAndGetPublisher(null, proxy);
            logger.Info($"topic: {topicName}, subscribed proxy: '{proxy}'");
        }

        public void Publish(string topicName, dynamic value, string source="", StringDict meta=null) {
            var p = new ADPublisher(this, topicName, source, meta);
            p.Publish(value);
        }

        public ADPublisher GetPublisher(string topicName, string source="", StringDict meta=null) {
            return new ADPublisher(this, topicName, source, meta);
        }

        public void WaitForEvents() {
            try {
                ic.waitForShutdown();
            }
            catch (OperationInterruptedException) {
            }
        }

        private Ice.ObjectPrx GetServantProxy(string topicName, ADSubscriber callback) {
            Type type;
            if (!DataModel.TopicTypes.TryGetValue(topicName, out type)) {
                throw new ArgumentException($"unknown topic name: '{topicName}'");
            }

            Ice.Object servant = (Ice.Object)Activator.CreateInstance(
                ServantTypes[type], topicName, callback);
            var proxy = adapter.addWithUUID(servant);
            if (proxy.ice_isTwoway())
                proxy = proxy.ice_oneway();
            return proxy;
        }

        internal TopicPrx GetTopic(string topicName) {
            try {
                return topicManager.retrieve(topicName);
            }
            catch (IceStorm.NoSuchTopic) {
                return topicManager.create(topicName);
            }
        }

        public TopicManagerPrx topicManager {
            get {
                if (_topicManager != null)
                    return _topicManager;

                var strprx = GetIceProperty(Constants.PROP_TOPIC_MANAGER_PROXY);
                var proxy = ic.stringToProxy(strprx);
                _topicManager = IceStorm.TopicManagerPrxHelper.checkedCast(proxy);
                return _topicManager;
            }
        }

        public void SetProperty(string path, dynamic value) {
            value = JsonConvert.SerializeObject(value);
            propertyManager.set(path, value);
        }

        public string GetProperty(string path) {
            return propertyManager.get(path);
        }

        internal PropertyServerPrx propertyManager {
            get {
                if (_propertyManager != null)
                    return _propertyManager;

                dynamic proxy = GetIceProperty(Constants.PROP_PROPERTY_SERVER_PROXY);
                proxy = ic.stringToProxy(proxy);
                _propertyManager = PropertyServerPrxHelper.checkedCast(proxy);
                return _propertyManager;
            }
        }
    }
}