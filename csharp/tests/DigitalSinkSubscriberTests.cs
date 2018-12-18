
using System.Threading;
using Xunit;

namespace LibCitisim {

    [Collection("IceStorm Collection")]
    public class DigitalSinkSubscriberTests : DigitalEventsMixin {

        private string topicName = "Twilight";

        [Fact]
        public void SubscribeCallbackIsCalled() {
            EventWaitHandle called = new EventWaitHandle(false, EventResetMode.AutoReset);
            broker.Subscribe(topicName, (value, source, meta) => {
                called.Set();
            });

            PublishEvent(topicName);
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