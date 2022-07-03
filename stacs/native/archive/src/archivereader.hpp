/**
 * @file archivereader.hpp
 * @author Peter Adkins
 * @date 2022-07-02
 */

#pragma once
#include <pybind11/pybind11.h>

#include <iostream>
#include <string>

class ArchiveReader {
   public:
    ArchiveReader(const std::string &filename);
    ~ArchiveReader();

    ArchiveReader *enter();
    bool exit(pybind11::object exc_type,
              pybind11::object exc_value,
              pybind11::object exc_traceback);

    std::string getFilename();

   private:
    std::string filename;
    struct archive *archive;
};

struct ArchiveError : std::exception {
    const char *what() const noexcept;
};