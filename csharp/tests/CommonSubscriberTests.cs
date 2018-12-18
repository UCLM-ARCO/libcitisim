using System;
using System.Threading;
using Xunit;

using StringDict = System.Collections.Generic.Dictionary<string, string>;

namespace LibCitisim {

    [Collection("IceStorm Collection")]
    public class CommonSubscriberTests : AnalogEventsMixin {

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