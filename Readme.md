# Process Integration

## Features enhancement

********** TO DO

### Smaract
- **Calibrate and Set software limits** and check it to prevent breaking device cables. SA_FindReferenceMark_S()

### Microscope
- **Eucentric**. Write operation steps.
    - Attention au sens et aux axes.
    - Calculer le décallage une fois qu'il a été fait la premmière fois.
- **Dynamical focus** for low-deep-field STEM acquisition?
- **16-bits** default acquisition.

### GUI
- Button to open help/tutorial to remember acquisition settings.






********** DONE
- OK. Connection with Smaract, button OK.
- OK. Connection with microscope, button OK.
- OK. **Hold time infinite** to prevent drift effect or position changes due to a non-aligned center of mass. Instability ? → No
- OK. **N° of channel**: channelIndex (unsigned 32bit), input - Selects the channel of the selected system. The index is zero based.
- OK. **Convert angles**:
    - angle_py  → angle,   revolution
    -  10°      → +10,      0
    - -10°      → 350,     -1
- OK. **Wait a little to stabilize** or **Increase velocity** to let time to Smaract device to finish its move. Maybe an increase of speed could help. Use **SA_TARGET_STATUS** state or 5.45s to make 180°.
- OK. **Careful to the way the angles are handled**: [0, 10, ..., 340, 350, 359], [0, 10, ..., 340, 350, 359], ...
                                                     [______revolution -1______], [_______revolution 0______], ...
- OK. **Verify types of any function variable**
- OK. **Control speed**
- OK. **Improve logs** to detail positive actions.

