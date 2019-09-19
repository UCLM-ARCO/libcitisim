
using System;
using System.Collections.Generic;
using KinectData;

namespace LibCitisim {

    public class PersonTrackerMixin : EventsFixture {

        // FIXME: this list will eventually get deprecated!
        protected List<string> knownTopics = new List<string> {
            "PersonTracking"
        };

        protected void PublishEvent(string topicName, string source = "") {
            var topic = GetTopic(topicName);
            var prx = topic.getPublisher();

            PersonTrackerPrx publisher = PersonTrackerPrxHelper.uncheckedCast(prx);

            KinectPoint[] points = new KinectPoint[] {
                new KinectPoint(
                    "trackid", "state", 1.0f, .5f, 2.2f, .7f, 4f, 12f, 14, 122347623)
            };
            publisher.notify(points, "Test");
            Console.WriteLine(">>> event published (using: {0})", publisher);
        }
    }
}