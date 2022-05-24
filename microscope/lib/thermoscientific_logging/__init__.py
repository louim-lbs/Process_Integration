"""
FEI INFRA logging package

This package allows logging to circular log files in FEI INFRA log format. It is a simple wrapper
around C/C++ FEI logging library (component version FEI_LOGGING_5.1.0_REL.4095) and is not
supposed to contain any additional logic on top of it.
"""

from .logging import Severity, Category, CircularFileLogWriter
