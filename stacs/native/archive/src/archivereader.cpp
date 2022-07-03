/**
 * @file archivereader.cpp
 * @author Peter Adkins
 * @date 2022-07-02
 */

#include "archivereader.hpp"

extern "C" {
#include <archive.h>
#include <archive_entry.h>
}

const char *ArchiveError::what() const noexcept {
    return "Unable to open archive for reading\n";
}

ArchiveReader::ArchiveReader(const std::string &filename) : filename(filename) {
    this->archive = archive_read_new();

    // Enable all libarchive supported filters and formats.
    archive_read_support_filter_all(this->archive);
    archive_read_support_format_all(this->archive);

    // Attempt to open the archive.
    int result = archive_read_open_filename(this->archive, filename.c_str(), 10240);

    if (result != ARCHIVE_OK) {
        throw ArchiveError();
    }
}

ArchiveReader::~ArchiveReader() {
}

const std::string &ArchiveReader::getFilename() {
    return filename;
}
