/**
 * @file archivereader.cpp
 * @author Peter Adkins
 * @date 2022-07-02
 */

#pragma once

extern "C" {
#include <archive.h>
#include <archive_entry.h>
}

#include <string>

class ArchiveEntry {
   public:
    ArchiveEntry(struct archive_entry *entry);
    ~ArchiveEntry();

    std::string getFilename();
    int64_t getSize();
    bool isDirectory();

   private:
    struct archive_entry *entry;
};
