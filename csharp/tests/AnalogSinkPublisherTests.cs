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

    // Note: we can not add a mock as a servant, because the adapter will call iceDispatch()
    // but is not implemented inside the mock (we need a mimic...)
    class AnalogSinkWrapp : AnalogSinkDisp_ {
        private AnalogSinkDisp_ mock;

        public AnalogSinkWrapp(AnalogSinkDisp_ mock) {
            this.mock = mock;
        }

        public override void notify(float value, string source, Metadata meta, Current current = null) {
            mock.notify(value, source, meta, current);
        }
    }

    [Collection("IceStorm Collection")]
    public class AnalogSinkPublisherTests : AnalogEventsMixin {

        private string topicName = "Temperature";
        private float value = 123.5f;
        private string source = "TestSource";
        private StringDict meta = new StringDict() { { "quallity", "200" } };
        private Ice.ObjectPrx proxy;
        private Mock<AnalogSinkDisp_> servant = new Mock<AnalogSinkDisp_>();

        public AnalogSinkPublisherTests() {
            proxy = AdapterAdd(new AnalogSinkWrapp(servant.Object));
            Subscribe(topicName, proxy);
        }

        [Fact]
        public void OneTimePublishEvent_IsOK() {
            EventWaitHandle ev = new EventWaitHandle(false, EventResetMode.AutoReset);
            servant.Setup(
                m => m.notify(
                    value,
                    It.IsAny<string>(),
                    It.IsAny<Metadata>(),
                    It.IsAny<Ice.Current>()))
                .Callback(() => ev.Set())
                .Verifiable();

            // create a one-time-usage publisher, set source as a random
            // string, meta with timestamp updated
            broker.Publish(topicName, value);

            ev.WaitOne(2000);
            servant.Verify();

            // got_meta = self.servant.notify.calls[0].args[2]
            // got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
            // assert_that(got_ts, close_to(time(), 10))

            // got_source = self.servant.notify.calls[0].args[1]
            // assert_that(len(got_source), greater_than(5))
        }
    }
}