from aiohttp import web
import time
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
            LOGGER.error("Couldn't connect to Homebridge " + e)

    async def startup(self, app: web.Application):
        """Add event handling

        To get messages, you need to call `mqtt.subscribe(topic)` and `mqtt.listen(topic, callback)`.

        You can set multiple listeners for each call to subscribe, and use wildcards to filter messages.
        """
        LOGGER.info("Starting up brewblox_homebridge plugin")
        failed = True
        while(failed):
            try:
                await mqtt.listen(app, self.topic, self.on_message)
                await mqtt.subscribe(app, self.topic)
                #self.current_state =
                LOGGER.info("Current switch state: " + str(int(self.controller.get_value(self.config.homebridge_device))))
                failed = False
            except Exception as e:
                LOGGER.error("Error during startup: " + e)
                LOGGER.error("Retrying...")
                time.sleep(3)
                failed = True
        LOGGER.info("Startup successful")

    async def shutdown(self, app: web.Application):
        """Shutdown and remove event handlers

        unsubscribe() and unlisten() must be called
        with the same arguments as subscribe() and listen()
        """
        await mqtt.unsubscribe(app, self.topic)
        await mqtt.unlisten(app, self.topic, self.on_message)

    async def on_message(self, topic: str, payload: str):
        data = json.loads(payload)
        #self.current_state = int(self.controller.get_value(self.config.homebridge_device))

        if(data['key']==self.config.service and self.config.block_name in data['data'].keys()):
            block = data['data'][self.config.block_name]
            # Turn on or off, depending on desired state
            changed = False
            if(block['desiredState'] == 1 and (block['state']==None or block['state']==0 or int(self.controller.get_value(self.config.homebridge_device))==0)):
                self.controller.set_value(self.config.homebridge_device, True)
                while(int(self.controller.get_value(self.config.homebridge_device, refresh=True))==0):
                    LOGGER.debug("Waiting for switch....")
                    time.sleep(1)
                LOGGER.debug("Switch turned on successfully")
                #self.current_state = 1
                block['state']=1
                changed = True
            elif(block['desiredState'] == 0 and (block['state']==None or block['state']==1 or int(self.controller.get_value(self.config.homebridge_device))==1)):
                self.controller.set_value(self.config.homebridge_device, False)
                while(int(self.controller.get_value(self.config.homebridge_device, refresh=True))==1):
                    LOGGER.debug("Waiting for switch....")
                    time.sleep(1)
                LOGGER.debug("Switch turned off successfully")
                #self.current_state = 0

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
    LOGGER.info("Staring brewblox-homebridge setup")
    features.add(app, SubscribingFeature(app))
    LOGGER.info("Setup successful")


def fget(app: web.Application) -> SubscribingFeature:
    # Retrieve the registered instance of SubscribingFeature
    return features.get(app, SubscribingFeature)
