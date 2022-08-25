/**
 * @file archivereader.hpp
 * @author Peter Adkins
 * @date 2022-07-02
 */

#pragma once
#include <pybind11/pybind11.h>

#include <iostream>
#include <string>

const int CHUNK_SIZE = 10240;

class ArchiveEntry;

class ArchiveReader {
   public:
    ArchiveReader(const std::string &filename);
    ~ArchiveReader();

    ArchiveReader *enter();
    bool exit(pybind11::object exc_type,
              pybind11::object exc_value,
              pybind11::object exc_traceback);

    pybind11::bytes read();
    ArchiveEntry next();
    ArchiveReader *iter();
    std::string getFilename();

   private:
    std::vector<char> chunk;
    std::string filename;
    struct archive *archive;
    struct archive_entry *entry;
};

struct ArchiveError : std::exception {
    const char *what() const noexcept;
};
