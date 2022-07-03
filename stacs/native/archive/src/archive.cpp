/**
 * @file archive.cpp
 * @author Peter Adkins
 * @date 2022-07-02
 */

#include <pybind11/pybind11.h>

#include "archivereader.cpp"

namespace py = pybind11;

PYBIND11_MODULE(archive, module) {
    module.doc() = "STACS Native Extensions for Archives";
    module.attr("__name__") = "stacs.native.archive";

    py::class_<ArchiveReader>(module, "ArchiveReader")
        .def(py::init<const std::string &>())
        .def_property_readonly("filename", &ArchiveReader::getFilename)
        .def("__enter__", &ArchiveReader::enter)
        .def("__exit__", &ArchiveReader::exit)
        .doc() = "An interface to read archive contents (via libarchive)";

    py::register_exception<ArchiveError>(module, "ArchiveError");
}
