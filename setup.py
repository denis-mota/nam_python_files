from setuptools import setup, Extension
import pybind11

nam_binding_module = Extension(
    'nam_binding',
    sources=[
        'nam_binding.cpp',
        '../NeuralAmpModelerCore/NAM/dsp.cpp',
        '../NeuralAmpModelerCore/NAM/get_dsp.cpp',
        '../NeuralAmpModelerCore/NAM/activations.cpp',
        '../NeuralAmpModelerCore/NAM/convnet.cpp',
        '../NeuralAmpModelerCore/NAM/lstm.cpp',
        '../NeuralAmpModelerCore/NAM/wavenet.cpp',
        '../NeuralAmpModelerCore/NAM/util.cpp',
        '../AudioDSPTools/dsp/ImpulseResponse.cpp',
        '../AudioDSPTools/dsp/wav.cpp',
        '../AudioDSPTools/dsp/dsp.cpp'
    ],
    include_dirs=[
        pybind11.get_include(),
        '../NeuralAmpModelerCore',
        '../NeuralAmpModelerCore/Dependencies/eigen',
        '../NeuralAmpModelerCore/Dependencies/nlohmann',
        '../AudioDSPTools'
    ],
    language='c++',
    extra_compile_args=['/std:c++20', '/EHsc']
)

setup(
    name='nam_binding',
    ext_modules=[nam_binding_module],
    install_requires=['pybind11>=2.10.0'],
    python_requires='>=3.8'
)