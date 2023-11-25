from aiohttp import web
import json
from brewblox_homebridge.homebridge.HomeBridgeController import *
from brewblox_service import brewblox_logger, features, mqtt

from brewblox_homebridge.models import ServiceConfig

LOGGER = brewblox_logger(__name__)

class SubscribingFeature(features.ServiceFeature):
    def __init__(self, app: web.Application):
        super().__init__(app)
        self.config: ServiceConfig = app['config']
        self.topic = f'{self.config.history_topic}/#'
        try:
            self.controller = HomeBridgeController(self.config.homebridge_host, self.config.homebridge_port, self.config.homebridge_auth_code)
            LOGGER.debug(self.controller.accessories)
        except Exception as e:
            LOGGER.error("Couldn't connect to Homebridge", e)

    async def startup(self, app: web.Application):
        """Add event handling

        To get messages, you need to call `mqtt.subscribe(topic)` and `mqtt.listen(topic, callback)`.

        You can set multiple listeners for each call to subscribe, and use wildcards to filter messages.
        """
        await mqtt.listen(app, self.topic, self.on_message)
        await mqtt.subscribe(app, self.topic)

    async def shutdown(self, app: web.Application):
        """Shutdown and remove event handlers

        unsubscribe() and unlisten() must be called
        with the same arguments as subscribe() and listen()
        """
        await mqtt.unsubscribe(app, self.topic)
        await mqtt.unlisten(app, self.topic, self.on_message)

    async def on_message(self, topic: str, payload: str):
        data = json.loads(payload)
        if(data['key']==self.config.service and self.config.block_name in data['data'].keys()):
            block = data['data'][self.config.block_name]
            LOGGER.debug(self.config.block_name + " " + json.dumps(block))
            # Turn on or off, depending on desired state
            changed = False
            if(block['desiredState'] == 1 and (block['state']==None or block['state']==0)):
                self.controller.set_value(self.config.homebridge_device, True)
                block['state']=1
                changed = True
            elif(block['desiredState'] == 0 and (block['state']==None or block['state']==1)):
                self.controller.set_value(self.config.homebridge_device, False)
                block['state']=0
                changed = True

            # Publish the updated state, but only if we changed the value
            if(changed == True):
                data['data'][self.config.block_name]=block
                LOGGER.debug("Updated block " + self.config.block_name + json.dumps(data))
                await mqtt.publish(self.app,
                        topic,
                        json.dumps({
                            'key': self.config.service,
                            'data': data['data']
                        }))
        else:
            LOGGER.error("Couldn't find block name " + self.config.block_name + " to map to Homebridge")


def setup(app: web.Application):
    # We register our feature here
    # It will now be automatically started when the service starts
    features.add(app, SubscribingFeature(app))


def fget(app: web.Application) -> SubscribingFeature:
    # Retrieve the registered instance of SubscribingFeature
    return features.get(app, SubscribingFeature)
