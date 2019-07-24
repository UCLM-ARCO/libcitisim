import os
import shutil
import Ice
import IceStorm
from subprocess import Popen, PIPE
from select import select

# FIXME decorator property/functools.lru_cache provides the same
class memoizedproperty:
    """Memoized properties

    >>> import random
    >>> class A:
    ...     @memoizedproperty
    ...     def a_property(self):
    ...         return random.randrange(1000)
    ...
    >>> a1 = A()
    >>> v1 = a1.a_property
    >>> v2 = a1.a_property
    >>> assert v1 == v2
    """

    def __init__(self, method):
        self.method = method
        self.instance = None
        self.cache = {}

    def __get__(self, instance, owner):
        self.instance = instance
        if instance not in self.cache:
            self.cache[instance] = self.method(instance)

        return self.cache[instance]

    def reset(self):
        del self.cache[self.instance]


class EventsMixin:
    @classmethod
    def setUpClass(cls):
        print("- setting up class...")
        if not hasattr(cls, "pwd") or not hasattr(cls, "config"):
            print("TEST ERROR: please, provide pwd and config")
            return

        cls.run_icestorm_server()
        cls.run_property_server()
        cls.run_welcome_server()

    @classmethod
    def run_icestorm_server(cls):
        db_path = "/tmp/test-libcitisim-is-db"
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
        os.makedirs(db_path)

        config = os.path.join(cls.pwd, "is.config")
        assert os.path.exists(config), "Missing " + config
        cmd = "icebox --Ice.Config=" + config
        cls.is_server = Popen(cmd.split(), cwd=cls.pwd, stdout=PIPE)

        print("- waiting for IS to launch...")
        pipe = select([cls.is_server.stdout], [], [], 3)[0]
        assert len(pipe), "IceStorm service did not launch correctly"
        assert pipe[0].readline() == b"IceStorm is ready\n"
        print("- IceStorm server OK")

    @classmethod
    def run_property_server(cls):
        config = os.path.join(cls.pwd, "ps.config")
        assert os.path.exists(config), "Missing " + config
        cmd = "property-server --Ice.Config=" + config

        if os.path.exists("/tmp/ps.json"):
            os.unlink("/tmp/ps.json")

        cls.ps_server = Popen(cmd.split(), cwd=cls.pwd, stdout=PIPE)
        print("- waiting for PropertyServer to launch...")
        while True:
            pipe = select([cls.ps_server.stdout], [], [], 3)[0]
            out = pipe[0].readline()
            assert len(pipe), "PropertyService did not launch correctly"
            if out.startswith(b"PropertyServer -t -e 1.1:tcp"):
                break
        print("- Property server OK")

    @classmethod
    def run_welcome_server(cls):
        config = os.path.join(cls.pwd, "welcome.config")
        assert os.path.exists(config), "Missing " + config
        cmd = "citisim-welcome --Ice.Config=" + config

        cls.welcome_server = Popen(
            cmd.split(), cwd=cls.pwd, stdout=PIPE, stderr=PIPE)
        print("- waiting for WelcomeServer to launch...")
        pipe = select([cls.welcome_server.stderr], [], [], 3)[0]
        assert len(pipe), "WelcomeService service did not launch correctly"
        out = pipe[0].readline()
        assert out == b"INFO:Welcome service started\n", out
        print("- Welcome server OK")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "is_server"):
            cls.is_server.terminate()
            cls.is_server.kill()

        if hasattr(cls, "welcome_server"):
            cls.welcome_server.terminate()
            cls.welcome_server.kill()

        if hasattr(cls, "ps_server"):
            cls.ps_server.terminate()
            cls.ps_server.kill()

    def _ice_setup(self):
        print("- setting up instance...")
        assert os.path.exists(self.config), "Missing " + self.config
        args = ["", "--Ice.Config=" + self.config]
        self.ic = Ice.initialize(args)
        self.adapter = self.ic.createObjectAdapterWithEndpoints(
            'adapter', 'tcp -h 127.0.0.1')
        self.adapter.activate()

    def _ice_finish(self):
        if self.ic:
            self.ic.shutdown()

    def _get_topic(self, name):
        manager = self.ic.propertyToProxy("TopicManager.Proxy")
        manager = IceStorm.TopicManagerPrx.checkedCast(manager)
        try:
            return manager.retrieve(name)
        except IceStorm.NoSuchTopic:
            return manager.create(name)

    def _subscribe(self, topic_name, proxy):
        topic = self._get_topic(topic_name)
        print(topic.subscribeAndGetPublisher({}, proxy))

    def _adapter_add(self, servant):
        return self.adapter.addWithUUID(servant)
