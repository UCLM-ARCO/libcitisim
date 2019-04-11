using System;
using System.Collections.Generic;
using Xunit;

namespace LibCitisim
{

    // This class is for initializing the WelcomeService service, given
    // in the format of a Collection Fixture
    public class WelcomeServiceFixture : IDisposable {
        public WelcomeServiceFixture() {
            Console.WriteLine("++++ launch Welcome service");
            WelcomeService.StartService();
        }

        public void Dispose() {
            Console.WriteLine("---- stop Welcome service");
            WelcomeService.StopService();
        }
    }

    [CollectionDefinition("WelcomeService Collection")]
    public class WelcomeServiceCollection : ICollectionFixture<WelcomeServiceFixture> { }

    // This class is for initializing the IceStorm service, given
    // in the format of a Collection Fixture
    public class IceStormFixture : IDisposable {
        public IceStormFixture() {
            Console.WriteLine("++++ launch IS service");
            ISService.StartService();
        }

        public void Dispose() {
            Console.WriteLine("---- stop IS service");
            ISService.StopService();
        }
    }

    [CollectionDefinition("IceStorm Collection")]
    public class IceStormCollection : ICollectionFixture<IceStormFixture> { }

    // This class is for initializing the Property Server, given
    // in the format of a Collection Fixture
    public class PropertyServerFixture : IDisposable {
        public PropertyServerFixture() {
            Console.WriteLine("++++ launch PS service");
            PSService.StartService();
        }

        public void Dispose() {
            Console.WriteLine("---- stop PS service");
            PSService.StopService();
        }
    }

    [CollectionDefinition("PropertyServer Collection")]
    public class PropertyServerCollection : ICollectionFixture<PropertyServerFixture> {

    }

    // This class is for initializing all services, given
    // in the format of a Collection Fixture
    public class AllServersFixture : IDisposable {
        private PropertyServerFixture _ps;
        private IceStormFixture _is;
        private WelcomeServiceFixture _ws;

        public AllServersFixture() {
            _ps = new PropertyServerFixture();
            _is = new IceStormFixture();
            _ws = new WelcomeServiceFixture();
        }

        public void Dispose() {
            _ps.Dispose();
            _is.Dispose();
            _ws.Dispose();
        }
    }

    [CollectionDefinition("AllServers Collection")]
    public class AllServersCollection : ICollectionFixture<AllServersFixture> {

    }
}