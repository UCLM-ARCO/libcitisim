
using System;
using System.Collections.Generic;
using Ice;
using IceStorm;
using SmartObject;

using Metadata = System.Collections.Generic.Dictionary<SmartObject.MetadataField, string>;
using StringDict = System.Collections.Generic.Dictionary<string, string>;

namespace LibCitisim {

    internal class Constants {
        public const string PROP_TOPIC_MANAGER_PROXY = "TopicManager.Proxy";
    }

    public class Logger {
        private string name;
        private int level = 8;
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

            if (args.Count > 0)
                throw new ArgumentException($"invalid meta: {args}");
            return meta;
        }
    }

    public delegate void AnalogSubscriber(
        float value, string source, Dictionary<string, string> meta
    );

    public class AnalogSinkI : SmartObject.AnalogSinkDisp_ {

        private string topicName;
        private AnalogSubscriber callback;
        private Logger logger;

        public AnalogSinkI(string topicName, AnalogSubscriber callback) {
            this.topicName = topicName;
            this.callback = callback;
            logger = Logger.GetLogger("libcitisim");
        }

        public override void notify(float value, string source, Metadata meta, Current current=null) {
            try {
                var strMeta = MetadataUtil.FromMetadata(meta);
                logger.Debug(string.Format(
                    "event arrived on '{0}, value: {1}, source: {2}, meta: {3}",
                    topicName, value, source, meta
                ));
                callback(value, source, strMeta);
            }
            catch (ArgumentException e) {
                logger.Error(e.ToString());
                logger.Error("there were some error on provided callback!");
            }
        }
    }

    public class Broker {

        private static Dictionary<Type, Type> ServantTypes = new Dictionary<Type, Type> {
            {typeof(SmartObject.AnalogSink), typeof(AnalogSinkI)}
        };

        private Ice.ObjectAdapter _adapter;
        private IceStorm.TopicManagerPrx _topicManager;

        private Ice.Communicator ic;
        private Ice.Properties props;
        private bool isBidir;
        private Logger logger;

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
            logger.SetLevel("debug");
        }

        ~Broker() {
            if (_adapter != null)
                _adapter.deactivate();
            ic.destroy();
        }

        private string GetProperty(string key, bool required=true) {
            string value = props.getProperty(key);
            if (required && string.IsNullOrEmpty(value))
                throw new ArgumentException("missing configuration property: '" + key + "'");
            return value;
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
                    string endpoints = GetProperty("Adapter.Endpoints");
                    logger.Info("creating adapter with endpoints: '" + endpoints + "'");
                }

                _adapter = ic.createObjectAdapter(adapterName);
                _adapter.activate();
                return _adapter;
            }
        }

        public TopicManagerPrx topicManager {
            get {
                if (_topicManager != null)
                    return _topicManager;

                var strprx = GetProperty(Constants.PROP_TOPIC_MANAGER_PROXY);
                var proxy = ic.stringToProxy(strprx);
                _topicManager = IceStorm.TopicManagerPrxHelper.checkedCast(proxy);
                return _topicManager;
            }
        }

        public void Subscribe(string topicName, AnalogSubscriber callback) {
            Ice.ObjectPrx proxy = GetServantProxy(topicName, callback);
            IceStorm.TopicPrx topic = GetTopic(topicName);

            if (isBidir)
                topic.ice_getConnection().setAdapter(_adapter);
            topic.subscribeAndGetPublisher(null, proxy);
            logger.Info(string.Format("topic: {0}, subscribed proxy: '{1}'", topicName, proxy));
        }

        private Ice.ObjectPrx GetServantProxy(string topicName, AnalogSubscriber callback) {
            Type type;
            if (!DataModel.TopicTypes.TryGetValue(topicName, out type)) {
                throw new ArgumentException("unknown topic name: '" + topicName + "'");
            }

            Ice.Object servant = (Ice.Object)Activator.CreateInstance(
                ServantTypes[type], topicName, callback);
            var proxy = adapter.addWithUUID(servant);
            if (proxy.ice_isTwoway())
                proxy = proxy.ice_oneway();
            return proxy;
        }

        private TopicPrx GetTopic(string topicName) {
            try {
                return topicManager.retrieve(topicName);
            }
            catch (IceStorm.NoSuchTopic) {
                return topicManager.create(topicName);
            }
        }
    }
}