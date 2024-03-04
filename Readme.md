
# M-SIS: Microsoft-Stage Integration Software

**fast, easy, robust**

M-SIS facilitates the acquisition of tomogram/tilt series with a two-buttons philosophy:
- One button to set up;
- One button to start automated acquisition.

Works for now with ThermoFisher microscopes running Autoscript and Smaract MCS-3D controllers. 

## Features

- Auto eucentric setting, user-independent
- Auto tomogram acquisition:
    - No manual beam correction
    - No manual focus correction
    - No manual displacement correction
- Simultaneous multi-modes acquisition: SE, BF, DF, HAADF
## Authors

- [@louis-marie.lebas](https://github.com/louim-lbs)


## Acknowledgements

 - [INSA de Lyon](https://www.insa-lyon.fr/)
 - [Laboratoire Mateis](https://mateis.insa-lyon.fr/)
 - [Agence Nationale de la Recherche](https://anr.fr/)
 
## Appendix

Any additional information goes here


## Screenshots

![MSIS Screenshot](https://github.com/louim-lbs/Process_Integration/blob/05df0187577cdba482f09bd7af7de732db466166/MSIS.png)


## Roadmap

- Asynchronous communication for microscope functions


## License

[MIT](https://choosealicense.com/licenses/mit/)


## Installation

For now, copy files in a directory and lauch main.py with Python.

In future updates:

Install my-project with pip

```bash
  pip install msis
```

## Documentation

[Documentation](https://linktodocumentation)


## Support

For support, email louis-marie.lebas@insa-lyon.fr


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
    - Calculer le décalage une fois qu'il a été fait la première fois.
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

