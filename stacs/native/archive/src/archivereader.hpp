/**
 * @file archivereader.hpp
 * @author Peter Adkins
 * @date 2022-07-02
 */

#pragma once

#include <string>

class ArchiveReader {
   private:
    std::string filename;
    struct archive *archive;

   public:
    ArchiveReader(const std::string &filename);
    ~ArchiveReader();

    const std::string &getFilename();
};

struct ArchiveError : std::exception {
    const char *what() const noexcept;
};