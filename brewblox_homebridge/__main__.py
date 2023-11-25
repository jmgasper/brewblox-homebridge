"""
Example of how to import and use the brewblox service
"""

from argparse import ArgumentParser

from brewblox_service import brewblox_logger, http, mqtt, scheduler, service

from brewblox_homebridge import subscribe
from brewblox_homebridge.models import ServiceConfig

LOGGER = brewblox_logger(__name__)


def create_parser() -> ArgumentParser:
    # brewblox-service has some default arguments
    # We can add more arguments here before sending the parser back to brewblox-service
    # The parsed values for all arguments are placed in app['config']
    # For documentation see https://docs.python.org/3/library/argparse.html
    parser: ArgumentParser = service.create_parser(default_name='brewblox_homebridge')

    # This will be used by publish_example
    # Note how we specify the type as float
    parser.add_argument('--poll-interval',
                        help='Interval (in seconds) between polling. [%(default)s]',
                        type=float,
                        default=5)

    # This will be used to map the block name to a Homebridge device name
    parser.add_argument('--block-name',
                        help='The Brewblox block name to monitor',
                        type=str)

    # The hostname of the Homebridge server
    parser.add_argument('--homebridge_host',
                        help='The Homebridge host URL / FQDN',
                        type=str)

    # The port of the Homebridge server
    parser.add_argument('--homebridge_port',
                        help='The Homebridge port',
                        type=str)

    # The auth code to use when authenticating with Homebridge
    parser.add_argument('--homebridge_auth_code',
                        help='The Homebridge auth code',
                        type=str)

    # The homebridge device to map to the block name
    parser.add_argument('--homebridge_device',
                        help='The Homebridge device name',
                        type=str)

    # The Brewblox service that holds the block
    parser.add_argument('--service',
                        help='The Brewblox service where the block lives',
                        type=str)
    return parser


def main():
    # First, we create a parser for the default service arguments
    # plus the arguments for this service
    parser = create_parser()

    # We added arguments to the parser
    # We also need an extended Pydantic model
    config = service.create_config(parser, model=ServiceConfig)

    # We have the config, now use it to create an aiohttp Application object
    # The `app` object will show up very often
    app = service.create_app(config)

    # We run the various setup() functions inside an async function
    # This way, we can already start tasks, or create asyncio Task, Future, and Event objects.
    async def setup():

        # Enable the task scheduler
        # This is required for MQTT
        # and for the RepeaterFeature used in publish_example
        scheduler.setup(app)

        # Enable event handling
        # Event subscription / publishing will be enabled after you call this function
        mqtt.setup(app)

        # Enable making HTTP requests
        # This allows you to access a shared aiohttp ClientSession
        # https://docs.aiohttp.org/en/stable/client_reference.html
        http.setup(app)

        # To keep everything consistent, examples also have the setup() function
        # In setup() they register everything that must be done before the service starts
        # It's not required to use this pattern, but it makes code easier to understand
        subscribe.setup(app)
        #publish_example.setup(app)

    # This will start the service.
    # The function blocks until you stop the process (container).
    #
    # Before startup, it awaits the `setup()` function,
    # and then adds default endpoints and prefixes for all endpoints.
    #
    # Default endpoints are:
    # {prefix}/api/doc (Swagger documentation of endpoints)
    # {prefix}/_service/status (Health check: this endpoint is called to check service status)
    #
    # The prefix is automatically added for all endpoints. You don't have to do anything for this.
    # To change the prefix, you can use the --name command line argument.
    #
    # See brewblox_service.service for more details on how arguments are parsed.
    #
    # The default value is "YOUR_PACKAGE" (provided in service.create_app()).
    # This means you can now access the example/endpoint as "/YOUR_PACKAGE/example/endpoint"
    service.run_app(app, setup(), listen_http=False)


if __name__ == '__main__':
    main()
