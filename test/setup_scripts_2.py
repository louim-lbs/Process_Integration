import numpy
import distutils.core
import Cython.Build
distutils.core.setup(
    ext_modules = Cython.Build.cythonize("scripts_2_cython.pyx"),
    include_dirs=[numpy.get_include()])

# python setup_scripts_2.py build_ext --inplace