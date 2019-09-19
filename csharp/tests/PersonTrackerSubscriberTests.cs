using System.Collections.Generic;
using System.Threading;
using Xunit;

namespace LibCitisim {

    [Collection("AllServers Collection")]
    public class PersonTrackerSubscriberTests : PersonTrackerMixin {

        [Fact]
        public void SubscriberCallbackIsCalled() {
            EventWaitHandle called = new EventWaitHandle(false, EventResetMode.AutoReset);
            broker.Subscribe("PersonTracking", (value, source, meta) => {
                called.Set();
            });

            PublishEvent("PersonTracking");
            Assert.True(called.WaitOne(3000));
        }

        [Fact]
        public void SubscribeToAllCurrentTopics() {
            // if this does not raise an exception, they are valid topic names
            foreach (var name in knownTopics) {
                broker.Subscribe(name, (v, s, m) => {});
            }
        }
    }
}