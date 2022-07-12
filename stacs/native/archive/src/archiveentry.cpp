/**
 * @file archivereader.cpp
 * @author Peter Adkins
 * @date 2022-07-02
 */

#include "archiveentry.hpp"

#include <sys/stat.h>

#include <string>

ArchiveEntry::ArchiveEntry(struct archive_entry *entry) {
    this->entry = entry;
}

ArchiveEntry::~ArchiveEntry() {
}

/**
 * Gets the filename of the archive member.
 *
 * @return std::string
 */
std::string ArchiveEntry::getFilename() {
    return archive_entry_pathname_utf8(this->entry);
}

/**
 * Gets the file size of the archive member.
 *
 * @return int64_t
 */
int64_t ArchiveEntry::getSize() {
    return archive_entry_size(this->entry);
}

/**
 * Checks whether the current archive member is a directory.
 *
 * @return bool
 */
bool ArchiveEntry::isDirectory() {
    if (S_ISDIR(archive_entry_mode(this->entry)) != 0) {
        return true;
    } else {
        return false;
    }
}
