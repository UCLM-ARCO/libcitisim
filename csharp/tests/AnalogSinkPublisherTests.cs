using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Ice;
using IceInternal;
using Moq;
using SmartObject;
using Xunit;

using Metadata = System.Collections.Generic.Dictionary<SmartObject.MetadataField, string>;
using StringDict = System.Collections.Generic.Dictionary<string, string>;

namespace LibCitisim {

    [Collection("IceStorm Collection")]
    public class AnalogSinkPublisherTests : AnalogEventsMixin {

        private string topicName = "Temperature";
        private float value = 123.5f;
        private string source = "TestSource";
        private StringDict meta = new StringDict() { { "quality", "200" } };
        private Ice.ObjectPrx proxy;
        private Mock<AnalogSinkDisp_> servant = new Mock<AnalogSinkDisp_> {CallBase = true};
        EventWaitHandle ev = new EventWaitHandle(false, EventResetMode.AutoReset);

        public AnalogSinkPublisherTests() {
            proxy = AdapterAdd((Ice.Object)servant.Object);
            Subscribe(topicName, proxy);
        }

        [Fact]
        public void OneTimePublish_EventIsOK() {
            servant.Setup(
                m => m.notify(
                    value,
                    It.Is<string>(s => s.Length > 5),
                    Match.Create<Metadata>(CheckMeta(null)),
                    It.IsAny<Ice.Current>()))
                .Callback(() => ev.Set())
                .Verifiable();

            // create a one-time-usage publisher, set source as a random
            // string, meta with timestamp updated
            broker.Publish(topicName, value);

            ev.WaitOne(2000);
            servant.Verify();
        }

        [Fact]
        public void OneTimePublish_GivenSourceAndMeta() {
            // create a one-time-usage publisher, set source as given, and
            // meta with Timestamp and also what you set here
            servant.Setup(
                m => m.notify(
                    value,
                    source,
                    Match.Create<Metadata>(CheckMeta(new Metadata() {
                        {MetadataField.Quality, meta["quality"]}
                    })),
                    It.IsAny<Ice.Current>()))
                .Callback(() => ev.Set())
                .Verifiable();

            broker.Publish(topicName, value, source, meta);

            ev.WaitOne(2000);
            servant.Verify();
        }

        [Fact]
        public void OneTimePublish_WithIncorrectMeta() {
            // it should raise an exception as it uses the MetadataHelper
            Assert.Throws<ArgumentException>(() => {
                broker.Publish("Temperature", 123.5, meta: new StringDict() {
                    {"someunknownkey", "true"}
                });
            });

            Assert.Throws<FormatException>(() => {
                broker.Publish("Temperature", 123.5, meta: new StringDict() {
                    {"quality", "invalidvalue"}
                });
            });
        }
    }
}