"""
smpub - Smart Publisher: CLI/API framework based on SmartSwitch.

Example:
    from smpub import Publisher, PublishedClass
    from smartswitch import Switcher

    class MyHandler(PublishedClass):
        __slots__ = ('data',)
        api = Switcher(prefix='handler_')

        def __init__(self):
            self.data = {}

        @api
        def handler_add(self, key, value):
            self.data[key] = value

    class MyApp(Publisher):
        def initialize(self):
            self.handler = MyHandler()
            self.publish('handler', self.handler)

    if __name__ == "__main__":
        app = MyApp()
        app.run()
"""

from smpub.publisher import Publisher
from smpub.published import PublishedClass, PublisherContext, discover_api_json

__version__ = "0.1.0"
__all__ = ["Publisher", "PublishedClass", "PublisherContext", "discover_api_json"]
