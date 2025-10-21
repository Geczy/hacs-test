# Free Sleep Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A first-class Home Assistant custom component for controlling your jailbroken Free Sleep Pod locally. This integration provides complete control of your pod without requiring internet access.

## Features

### Climate Control (2 Entities)

- **Left and Right Climate Entities** - Full temperature control for both sides
- HVAC modes: Off, Heat/Cool
- Temperature range: 55-110°F
- Real-time current and target temperature
- Away mode support

### Adjustable Base Control (1 Cover Entity)

- **Native Cover Entity** for intuitive base control
- Position control (0-100% derived from head angle)
- Tilt control (derived from feet angle)
- Preset positions: flat, sleep, relax, zero_gravity, anti_snore
- Moving state tracking
- Open/close/stop commands

### Sensors (12+ Entities)

- **Water Level** - Percentage calculated from sensor data
- **Room Climate** - Temperature and humidity
- **LED Brightness** - Current brightness level
- **Per-Side Status** - Current temp, target temp, time remaining
- **Biometrics** (when enabled) - Heart rate, HRV, breathing rate for both sides

### Binary Sensors (7 Entities)

- Water level OK status
- Priming active status
- Prime notification pending
- Base moving status
- Pod power status (left/right)
- Alarm vibrating status (left/right)

### Controls

- **Switches** - Power control for each side, link both sides
- **Numbers** - LED brightness, temperature controls, base position angles
- **Buttons** - Prime pod, snooze/dismiss alarms, stop base movement

### Advanced Services

- `free_sleep.set_schedule` - Update temperature/alarm schedules
- `free_sleep.set_alarm` - Configure alarms
- `free_sleep.set_base_position` - Direct head/feet angle control
- `free_sleep.set_base_preset` - Apply preset positions
- `free_sleep.enable_away_mode` - Enable away mode
- `free_sleep.disable_away_mode` - Disable away mode
- `free_sleep.prime_pod` - Manual priming

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/Geczy/hacs-test`
6. Select category "Integration"
7. Click "Add"
8. Find "Free Sleep" in the integration list
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/free_sleep` directory to your Home Assistant `config/custom_components` directory
2. Restart Home Assistant

## Configuration

### Setup via UI

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Free Sleep"
4. Enter your pod's IP address or hostname (e.g., `http://192.168.1.100:3000` or just `192.168.1.100`)
5. Click **Submit**

The integration will automatically discover and create all available entities.

### Finding Your Pod's IP Address

You can find your pod's IP address by:

1. Checking your router's DHCP client list
2. Using a network scanner app on your phone
3. Checking the pod's web interface if you've already accessed it

## Usage Examples

### Basic Automation - Bedtime Routine

```yaml
automation:
  - alias: "Bedtime - Cool Pod"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.free_sleep_pod_left_side
        data:
          temperature: 68
      - service: climate.turn_on
        target:
          entity_id: climate.free_sleep_pod_left_side
```

### Set Base to Reading Position

```yaml
automation:
  - alias: "Evening Reading Position"
    trigger:
      - platform: time
        at: "20:00:00"
    action:
      - service: free_sleep.set_base_preset
        data:
          preset: "relax"
```

### Temperature Based on Time

```yaml
automation:
  - alias: "Night Temperature Schedule"
    trigger:
      - platform: time
        at: "22:00:00"
      - platform: time
        at: "02:00:00"
      - platform: time
        at: "06:00:00"
    action:
      - choose:
          - conditions:
              - condition: time
                after: "22:00:00"
                before: "02:00:00"
            sequence:
              - service: climate.set_temperature
                target:
                  entity_id: climate.free_sleep_pod_left_side
                data:
                  temperature: 72
          - conditions:
              - condition: time
                after: "02:00:00"
                before: "06:00:00"
            sequence:
              - service: climate.set_temperature
                target:
                  entity_id: climate.free_sleep_pod_left_side
                data:
                  temperature: 65
          - conditions:
              - condition: time
                after: "06:00:00"
            sequence:
              - service: climate.set_temperature
                target:
                  entity_id: climate.free_sleep_pod_left_side
                data:
                  temperature: 78
```

### Low Water Level Notification

```yaml
automation:
  - alias: "Low Water Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.free_sleep_pod_water_level
        below: 20
    action:
      - service: notify.mobile_app
        data:
          title: "Pod Water Low"
          message: "Water level is below 20%. Time to refill!"
```

### Voice Control Examples

Once set up, you can use voice assistants:

- "Alexa, set the bedroom temperature to 70 degrees" (if climate entity is exposed)
- "Hey Google, turn on the left pod"
- "Alexa, set the bed to flat position" (using cover entity)

## Dashboard Cards

### Climate Card Example

```yaml
type: thermostat
entity: climate.free_sleep_pod_left_side
name: Left Side Temperature
```

### Base Control Card

```yaml
type: entities
entities:
  - entity: cover.free_sleep_pod_adjustable_base
    name: Adjustable Base
  - entity: number.free_sleep_pod_base_head_angle
    name: Head Angle
  - entity: number.free_sleep_pod_base_feet_angle
    name: Feet Angle
  - entity: button.free_sleep_pod_stop_base_movement
    name: Stop Movement
```

### Sensor Dashboard

```yaml
type: vertical-stack
cards:
  - type: horizontal-stack
    cards:
      - type: gauge
        entity: sensor.free_sleep_pod_water_level
        name: Water Level
        min: 0
        max: 100
        severity:
          red: 0
          yellow: 30
          green: 60
      - type: sensor
        entity: sensor.free_sleep_pod_room_temperature
        name: Room Temp
  - type: horizontal-stack
    cards:
      - type: sensor
        entity: sensor.free_sleep_pod_heart_rate_left
        name: Heart Rate Left
        icon: mdi:heart-pulse
      - type: sensor
        entity: sensor.free_sleep_pod_heart_rate_right
        name: Heart Rate Right
        icon: mdi:heart-pulse
```

## Troubleshooting

### Integration Not Discovering Pod

- Ensure your pod is on the same network as Home Assistant
- Verify you can access the pod's web interface at `http://POD_IP:3000`
- Check that the Free Sleep server is running on the pod
- Try using the full URL including `http://` and port `:3000`

### Entities Not Updating

- The integration polls every 5 seconds for device status
- Biometric sensors require biometrics to be enabled on the pod
- Base control entities only appear if an adjustable base is detected

### Away Mode Issues

- When away mode is enabled for a side, temperature changes are blocked
- You can still turn the side off while in away mode
- Use the `free_sleep.disable_away_mode` service to re-enable control

### Biometric Sensors Showing "Unknown"

- Biometrics must be enabled on the pod first
- Run: `sh /home/dac/free-sleep/scripts/enable_biometrics.sh` on the pod
- Scheduled power on/off times must be configured
- Daily priming must be enabled

## Requirements

- Home Assistant 2024.1.0 or newer
- Free Sleep Pod (jailbroken and running Free Sleep server)
- Pod must be accessible on your local network

## Support

For issues, questions, or feature requests:

- Join the [Discord community](https://discord.gg/JpArXnBgEj)
- Open an issue on [GitHub](https://github.com/throwaway31265/issues)

## Credits

Built for the Free Sleep project - an open-source solution for local control of 8 Sleep pods.

## License

This integration is released under the same license as the Free Sleep project.
