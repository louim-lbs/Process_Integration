# Microsoft-Stage Integration Software M-SIS

M-SIS is an integration software to facilitate the acquisition of images, initially thought for tomograms.

The soft works with a two-buttons philosophy: one to set up, and one to acquire a set of images.


## Features enhancement

********** TO DO

- Improve performances
- Investigate threading

### Smaract
- **Calibrate and Set software limits** and check it to prevent breaking device cables. SA_FindReferenceMark_S()

### Microscope
- **Eucentric**. Write operation steps.
    - match filtre passe bas
    - **Pondérer** le match par la confiance.
    - Deal with smaract errors
    - IF NOT MATCHED INCREASE DWELL TIME.
    - Calculer le décallage une fois qu'il a été fait la première fois.
    - Le HAADF donne le meilleur contraste.
    - Augmenter le dwell time pour augmenter la précision.
    - Corriger le décalage de l'axe de tilt grâce à une analyse avec un déplacement horizontal de y
    - Faire se recouvrir les patchs pour moyenner les erreurs.
    - Logging
    - Check limits of displacement.
    - Centering image on particle after correction.
- Angles file
- Biner les images du match pour les rendre résistantes au bruit.

### GUI
- Button to open help/tutorial to remember acquisition settings.
- Button position with fraction of size, not with element height.






********** DONE
- OK. **Dynamical focus** for low-deep-field STEM acquisition?
- OK. **16-bits** default acquisition.
- OK. Attention aux sens et aux axes. Match function: x and y from left-up corner of the image.
- OK. Increase angle not zoom?
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

