# Actron Connect - Home Assistant Integration

## Description

This is a custom component for Home Assistant to allow integration with Actron Connect devices. It is compatible with the following devices:

- Actron Standard Classic
- Actron ESP Plus
- Actron ESP Ultima
- Actron Platinum Plus
- Actron Platinum Ultima

It is not compatible with Actron Neo or Que devices.

## Features

This integration relies on a combination of local polling of the device and a connection to the Actron Connect cloud service to provide its functionality.

Via local polling to the device itself:

- On/off status
- Inside temperature
- Target temperature
- AC mode (cool, heat, fan only, auto)
- Compressor activity (heating, cooling, idle)
- Fan speed (low, medium, high)

Via the Actron Connect cloud service:

- General device information
- Automatic zone configuration, including zone names
- Turn device on or off
- Turn individual zones on or off
- Set AC mode (cool, heat, fan only, auto)
- Set fan speed (low, medium, high)

The integration uses the standard `climate` entity type, which is compatible with the built-in `Thermostat` dashboard card. Zone information is not available on the `Thermostat` card, but can be accessed and controlled via the standard `Switch` entities the integration exposes.

![Dashboard thermostat card](./images/dashboard-with-zones.png?raw=true "Dashboard thermostat card")

## Limitations

Due to limitations with the Actron Connect API, it is currently not possible to put the device in ESP mode, or to enable continuous fan speed.

## Installation

This custom component hasn't been published yet, and therefore needs to be installed manually. To install the component, copy all the files from the `src` folder of this repository into a new `actron_connect` folder in the `/config/custom_components` folder of your Home Assistant installation. It is important that the name of the folder is `actron_connect` and is not modified.

Restart Home Assistant for the custom component to be detected and initialised.

## Device Setup

### Set up a new device:

- Once the custom is installed and Home Assistant has been restarted, go to `Settings` -> `Devices & Services` and click on `+ Add integration`.
- On the `Select brand` modal, look for `Actron Connect` and click on it
- 3 fields need to be populated:
  - **Host**: the host name or IP address of the device on your local network. Do NOT include the scheme in the field (`http://` or `https://`)
  - **Username**: your user name for the Actron Connect cloud service
  - **Password**: your password for the Actron Connect cloud service
- After submitting the form, you should be redirected to the `Integrations entries` page for the Actron Connect integration, and your device should be configured:
  ![Integration entries overview](./images/integration-entries.png?raw=true "Integration entries overview")
- If you click on the new device, you should see your device details, which would look something like this:
  ![Device information](./images/device-info.png?raw=true "Device information")

### Set up the card in the dashboard:

For visualization on a dashboard, this integration works great with the built-in `Thermostat` card.
Be mindful that the HVAC modes and fan modes from the climate entity are not displayed by default, and you would need to add them in the list of features in the thermostat card settings.

You can also view the information related to individual zones and turn them on and off with this integration, but this is not a feature that is supported by the thermostat card at this point.

To work around this, I am using a `Vertical stack` card on my dashboard.

- The first card is the `Thermostat` card, with HVAC modes and fan modes enabled
- The second card is a `Horizontal stack` card, which contains 4 `Button` cards (I have 4 zones activated on my device). After customising the names and icons, I ended up with this:

![Dashboard thermostat card](./images/dashboard-with-zones.png?raw=true "Dashboard thermostat card")

This is a bit of manual work, but well worth it.
If you want to copy my setup, here is the yaml for it. Note that you will need to change then entity IDs for this to work. You can also customize the zone name and icon to your liking.

```yaml
type: vertical-stack
cards:
  - type: thermostat
    entity: climate.aconnect6827193ea688_climate
    features:
      - type: climate-hvac-modes
      - style: icons
        type: climate-fan-modes
    name: Air Conditioner
  - type: horizontal-stack
    cards:
      - show_name: true
        show_icon: true
        type: button
        entity: switch.aconnect6827193ea688_zone_master_bed
        name: Master Bed
        icon: mdi:bed-queen
      - show_name: true
        show_icon: true
        type: button
        entity: switch.aconnect6827193ea688_zone_kids_rooms
        name: Kids Rooms
        icon: mdi:bunk-bed
      - show_name: true
        show_icon: true
        type: button
        entity: switch.aconnect6827193ea688_zone_living_room
        name: Living Room
        icon: mdi:sofa
      - show_name: true
        show_icon: true
        type: button
        entity: switch.aconnect6827193ea688_zone_studies
        name: Studies
        icon: mdi:desk-lamp
```

## Uninstallation

To remove the integration from Home Assistant:

- Go to `Settings` -> `Devices & Services`
- Click on the `Actron Connect` integration
- In the list of integration entries, click on the 3 vertical dots in the top-right corner, and click on `Delete`. After confirming, this will delete all the entities for this device
- If you have more devices integrated, repeat the step above for all devices
- Delete the `actron_connect` folder in the `/config/custom_components` folder of your Home Assistant installation
- Restart Home Assistant

## Future development

- The integration does not have a logo yet, but this is being worked on

- This integration has only been tested with one device so far, so I am not comfortable releasing it to the Home Assistant integration store yet. This will be done once some feedback has been received by more users on a variety of devices

- The `Thermostat` card does not currently support turning the device on and off other than by using the AC modes. It also doesn't support turning individual zones on and off. The next step is to develop a custom card that supports those features, but for now the workaround is to combine multiple cards, as outlined in the `Device Setup` section of this document
