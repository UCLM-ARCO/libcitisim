using System;
using KinectData;
using LibCitisim;

namespace person_tracker {
    class Program {

        static void Main(string[] args) {
            string source = "0A06000000007357";
            KinectPoint[] points = new KinectPoint[] {
                new KinectPoint(
                    "trackid", "state", .0f, .1f, .2f, .5f, .6f, .9f, 12, 12345623)
            };

            Broker broker = Broker.Initialize("publisher.config");
            var pub = broker.GetPublisher(source, "PersonTracker");
            pub.Publish(points);
        }
    }
}
