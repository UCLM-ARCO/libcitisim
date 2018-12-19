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
        private EventWaitHandle ev = new EventWaitHandle(false, EventResetMode.AutoReset);

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
        public void OneTimePublish_UseDoubleIsOK() {
            var value = 123.4;

            servant.Setup(
                m => m.notify(
                    (float)value,
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
            // it should raise an exception as it uses the MetadataUtil
            Assert.Throws<ArgumentException>(() => {
                broker.Publish(topicName, 123.5, meta: new StringDict() {
                    {"someunknownkey", "true"}
                });
            });

            Assert.Throws<FormatException>(() => {
                broker.Publish(topicName, 123.5, meta: new StringDict() {
                    {"quality", "invalidvalue"}
                });
            });
        }

        [Fact]
        public void Publisher_SimpleEvent() {
            // create a reusable publisher for the given topic, source as a
            // random string, meta with timestamp updated

            servant.Setup(
                m => m.notify(
                    value,
                    It.Is<string>(s => s.Length > 5),
                    Match.Create<Metadata>(CheckMeta(null)),
                    It.IsAny<Ice.Current>()))
                .Callback(() => ev.Set())
                .Verifiable();

            var p = broker.GetPublisher(topicName);
            p.Publish(value);

            ev.WaitOne(2000);
            servant.Verify();
        }

        [Fact]
        public void Publisher_WithDefaultSourceAndMeta() {
            // create a reusable publisher, set source and meta as
            // specified plus Timestamp field

            var source = "Source123";
            var meta = new StringDict() {{"quality", "24"}};

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

            var p = broker.GetPublisher(topicName, source, meta);
            p.Publish(value);

            ev.WaitOne(2000);
            servant.Verify();
        }

        [Fact]
        public void Publisher_WithOverriddenSource_JustOnce() {
            // change source only for this specific event
            var source = "Source1";

            servant.Setup(
                m => m.notify(
                    value,
                    It.IsAny<string>(),
                    Match.Create<Metadata>(CheckMeta(null)),
                    It.IsAny<Ice.Current>()))
                .Callback(() => ev.Set())
                .Verifiable();

            servant.Setup(
                m => m.notify(
                    value,
                    source,
                    Match.Create<Metadata>(CheckMeta(null)),
                    It.IsAny<Ice.Current>()))
                .Callback(() => ev.Set())
                .Verifiable();

            var p = broker.GetPublisher(topicName);

            p.Publish(value);
            ev.WaitOne(2000);

            p.Publish(value, source: source);
            ev.WaitOne(2000);

            servant.Verify();
        }

        [Fact]
        public void Publisher_WithOverriddenMeta_JustOnce() {
            // update meta only for this specific event, it will have
            // Timestamp and also what you say here

            var p = broker.GetPublisher(topicName);
            var meta = new StringDict() {{"quality", "120"}};

            servant.Setup(
                m => m.notify(
                    value,
                    It.IsAny<string>(),
                    Match.Create<Metadata>(CheckMeta(new Metadata() {
                        {MetadataField.Quality, meta["quality"]}
                    })),
                    It.IsAny<Ice.Current>()))
                .Callback(() => ev.Set())
                .Verifiable();

            p.Publish(value, meta: meta);

            ev.WaitOne(2000);
            servant.Verify();
        }

        [Fact]
        public void Publisher_WithOverriddenInvalidMeta_JustOnce() {
            // it should raise an exception as it uses the MetadataUtil
            var p = broker.GetPublisher(topicName);

            Assert.Throws<ArgumentException>(() => {
                p.Publish(123.5, meta: new StringDict() {
                    {"invalidkey", "1"}
                });
            });

            Assert.Throws<FormatException>(() => {
                p.Publish(123.5, meta: new StringDict() {
                    {"quality", "invalidvalue"}
                });
            });
        }

        [Fact]
        public void Publisher_NoTimestampInMeta_JustOnce() {
            // create a reusable publisher for the given topic, source as a
            // random string, meta with no timestamp

            var p = broker.GetPublisher(topicName, meta: new StringDict() {{"timestamp", null}});

            servant.Setup(
                m => m.notify(
                    value,
                    It.IsAny<string>(),
                    Match.Create<Metadata>(CheckMeta(new Metadata() {
                        {MetadataField.Timestamp, null}
                    })),
                    It.IsAny<Ice.Current>()))
                .Callback(() => ev.Set())
                .Verifiable();

            p.Publish(value);

            ev.WaitOne(2000);
            servant.Verify();
        }

        [Fact]
        public void PublishToAllCurrentTopics() {
            // if this does not raise an exception, they are valid topic names
            var value = 12;
            foreach (var name in knownTopics) {
                EventWaitHandle ev = new EventWaitHandle(false, EventResetMode.AutoReset);
                Mock<AnalogSinkDisp_> servant = new Mock<AnalogSinkDisp_> {CallBase = true};
                proxy = AdapterAdd((Ice.Object)servant.Object);
                Subscribe(name, proxy);

                servant.Setup(
                m => m.notify(
                    value,
                    It.IsAny<string>(),
                    Match.Create<Metadata>(CheckMeta(null)),
                    It.IsAny<Ice.Current>()))
                .Callback(() => ev.Set())
                .Verifiable();

                broker.Publish(name, value);

                ev.WaitOne(2000);
                servant.Verify();

                value += 5;
            }
        }

    }
}