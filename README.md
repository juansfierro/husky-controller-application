# husky-controller-application

## How To Run
Install the required pip packages in `requirements.txt`.

Run `app.py`

## Connecting To The Robot Using Rosbridge
1. Enter the IP address and port of the Rosbridge server. By default, the Rosbridge server WebSocket is opened on port `9090`.
2. Press the "Connect" button and wait for confirmation that the connection was successful.
3. If the camera feed does not start automatically, press the "Restart" button and wait a few seconds for the live feed to start.

## Driving The Robot
Use the arrow keys to control the robot.
  - `Up` - Forward
  - `Down` - Backward
  - `Left` - Rotate left
  - `Right` - Rotate right
  - `Spacebar` - Stop

Note: This application was developed for the Clearpath A200 Husky, which uses a differential drive.

### Adjusting The Speed
Change the values for linear and angular velocity by a step interval:
  - `W` - Increase linear speed (m/s)
  - `S` - Decrease linear speed (m/s)
  - `Q` - Increase angular speed (rad/s)
  - `A` - Decrease angular speed (rad/s)

The interval size can be set between 0.01 and 1.00.

## Troubleshooting
1. Robot continues moving after disconnecting from Rosbridge server
   -  Verify that the clocks on the Husky's PC and SBC are synchronized and set to the current time. Verify, that your machine also has the current time. The Husky's PC and the secondary computer use Chrony to sync their clocks. To reconfigure the NTP, follow the steps in [Clearpath's documentation](https://docs.clearpathrobotics.com/docs/ros/networking/ntp/) and apply the changes.
2. Could not open UDP stream on port XXXX
   - If the camera stream does not start upon pressing the "Restart" button, verify that a camera is connected to the SBC and that it is transmitting video.
