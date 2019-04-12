
using System;
using Xunit;

namespace LibCitisim {

    [Collection("AllServers Collection")]
    public class CommonPublisherTests : AnalogEventsMixin {

        [Fact]
        public void PublishWithUnknownTransducerType_NotPossible() {
            Assert.Throws<ArgumentException>(() => {
                broker.GetPublisher(
                    source: "0011223344556677",
                    transducerType: "InvalidType");
            });
        }
    }
}