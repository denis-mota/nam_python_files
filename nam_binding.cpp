#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include "../NeuralAmpModelerCore/NAM/dsp.h"
#include "../NeuralAmpModelerCore/NAM/get_dsp.h"
#include "../AudioDSPTools/dsp/ImpulseResponse.h"
#include "../AudioDSPTools/dsp/wav.h"
#include "../AudioDSPTools/dsp/dsp.h"

namespace py = pybind11;

class PyNAMProcessor {
public:
    PyNAMProcessor(const std::string& model_path) {
        dsp = nam::get_dsp(model_path);
        if (!dsp) {
            throw std::runtime_error("Failed to load NAM model");
        }
    }

    py::array_t<double> process(py::array_t<double> input) {
        py::buffer_info buf = input.request();
        double* input_ptr = static_cast<double*>(buf.ptr);
        int num_samples = static_cast<int>(buf.size);

        auto output = py::array_t<double>(num_samples);
        py::buffer_info out_buf = output.request();
        double* output_ptr = static_cast<double*>(out_buf.ptr);

        dsp->process(input_ptr, output_ptr, num_samples);
        return output;
    }

    void reset(double sample_rate, int buffer_size) {
        dsp->Reset(sample_rate, buffer_size);
        dsp->prewarm();
    }

private:
    std::unique_ptr<nam::DSP> dsp;
};

class PyIRProcessor {
public:
    PyIRProcessor(const std::string& ir_path, double sample_rate) {
        ir = std::make_unique<dsp::ImpulseResponse>(ir_path.c_str(), sample_rate);
        if (ir->GetWavState() != dsp::wav::LoadReturnCode::SUCCESS) {
            throw std::runtime_error("Failed to load IR file");
        }
    }

    py::array_t<double> process(py::array_t<double> input) {
        py::buffer_info buf = input.request();
        double* input_ptr = static_cast<double*>(buf.ptr);
        int num_samples = static_cast<int>(buf.size);

        // Create input buffer for IR processing
        double* input_buffer[1] = { input_ptr };

        // Process through IR
        double** output_buffer = ir->Process(input_buffer, 1, num_samples);

        // Create output numpy array
        auto output = py::array_t<double>(num_samples);
        py::buffer_info out_buf = output.request();
        double* output_ptr = static_cast<double*>(out_buf.ptr);

        // Copy output data
        std::memcpy(output_ptr, output_buffer[0], num_samples * sizeof(double));

        return output;
    }

private:
    std::unique_ptr<dsp::ImpulseResponse> ir;
};

PYBIND11_MODULE(nam_binding, m) {
    py::class_<PyNAMProcessor>(m, "NAMProcessor")
        .def(py::init<const std::string&>())
        .def("process", &PyNAMProcessor::process)
        .def("reset", &PyNAMProcessor::reset);

    py::class_<PyIRProcessor>(m, "IRProcessor")
        .def(py::init<const std::string&, double>())
        .def("process", &PyIRProcessor::process);
}