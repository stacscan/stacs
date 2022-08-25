/**
 * @file archive.cpp
 * @author Peter Adkins
 * @date 2022-07-02
 */

#include <pybind11/pybind11.h>

#include "archiveentry.cpp"
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
        .def("__iter__", &ArchiveReader::iter)
        .def("__next__", &ArchiveReader::next)
        .def("read", &ArchiveReader::read)
        .doc() = "An interface to read archive contents (via libarchive)";

    py::class_<ArchiveEntry>(module, "ArchiveEntry")
        .def_property_readonly("filename", &ArchiveEntry::getFilename)
        .def_property_readonly("isdir", &ArchiveEntry::isDirectory)
        .def_property_readonly("size", &ArchiveEntry::getSize)
        .doc() = "Represents a member of an Archive";

    py::register_exception<ArchiveError>(module, "ArchiveError");
}
