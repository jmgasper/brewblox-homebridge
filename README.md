# Homebridge Service

This package contains a simple [Homebridge](https://homebridge.io) service implementation that can control Homebridge switches.  In my personal setup, this is used in place of SSRs to control pumps and heating elements.  [Zigbee switches](https://www.ikuu.com.au/product/double-power-point-ip54/) have been installed and integrated with Homebridge via [Zigbee2MQTT](https://www.zigbee2mqtt.io) and [homebridge-z2m](https://z2m.dev)

### Config

To set this up, create a Digital Actuator in your service, without assigning it a channel.  Our code will act as the channel, taking signals and sending them to Homebridge to turn a switch on or off.

You need to provide:

* `mqtt-host` - the host of the MQTT server.  In my case, this is just the IP addres of my Brewblox server
* `block-name` - the block name of the digital actuator you created above
* `homebridge-host` - the IP or FQDN of the Homebridge server
* `homebridge-port` - the port that the Homebridge server runs on
* `homebridge-auth-code` - the auth code of the Homebridge server, retrieved from the Homebridge server homepage
* `homebridge-device` - the name of the Homebridge device / swtich that will be controlled by the digital actuator block
* `service` - the name of the Brewblox service that contains the block-name

### Sample docker-compose entry

To add the setup to your docker-compose, a sample entry looks like this:

```
  boil-heating-element:
    image: ghcr.io/jmgasper/brewblox-homebridge:develop
    privileged: true
    restart: unless-stopped
    command: --port 5002 --mqtt-host=192.168.1.36 --block-name="Boil Heating Element" --homebridge-host="192.168.1.158" --homebridge-port=51887 --homebridge-auth-code="123-45-678" --homebridge-device="Brew Elements left" --service="brew-room"
    volumes:
    - type: bind
      source: /etc/localtime
      target: /etc/localtime
      read_only: true
```
