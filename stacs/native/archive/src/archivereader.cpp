/**
 * @file archivereader.cpp
 * @author Peter Adkins
 * @date 2022-07-02
 */

#include "archivereader.hpp"

#include "archiveentry.hpp"

extern "C" {
#include <archive.h>
#include <archive_entry.h>
}

const char *ArchiveError::what() const noexcept {
    return "Unable to open archive for reading\n";
}

ArchiveReader::ArchiveReader(const std::string &filename) : filename(filename) {
}

ArchiveReader::~ArchiveReader() {
}

ArchiveReader *ArchiveReader::iter() {
    return this;
}

/**
 * Gets the filename of the currently open file.
 *
 * @return std::string
 */
std::string ArchiveReader::getFilename() {
    return this->filename;
}

/**
 * Reads the currently selected archive member into a buffer, returning the
 * number of bytes read. 0 will be returned when no more data is available.
 *
 * @return int
 */
pybind11::bytes ArchiveReader::read() {
    std::vector<char> chunk;
    chunk.resize(CHUNK_SIZE);

    int result = archive_read_data(this->archive,
                                   chunk.data(),
                                   chunk.size());

    if (result < 0) {
        throw ArchiveError();
    }

    return pybind11::bytes(chunk.data(), result);
}

/**
 * Find and return the next member in the archive.
 *
 * @return ArchiveEntry
 */
ArchiveEntry ArchiveReader::next() {
    int result = archive_read_next_header(this->archive, &this->entry);

    if (result == ARCHIVE_OK) {
        return ArchiveEntry(this->entry);
    }
    if (result == ARCHIVE_EOF) {
        throw pybind11::stop_iteration();
    }

    throw ArchiveError();
}

/**
 * Loads an archive on Python Context Manager enter.
 *
 * @return ArchiveReader*
 */
ArchiveReader *ArchiveReader::enter() {
    this->archive = archive_read_new();

    // Enable all libarchive supported filters and formats.
    archive_read_support_filter_all(this->archive);
    archive_read_support_format_all(this->archive);

    // Attempt to open the archive.
    int result = archive_read_open_filename(this->archive,
                                            this->filename.c_str(),
                                            10240);

    if (result != ARCHIVE_OK) {
        throw ArchiveError();
    }

    return this;
}

/**
 * Cleans up the open archive on Python Context Manager exit.
 *
 * @return true
 */
bool ArchiveReader::exit(pybind11::object exc_type,
                         pybind11::object exc_value,
                         pybind11::object exc_traceback) {
    int result = archive_read_free(this->archive);

    if (result == ARCHIVE_OK) {
        return true;
    }

    return false;
}
