
using System;
using Xunit;

namespace LibCitisim {

    [Collection("IceStorm Collection")]
    public class CommonPublisherTests : AnalogEventsMixin {

        [Fact]
        public void PublishToUnknownTopic_NotPossible() {
            Assert.Throws<ArgumentException>(() => {
                broker.Publish("UnknownTopic", 1.263);
            });
        }
    }
}