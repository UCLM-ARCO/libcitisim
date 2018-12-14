using System;

using StringDict = System.Collections.Generic.Dictionary<string, string>;
using Metadata = System.Collections.Generic.Dictionary<SmartObject.MetadataField, string>;
using System.Collections.Generic;

namespace LibCitisim {

    public class EventsFixture : IDisposable {
        protected Ice.Communicator ic;
        protected Broker broker;
        private string pwd = Environment.GetEnvironmentVariable("TEST_DIR");
        private string config;

        public EventsFixture() {
            config = pwd + "/tests.config";

            // for testing purposes only
            List<string> args = new List<string> () {"", "--Ice.Config=" + config};
            string[] args_ = args.ToArray();
            ic = Ice.Util.initialize(ref args_);

            // the real subject under testing
            broker = new Broker(config);
        }

        public void Dispose() {
            ic.shutdown();
            ic.destroy();
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
    }

    public class AnalogEventsMixin : EventsFixture {

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