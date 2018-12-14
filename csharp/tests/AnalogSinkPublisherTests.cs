using Xunit;
using StringDict = System.Collections.Generic.Dictionary<string, string>;

namespace LibCitisim {

    [Collection("IceStorm Collection")]
    public class AnalogSinkPublisherTests : AnalogEventsMixin {

        private string topicName = "Temperature";
        private float value = 123.5f;
        private string source = "TestSource";
        private StringDict meta = new StringDict() {{"quallity", "200"}};

        [Fact]
        public void OneTimePublishEvent_IsOK() {
            // # create a one-time-usage publisher, set source as a random
            // # string, meta with timestamp updated
            // self.broker.publish(self.topic_name, self.value)

            // assert_that(self.servant.notify,
            //             called().
            //             with_args(self.value, anything(), anything(), anything()).
            //             async(timeout=2))

            // got_meta = self.servant.notify.calls[0].args[2]
            // got_ts = int(got_meta[SmartObject.MetadataField.Timestamp])
            // assert_that(got_ts, close_to(time(), 10))

            // got_source = self.servant.notify.calls[0].args[1]
            // assert_that(len(got_source), greater_than(5))
        }
    }
}