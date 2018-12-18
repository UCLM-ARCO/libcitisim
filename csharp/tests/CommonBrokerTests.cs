using System;
using Xunit;

namespace LibCitisim {

    public class DefaultPropertyTests {

        [Fact]
        public void DefaultTopicManagerProxy() {
            var sut = new Broker("");

            Assert.Throws<Ice.NoEndpointException>(() => {
                Console.WriteLine(sut.topicManager);
            });
        }
    }

    public class PropertyCastTests {

        [Fact]
        public void Datamodel_CheckCorrectUnits() {
            DataModel.Properties["units"].check("wats");
        }

        [Fact]
        public void Datamodel_CheckWrongUnits() {
            Assert.Throws<ArgumentException>(() => {
                DataModel.Properties["units"].check("wrong");
            });
        }
    }
}