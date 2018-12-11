using System;
using System.Collections.Generic;
using Xunit;

using MetadataDict = System.Collections.Generic.Dictionary<string, string>;

namespace LibCitisim {

    public class EventsMixin {
        private Ice.Communicator ic;
        private string pwd = Environment.GetEnvironmentVariable("TEST_DIR");

        public EventsMixin() {
            List<string> args = new List<string> () {
                "", "--Ice.Config=" + pwd + "/tests.config"
            };

            string[] args_ = args.ToArray();
            ic = Ice.Util.initialize(ref args_);
        }

        protected IceStorm.TopicPrx _GetTopic(string name) {
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

    public class AnalogEventsMixin : EventsMixin {

        protected void _PublishEvent(string topicName, string source="", MetadataDict meta=null) {
            var topic = _GetTopic(topicName);
            var publisher = topic.getPublisher();
            if (meta != null) {

            }
        }
    }

    public class CommonSubscriberTests : AnalogEventsMixin {

        private Broker broker;

        public CommonSubscriberTests() {
            broker = new Broker();
        }

        [Fact]
        public void SubscribeToAnUnknownTopic_IsNotPossible() {
            Assert.Throws<ArgumentException>(() => {
                broker.Subscribe("UnknownTopic", null);
            });
        }

        [Fact]
        public void SubscriberReceivedMetadata_WithStringfiedKeys() {
            bool called = false;
            AnalogSubscriber ProcessEvent = (
                float value, string source, Dictionary<string, string> meta) => {
                    called = true;
            };

            broker.Subscribe("WindVane", ProcessEvent);
            _PublishEvent("WindVane", meta: new MetadataDict(){{"quality", "123"}});
            Assert.True(called);
        }
    }
}