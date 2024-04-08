
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

For now, copy files in a directory and launch main.py with Python.

In future updates:

Install my-project with pip

```bash
  pip install msis
```

## Documentation

[Documentation](https://linktodocumentation)


## Support

For support, email louis-marie.lebas@insa-lyon.fr


## Features enhancement

** TO DO

- Improve performances
- Investigate threading

### Smaract
- **Calibrate and Set software limits** and check it to prevent breaking device

### Microscope
- **Eucentric**. Write operation steps.
    - match filtre passe bas
    - **Pondérer** le match par la confiance.
    - IF NOT MATCHED INCREASE DWELL TIME.
    - Calculer le décalage une fois qu'il a été fait la première fois.
    - Le HAADF donne le meilleur contraste.
    - Augmenter le dwell time pour augmenter la précision.
    - Corriger le décalage de l'axe de tilt grâce à une analyse avec un déplacement horizontal de y
    - Logging
    - Check limits of displacement.
    - Centering image on particle after correction.
- Angles file

### GUI
- Button to open help/tutorial to remember acquisition settings.
- Button position with fraction of size, not with element height.