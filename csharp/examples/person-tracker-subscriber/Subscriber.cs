using System;
using LibCitisim;

namespace person_tracker_subscriber {
    class Program {

        static void Main(string[] args) {
            Broker broker = Broker.Initialize("subscriber.config");
            broker.SubscribeToPublisher("0A06000000007357", (p, s) => {
                Console.WriteLine($"- received event, source: {s}, points: {p}");
            });

            Console.WriteLine("Waiting events...");
            broker.WaitForEvents();
        }
    }
}
