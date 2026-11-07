// B01 ABI probe only: no Qt, disks, installer job or system mutation.
#include <pybind11/embed.h>
namespace py = pybind11;
PYBIND11_EMBEDDED_MODULE(toddy_fixture, module) {
    module.def("identity", []() { return "toddy-native-pybind-fixture"; });
}
int main() {
    py::scoped_interpreter interpreter{};
    py::exec("import sys, toddy_fixture\n"
             "assert sys.version_info[:2] == (3, 14)\n"
             "assert toddy_fixture.identity() == 'toddy-native-pybind-fixture'\n");
    return 0;
}
