using System;
using System.Collections.Generic;
using Json = Newtonsoft.Json.JsonConvert;
using PropertyService;
using Xunit;

using Metadata = System.Collections.Generic.Dictionary<SmartObject.MetadataField, string>;
using System.Globalization;

namespace LibCitisim {

    public class PropertyMixin : IDisposable {

        protected Ice.Communicator ic;
        protected Broker broker;
        private string pwd = Environment.GetEnvironmentVariable("TEST_DIR");
        private string config;
        private PropertyServerPrx _manager;

        public PropertyMixin() {
            config = pwd + "/tests.config";

            // for testing purposes only
            List<string> args = new List<string>() { "", "--Ice.Config=" + config };
            string[] args_ = args.ToArray();
            ic = Ice.Util.initialize(ref args_);

            // the real subject under testing
            try {
               broker = Broker.Initialize(config);
            }catch(InvalidOperationException) {
                broker = Broker.GetBroker();
            }
        }

        public void Dispose() {
            ic.shutdown();
            ic.destroy();
            Console.WriteLine(">>> disposed test");
        }

        internal PropertyServerPrx manager {
            get {
                if (_manager != null)
                    return _manager;

                var proxy = ic.propertyToProxy("PropertyServer.Proxy");
                _manager = PropertyServerPrxHelper.checkedCast(proxy);
                return _manager;
            }
        }

        internal string GetProperty(string path) {
            return manager.get(path);
        }

        internal void SetProperty(string path, string value) {
            manager.set(path, value);
        }
    }

    [Collection("AllServers Collection")]
    public class PropertyServerTests : PropertyMixin {

        [Fact]
        public void SetProperty_AsString() {
            // set a string property
            var path = "17510026 | units";
            string value = "Celsius";

            broker.SetProperty(path, value);

            string got = Json.DeserializeObject<string>(GetProperty(path));
            Assert.Equal(value, got);
        }

        [Fact]
        public void GetProperty_AsString() {
            // get a string property
            var path = "17510027 | units";
            string value = "Celsius";
            SetProperty(path, Json.SerializeObject(value));

            string got = broker.GetProperty(path);

            got = Json.DeserializeObject<string>(got);
            Assert.Equal(value, got);
        }

        [Fact]
        public void SetProperty_AsInt() {
            // set an integer property
            var path = "17510026 | int";
            int value = 6486;

            broker.SetProperty(path, value);

            int got = Json.DeserializeObject<int>(GetProperty(path));
            Assert.Equal(value, got);
        }

        [Fact]
        public void GetProperty_AsInt() {
            // get an integer property
            var path = "17510027 | int";
            int value = 6486;
            SetProperty(path, Json.SerializeObject(value));

            dynamic got = broker.GetProperty(path);

            got = Json.DeserializeObject<int>(got);
            Assert.Equal(value, got);
        }

        [Fact]
        public void SetProperty_AsFloat() {
            // set a float property
            var path = "17510026 | float";
            float value = 64.86f;

            broker.SetProperty(path, value);

            float got = Json.DeserializeObject<float>(GetProperty(path));
            Assert.Equal(value, got);
        }

        [Fact]
        public void GetProperty_AsFloat() {
            // get a float property
            var path = "17510027 | float";
            float value = 64.86f;
            SetProperty(path, Json.SerializeObject(value));

            dynamic got = broker.GetProperty(path);

            got = Json.DeserializeObject<float>(got);
            Assert.Equal(value, got);
        }

        [Fact]
        public void SetProperty_AsList() {
            // set a list property
            var path = "17510026 | list";
            List<int> value = new List<int>() {-50, 255};

            broker.SetProperty(path, value);

            dynamic got = Json.DeserializeObject<List<int>>(GetProperty(path));
            Assert.Equal(value, got);
        }

        [Fact]
        public void GetProperty_AsList() {
            // get a list property
            var path = "17510027 | list";
            List<int> value = new List<int>() {-50, 255};
            SetProperty(path, Json.SerializeObject(value));

            dynamic got = broker.GetProperty(path);

            got = Json.DeserializeObject<List<int>>(got);
            Assert.Equal(value, got);
        }

        [Fact]
        public void SetProperty_AsDictionary() {
            // set a dictionary property
            var path = "17510026 | dict";
            Dictionary<string, string> value = new Dictionary<string, string> {
                {"key1", "a"}, {"key2", "2"}, {"key3", "3.14"}
            };

            broker.SetProperty(path, value);

            dynamic got = Json.DeserializeObject<Dictionary<string, string>>(GetProperty(path));
            Assert.Equal(value, got);

            // individual key values
            var key1_value = Json.DeserializeObject<string>(GetProperty("17510026 | dict | key1"));
            Assert.Equal(value["key1"], key1_value);

            var key2_value = Json.DeserializeObject<int>(GetProperty("17510026 | dict | key2"));
            Assert.Equal(int.Parse(value["key2"]), key2_value);

            var key3_value = Json.DeserializeObject<float>(GetProperty("17510026 | dict | key3"));
            var expected = float.Parse(value["key3"], CultureInfo.InvariantCulture.NumberFormat);
            Assert.Equal(expected, key3_value);
        }

        [Fact]
        public void GetProperty_AsDictionary() {
            // get a dictionary property
            var path = "17510027 | dict";
            Dictionary<string, string> value = new Dictionary<string, string> {
                {"key1", "a"}, {"key2", "2"}, {"key3", "3.14"}
            };
            SetProperty(path, Json.SerializeObject(value));

            dynamic got = broker.GetProperty(path);

            got = Json.DeserializeObject<Dictionary<string, string>>(got);
            Assert.Equal(value, got);

            // individual key values
            var key1_value = Json.DeserializeObject<string>(
                broker.GetProperty("17510027 | dict | key1"));
            Assert.Equal(value["key1"], key1_value);

            var key2_value = Json.DeserializeObject<int>(
                broker.GetProperty("17510027 | dict | key2"));
            Assert.Equal(int.Parse(value["key2"]), key2_value);

            var key3_value = Json.DeserializeObject<float>(
                broker.GetProperty("17510027 | dict | key3"));
            var expected = float.Parse(value["key3"], CultureInfo.InvariantCulture.NumberFormat);
            Assert.Equal(expected, key3_value);
        }

        // FIXME: I didn't find a non-serializable object to test!
        // [Fact]
        // public void SetNoSerializableProperty_ShouldRaiseException() {
        //     // set a value that can not be JSON serialized
        //     var path = "17510026 | notSerializable";
        //     Type value = typeof(DateTime);

        //     Assert.Throws<ArgumentException>(() => {
        //         broker.SetProperty(path, value);
        //     });
        // }
    }
}