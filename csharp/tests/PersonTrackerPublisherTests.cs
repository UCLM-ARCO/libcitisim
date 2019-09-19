
using System.Threading;
using KinectData;
using Moq;
using Xunit;

namespace LibCitisim {

    [Collection("AllServers Collection")]
    public class PersonTrackerPublisherTests : PersonTrackerMixin {

        private string source = "0011223344556699";
        private string transducerType = "PersonTracker";
        private KinectPoint[] points = new KinectPoint[] {
            new KinectPoint("trackid", "state", .0f, .1f, .2f, .5f, .6f, .9f, 12, 12345623)
        };

        private Ice.ObjectPrx proxy;
        private Mock<PersonTrackerDisp_> servant =
            new Mock<PersonTrackerDisp_> {CallBase = true};
        private EventWaitHandle ev =
            new EventWaitHandle(false, EventResetMode.AutoReset);

        public PersonTrackerPublisherTests() {
            proxy = AdapterAdd((Ice.Object)servant.Object);
        }

        [Fact]
        public void Publisher_SimpleEvent() {

            servant.Setup(
                m => m.notify(
                    points,
                    It.Is<string>(s => s.Length > 5),
                    It.IsAny<Ice.Current>()))
                .Callback(() => ev.Set())
                .Verifiable();

            var p = broker.GetPublisher(source, transducerType);
            p.Subscribe(proxy);
            p.Publish(points);

            ev.WaitOne(2000);
            servant.Verify();
        }
    }

    [Collection("AllServers Collection")]
    public class BidirPersonTrackerPublisherTests : PersonTrackerMixin {

        private string source = "0011223344556699";
        private string transducerType = "PersonTracker";
        private KinectPoint[] points = new KinectPoint[] {
            new KinectPoint("trackid", "state", .0f, .1f, .2f, .5f, .6f, .9f, 12, 12345623)
        };

        private Ice.ObjectPrx proxy;
        private Mock<PersonTrackerDisp_> servant =
            new Mock<PersonTrackerDisp_> {CallBase = true};
        private EventWaitHandle ev =
            new EventWaitHandle(false, EventResetMode.AutoReset);

        public BidirPersonTrackerPublisherTests() {
            SetupBidirBroker();
            proxy = AdapterAdd((Ice.Object)servant.Object);
        }

        [Fact]
        public void Publisher_SimpleEvent() {

            servant.Setup(
                m => m.notify(
                    points,
                    It.Is<string>(s => s.Length > 5),
                    It.IsAny<Ice.Current>()))
                .Callback(() => ev.Set())
                .Verifiable();

            var p = broker.GetPublisher(source, transducerType);
            p.Subscribe(proxy);
            p.Publish(points);

            ev.WaitOne(2000);
            servant.Verify();
        }
    }
}
