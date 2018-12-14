using System.Collections.Generic;
using System.Threading;
using Xunit;

namespace LibCitisim {

    [Collection("IceStorm Collection")]
    public class AnalogSinkSubscriberTests : AnalogEventsMixin {

        // FIXME: this list is deprecated!
        private List<string> knownTopics = new List<string> {
            "Temperature", "Power", "Vibration", "WindVane", "PluviometerLastDay",
            "Anemometer", "Battery", "CarbonDioxide", "Humidity", "Ozone",
        };

        [Fact]
        public void SubscriberCallbackIsCalled() {
            EventWaitHandle called = new EventWaitHandle(false, EventResetMode.AutoReset);
            broker.Subscribe("Temperature", (value, source, meta) => {
                called.Set();
            });

            PublishEvent("Temperature");
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