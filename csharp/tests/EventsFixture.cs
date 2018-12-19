using System;
using System.Collections.Generic;
using SmartObject;

using Metadata = System.Collections.Generic.Dictionary<SmartObject.MetadataField, string>;

namespace LibCitisim {
    public class EventsFixture : IDisposable {

        protected Ice.Communicator ic;
        protected Broker broker;
        private string pwd = Environment.GetEnvironmentVariable("TEST_DIR");
        private string config;
        private Ice.ObjectAdapter adapter;

        public EventsFixture() {
            config = pwd + "/tests.config";

            // for testing purposes only
            List<string> args = new List<string> () {"", "--Ice.Config=" + config};
            string[] args_ = args.ToArray();
            ic = Ice.Util.initialize(ref args_);

            adapter = ic.createObjectAdapterWithEndpoints("adapter", "tcp -h 127.0.0.1 -p 9999");
            adapter.activate();

            // the real subject under testing
            try {
                broker = Broker.Initialize(config);
            }catch(InvalidOperationException) {
                broker = Broker.GetBroker();
            }
        }

        public void Dispose() {
            ic.shutdown();
            ic.destroy();
            adapter.deactivate();
            Console.WriteLine(">>> disposed test");
        }

        public IceStorm.TopicPrx GetTopic(string name) {
            dynamic manager = ic.propertyToProxy("TopicManager.Proxy");
            manager = IceStorm.TopicManagerPrxHelper.checkedCast(manager);
            try {
                return manager.retrieve(name);
            }
            catch (IceStorm.NoSuchTopic) {
                return manager.create(name);
            }
        }

        public void Subscribe(string topicName, Ice.ObjectPrx proxy) {
            var topic = GetTopic(topicName);
            topic.subscribeAndGetPublisher(null, proxy);
            Console.WriteLine($">>> subscribe to '{topicName}', proxy: '{proxy}");
        }

        public Ice.ObjectPrx AdapterAdd(Ice.Object servant) {
            return adapter.addWithUUID(servant);
        }

        public Predicate<Metadata> CheckMeta(Metadata props) {
            bool _partial(Metadata m) {
                if (props is null || ! props.ContainsKey(MetadataField.Timestamp)) {
                    var ts = DateTimeOffset.FromUnixTimeSeconds(
                        long.Parse(m[MetadataField.Timestamp]));
                    var delta = ((DateTimeOffset)DateTime.Now) - ts;
                    if (delta.TotalSeconds > 2)
                        return false;
                }

                if (props != null) {
                    foreach (var item in props) {
                        if (item.Value is null) {
                            if (m.ContainsKey(item.Key))
                                return false;
                        }
                        else if (m[item.Key] != item.Value)
                            return false;
                    }
                }
                return true;
            }
            return _partial;
        }
    }
}