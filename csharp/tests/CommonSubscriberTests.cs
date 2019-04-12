using System;
using System.Threading;
using Xunit;

using StringDict = System.Collections.Generic.Dictionary<string, string>;

namespace LibCitisim {

    [Collection("AllServers Collection")]
    public class CommonSubscriberTests : AnalogEventsMixin {

        [Fact]
        public void SubscribeToSpecificPublisher() {
            var publisher = "0011223344556647";
            broker.SetProperty(
                publisher + " | private-channel", publisher + ".private");
            broker.SetProperty(
               publisher + " | transducer-type", "LightSensor");

            EventWaitHandle called = new EventWaitHandle(false, EventResetMode.AutoReset);
            ADSubscriber ProcessEvent = (value, source, meta) => {
                Assert.True(meta.ContainsKey("quality"));
                called.Set();
            };

            broker.SubscribeToPublisher(publisher, ProcessEvent);
            PublishEvent(publisher + ".private", meta: new StringDict(){{"quality", "123"}});
            Assert.True(called.WaitOne(2000));
        }

        [Fact]
        public void SubscribeToUnknownPublisher() {
            broker.PropertyManager.clear();
            var publisher = "0011223456656647";

            Assert.Throws<ArgumentException>(() => {
                broker.SubscribeToPublisher(publisher, (v, s, m) => {});
            });
        }

        [Fact]
        public void SubscribeToAnUnknownTopic_IsNotPossible() {
            Assert.Throws<ArgumentException>(() => {
                broker.Subscribe("UnknownTopic", null);
            });
        }

        [Fact]
        public void SubscriberReceivedMetadata_WithStringfiedKeys() {
            EventWaitHandle called = new EventWaitHandle(false, EventResetMode.AutoReset);
            ADSubscriber ProcessEvent = (value, source, meta) => {
                Assert.True(meta.ContainsKey("quality"));
                called.Set();
            };

            broker.Subscribe("WindVane", ProcessEvent);
            PublishEvent("WindVane", meta: new StringDict(){{"quality", "123"}});
            Assert.True(called.WaitOne(2000));
        }
    }
}