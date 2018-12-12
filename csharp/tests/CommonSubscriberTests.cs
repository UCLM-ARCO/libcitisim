using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;
using Xunit;

using MetadataDict = System.Collections.Generic.Dictionary<string, string>;

namespace LibCitisim {

    public class EventsFixture : IDisposable {
        protected Ice.Communicator ic;
        private string pwd = Environment.GetEnvironmentVariable("TEST_DIR");
        private string config;
        private Process isServer;

        public EventsFixture() {
            config = pwd + "/tests.config";

            _LaunchIceStorm();
            _IceInitialize();
        }

        private void _IceInitialize() {
            List<string> args = new List<string> () {
                "", "--Ice.Config=" + config
            };

            string[] args_ = args.ToArray();
            ic = Ice.Util.initialize(ref args_);
        }

        private void _LaunchIceStorm() {
            var dbPath = "/tmp/test-libcitisim-is-db";
            if (Directory.Exists(dbPath))
                Directory.Delete(dbPath);
            Directory.CreateDirectory(dbPath);

            isServer = new Process();
            isServer.StartInfo.FileName = "icebox";
            isServer.StartInfo.Arguments = "--Ice.Config=" + config;
            isServer.StartInfo.UseShellExecute = false;
            isServer.StartInfo.RedirectStandardError = true;
            isServer.StartInfo.RedirectStandardOutput = true;

            StringBuilder output = new StringBuilder();
            EventWaitHandle ev = new EventWaitHandle(false, EventResetMode.AutoReset);
            isServer.ErrorDataReceived += new DataReceivedEventHandler((sender, e) => {
                if (!String.IsNullOrEmpty(e.Data)) {
                    Console.WriteLine("ERROR: "+e.Data);
                }
            });
            isServer.OutputDataReceived += new DataReceivedEventHandler((sender, e) => {
                if (!String.IsNullOrEmpty(e.Data)) {
                    output.Append(e.Data);
                    ev.Set();
                }
            });
            Assert.True(isServer.Start());

            ev.WaitOne(5000);
            Assert.Equal("IceStorm is ready\n", output.ToString());
        }

        public IceStorm.TopicPrx GetTopic(string name) {
            dynamic manager = ic.propertyToProxy("TopicManager.Proxy");
            manager = IceStorm.TopicManagerPrxHelper.checkedCast(manager);
            try {
                return manager.retrieve(name);
            }
            catch (IceStorm.NoSuchTopic) {
                return manager.create(name);
            }
        }

        public void Dispose() {
            isServer.Dispose();
            ic.shutdown();
            ic.destroy();
        }
    }

    public class AnalogEventsMixin : EventsFixture {

        protected void _PublishEvent(string topicName, string source="", MetadataDict meta=null) {
            var topic = GetTopic(topicName);
            var publisher = topic.getPublisher();
            if (meta != null) {

            }
        }
    }

    public class CommonSubscriberTests : AnalogEventsMixin {

        private Broker broker;

        public CommonSubscriberTests() {
            broker = new Broker();
        }

        [Fact]
        public void SubscribeToAnUnknownTopic_IsNotPossible() {
            Assert.Throws<ArgumentException>(() => {
                broker.Subscribe("UnknownTopic", null);
            });
        }

        [Fact]
        public void SubscriberReceivedMetadata_WithStringfiedKeys() {
            bool called = false;
            AnalogSubscriber ProcessEvent = (
                float value, string source, Dictionary<string, string> meta) => {
                    called = true;
            };

            broker.Subscribe("WindVane", ProcessEvent);
            _PublishEvent("WindVane", meta: new MetadataDict(){{"quality", "123"}});
            Assert.True(called);
        }
    }
}