using System;
using System.Collections.Generic;

using StringDict = System.Collections.Generic.Dictionary<string, string>;
using Metadata = System.Collections.Generic.Dictionary<SmartObject.MetadataField, string>;


namespace LibCitisim {

    public class DigitalEventsMixin : EventsFixture {

        // FIXME: this list will eventually get deprecated!
        protected List<string> knownTopics = new List<string> {
            "Twilight"
        };

        protected void PublishEvent(string topicName, string source="",
                                    StringDict meta=null, bool value=true) {

            var topic = GetTopic(topicName);
            var prx = topic.getPublisher();
            Metadata meta_ = new Metadata();
            if (meta != null)
                 meta_ = MetadataUtil.FromDict(meta);
            SmartObject.DigitalSinkPrx publisher =
                SmartObject.DigitalSinkPrxHelper.uncheckedCast(prx);
            publisher.notify(value, "Test", meta_);
            Console.WriteLine(">>> event published (using: {0})", publisher);
        }
    }
}