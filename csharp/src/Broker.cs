
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
        internal static readonly string PROP_WELCOME_SERVER_PROXY =
            "WelcomeServer.Proxy";
        internal static readonly string PROP_TOPIC_MANAGER_PROXY =
            "TopicManager.Proxy";
        internal static readonly string PROP_PROPERTY_SERVER_PROXY =
            "PropertyServer.Proxy";
        internal static readonly string PROP_WIRING_SERVER_PROXY =
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
            lock (instances) {
                Logger retval;
                if (!instances.TryGetValue(name, out retval)) {
                    retval = new Logger(name);
                    instances[name] = retval;
                }
                return retval;
            }
        }

        public void Debug(string message) {
            if (level >= 10)
                Console.WriteLine($"[{name}/debug]: {message}");
        }

        public void Info(string message) {
            if (level >= 8)
                Console.WriteLine($"[{name}/info]: {message}");
        }

        public void Warn(string message) {
            if (level >= 6)
                Console.WriteLine($"[{name}/WARN]: {message}");
        }

        public void Error(string message) {
            if (level >= 4)
                Console.WriteLine($"[{name}/ERROR]: {message}");
        }
    }

    public class MetadataUtil {

        private static Dictionary<string, MetadataField> NamedFields =
            new Dictionary<string, MetadataField> {
                {"timestamp",     MetadataField.Timestamp},
                {"quality",       MetadataField.Quality},
                {"expiration",    MetadataField.Expiration},
                {"latitude",      MetadataField.Latitude},
                {"longitude",     MetadataField.Longitude},
                {"altitude",      MetadataField.Altitude},
                {"place",         MetadataField.Place},
                {"category",      MetadataField.Category},
                {"citizenemail",  MetadataField.CitizenEmail},
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

    public class ObservableMixin : SmartObject.ObservableDisp_ {
        protected Logger logger = Logger.GetLogger("libcitisim");
        protected dynamic observer;
        protected ProxyCasting observerCast;
        protected Broker broker;
        protected string source;

        internal static Dictionary<Type, ProxyCasting> ProxyTypes =
            new Dictionary<Type, ProxyCasting> {
                {typeof(SmartObject.AnalogSink), (prx) => {
                    return SmartObject.AnalogSinkPrxHelper.uncheckedCast(prx);
                }},
                {typeof(SmartObject.DigitalSink), (prx) => {
                    return SmartObject.DigitalSinkPrxHelper.uncheckedCast(prx);
                }},
            };

        public ObservableMixin(Broker broker, string source, string transducerType) {
            source = source.Trim();
            if (String.IsNullOrEmpty(source))
                throw new ArgumentException("Invalid provided source");

            Type type;
            if (!DataModel.TransducerTypes.TryGetValue(transducerType, out type))
                throw new ArgumentException($"Unknown transducer type: {transducerType}");
            observerCast = ProxyTypes[type];

            this.broker = broker;
            this.source = source;
        }

        public override void setObserver(string observer, Ice.Current current) {
            Ice.Communicator ic = current.adapter.getCommunicator();
            dynamic proxy = ic.stringToProxy(observer);
            this.observer = observerCast(proxy);
            logger.Info($"new observer {observer} for {current.id.name}");
        }

        public void Subscribe(Ice.ObjectPrx observer) {
            var propKey = source + " | private-channel";
            var channelName = JsonConvert.DeserializeObject<string>(
                broker.GetProperty(propKey));
            var topic = broker.GetTopic(channelName);
            topic.subscribeAndGetPublisher(null, observer);
            logger.Debug($"subscribe observer to topic '{channelName}'");
        }
    }

    public class ObservablePublisher : ObservableMixin {
        private StringDict meta;

        public ObservablePublisher(Broker broker, string source,
            string transducerType, StringDict meta=null) :
                base(broker, source, transducerType) {

            if (meta == null)
                meta = new StringDict();
            this.meta = meta;
        }

        public void Publish(dynamic value, StringDict meta=null) {
            if (observer == null)
                throw new InvalidOperationException("Publisher not yet configured!");
            if (meta is null)
                meta = this.meta;

           // double is not supported, cast to float
           if (value.GetType() == typeof(double))
               value = (float)value;

            // if there is "timestamp" but explicitly set to None, then
            // remove ts from meta, otherwise (there is no "timestamp" key
            // in meta), set it as now
            if (! meta.ContainsKey("timestamp"))
                meta["timestamp"] = ((DateTimeOffset)DateTime.Now).ToUnixTimeSeconds().ToString();
            else if (meta["timestamp"] is null)
                meta.Remove("timestamp");

            var meta_ = MetadataUtil.FromDict(meta);
            observer.notify(value, source, meta_);

            {
                string strmeta = "{";
                foreach (var i in meta_)
                    strmeta += $"{i.Key}: '{i.Value}',";
                strmeta += "}";
                logger.Debug(
                    $"publish event to '{observer}', value: {value}, " +
                    $"source: {source}, meta: {strmeta}"
                );
            }
        }
    }

    public class ObservableInfosystemPublisher : ObservableMixin {
        public ObservableInfosystemPublisher(Broker broker, string source,
            string transducerType) : base(broker, source, transducerType) {
        }

        public void SayInPlace(string place, string message) {
            if (observer == null)
                throw new InvalidOperationException("Publisher not yet configured!");

            observer.sayInPlace(place, message);

            logger.Debug(
                    $"publish sayInPlace event to '{observer}', place: {place}, " +
                    $"message: {message}"
                );
        }

        public void sayInSpeaker(string speaker, string message) {
            if (observer == null)
                throw new InvalidOperationException("Publisher not yet configured!");

            observer.sayInSpeaker(speaker, message);

            logger.Debug(
                    $"publish sayInSpeaker event to '{observer}', speaker: {speaker}, " +
                    $"message: {message}"
                );
        }
    }

    public delegate dynamic ProxyCasting(Ice.ObjectPrx value);

    public sealed class Broker : IDisposable {

        // these are the cached values of the properties
        private Ice.ObjectAdapter _adapter;
        private IceStorm.TopicManagerPrx _topicManager;
        private PropertyServerPrx _propertyManager;
        private WelcomeServicePrx _welcomeServer;

        private Ice.Communicator ic;
        private Ice.Properties props;
        private bool isBidir;
        private Logger logger;

        private static Dictionary<Type, Type> ServantTypes =
            new Dictionary<Type, Type> {
                {typeof(SmartObject.AnalogSink), typeof(AnalogSinkI)},
                {typeof(SmartObject.DigitalSink), typeof(DigitalSinkI)}
            };

        private static Broker instance;

        public static Broker Initialize(string config, Ice.Communicator ic=null) {
            string[] args = new string[] {"", "--Ice.Config=" + config};
            if (string.IsNullOrEmpty(config)) {
                Logger.GetLogger("libcitisim").Warn($"Config file is not provided!");
            }
            return Initialize(args, ic);
        }

        public static Broker Initialize(string[] args, Ice.Communicator ic=null) {
            if (instance != null)
                throw new InvalidOperationException("Broker already initialized!");
            instance = new Broker(args, ic);
            return instance;
        }

        // use this if you want another instance of the broker
        public static void ForgetInstance() {
            instance = null;
        }

        public static Broker GetBroker() {
            if (instance is null)
                throw new InvalidOperationException("Broker not initialized!");
            return instance;
        }

        private Broker(string[] args, Ice.Communicator ic=null) {
            this.ic = ic;
            if (this.ic is null)
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
            Dispose();
        }

        public void Dispose() {
            if (_adapter != null)
                _adapter.deactivate();
            if (ic != null)
                ic.destroy();
            logger.Debug("broker correctly disposed");
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
                    adapterName = "LibCitisimAdapter";
                    string endpoints = GetIceProperty($"{adapterName}.Endpoints");
                    logger.Info($"creating adapter with endpoints: '{endpoints}'");
                }

                _adapter = ic.createObjectAdapter(adapterName);
                _adapter.activate();
                return _adapter;
            }
        }

        // FIXME: adapter_add() goes here

        public WelcomeServicePrx WelcomeServer {
            get {
                if (_welcomeServer != null)
                    return _welcomeServer;

                dynamic proxy = GetIceProperty(Constants.PROP_WELCOME_SERVER_PROXY);
                proxy = ic.stringToProxy(proxy);
                _welcomeServer = WelcomeServicePrxHelper.checkedCast(proxy);
                return _welcomeServer;
            }
        }

        // FIXME: wiring_server property goes here

        public void hello(string address, string transducerType) {
            if (isBidir) {
                logger.Debug("calling helloBidir() on WelcomeServer");
                WelcomeServer.ice_getConnection().setAdapter(adapter);
                WelcomeServer.helloBidir(address, transducerType);
            }
            else {
                logger.Debug("calling hello() on WelcomeServer");
                WelcomeServer.hello(address, transducerType);
            }
        }

        public void Subscribe(string topicName, ADSubscriber callback) {
            Ice.ObjectPrx proxy = GetServantProxy(topicName, callback);
            SubscribeProxy(topicName, proxy);
        }

        public void SubscribeToPublisher(string source, ADSubscriber callback) {
            try {
                var privateChannelKey = source + " | private-channel";
                string topicName = JsonConvert.DeserializeObject<string>(
                    GetProperty(privateChannelKey));

                var typeKey = source + " | transducer-type";
                string transducerType = JsonConvert.DeserializeObject<string>(
                    GetProperty(typeKey));

                Type type;
                if (!DataModel.TransducerTypes.TryGetValue(transducerType, out type)) {
                    throw new ArgumentException($"unknown transducer type: '{transducerType}'");
                }

                Ice.Object servant = (Ice.Object)Activator.CreateInstance(
                    ServantTypes[type], topicName, callback);
                var proxy = adapter.addWithUUID(servant);

                SubscribeProxy(topicName, proxy);
            }
            catch (System.Exception e) {
                throw new ArgumentException(
                    $"Unknown or invalid publisher: {source}, error: {e}");
            }
        }

        private void SubscribeProxy(string topicName, Ice.ObjectPrx proxy) {
            IceStorm.TopicPrx topic = GetTopic(topicName);

            if (isBidir)
                topic.ice_getConnection().setAdapter(_adapter);
            topic.subscribeAndGetPublisher(null, proxy);
            logger.Info($"topic: {topicName}, subscribed proxy: '{proxy}'");
        }

        public ObservablePublisher GetPublisher(
                string source, string transducerType, StringDict meta=null) {

            logger.Debug($"retrieving publisher for '{source}'...");
            var pub = new ObservablePublisher(this, source, transducerType, meta);
            var pub_prx = adapter.add(pub, Ice.Util.stringToIdentity(source));
            hello(pub_prx.ToString(), transducerType);
            return pub;
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
            return proxy;
        }

        internal TopicPrx GetTopic(string topicName) {
            try {
                return TopicManager.retrieve(topicName);
            }
            catch (IceStorm.NoSuchTopic) {
                return TopicManager.create(topicName);
            }
        }

        public TopicManagerPrx TopicManager {
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
            PropertyManager.set(path, value);
        }

        // Note: do not deserialize here, or provide a method to retrieve a list, a dict...
        public string GetProperty(string path) {
            return PropertyManager.get(path);
        }

        public PropertyServerPrx PropertyManager {
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