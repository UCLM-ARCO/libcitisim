using System;
using Xunit;

namespace LibCitisim {

    public class BrokerTests {

        public BrokerTests() {
            Broker.ForgetInstance();
        }

        [Fact]
        public void Singleton_InitializeReturnsBroker() {
            var broker1 = Broker.Initialize("");
            var broker2 = Broker.GetBroker();
            Assert.True(ReferenceEquals(broker1, broker2));
        }

        [Fact]
        public void Singleton_TwoGetBrokerReturnsSame() {
            Broker.Initialize("");
            var broker1 = Broker.GetBroker();
            var broker2 = Broker.GetBroker();
            Assert.True(ReferenceEquals(broker1, broker2));
        }

        [Fact]
        public void Singleton_SecondInitializeThrowsException() {
            Broker.Initialize("");
            Assert.Throws<InvalidOperationException>(() => {
                Broker.Initialize("");
            });
        }

        [Fact]
        public void Singleton_GetBrokerWithoutInitializeThrowsException() {
            Assert.Throws<InvalidOperationException>(() => {
                Broker.GetBroker();
            });
        }
    }

    public class DefaultPropertyTests {

        [Fact]
        public void DefaultTopicManagerProxy() {
            Broker.ForgetInstance();
            var sut = Broker.Initialize("");

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