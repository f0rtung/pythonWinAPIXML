import win32file
import time
import xml.etree.ElementTree as ET
import shutil
import os
from optparse import OptionParser


class FileHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file_handler = win32file.INVALID_HANDLE_VALUE
        self.file_content = bytes()
        self.wait_time_sec = 15
        print("FileHandler({0:s}) was created!".format(self.file_path))

    def __str__(self):
        return "FileHandler({0:s})".format(self.file_path)

    def check_file_handler_status(self):
        return self.file_handler != win32file.INVALID_HANDLE_VALUE

    def open_file_or_wait(self):
        if self.check_file_handler_status():
            return True
        while True:
            try:
                print("Try open {0:s}".format(self.__str__()))
                self.file_handler = win32file.CreateFile(self.file_path,
                                                         win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                                                         0,
                                                         None,
                                                         win32file.OPEN_ALWAYS,
                                                         win32file.FILE_ATTRIBUTE_NORMAL,
                                                         0)
                if self.check_file_handler_status():
                    print("{0:s} was opened!".format(self.__str__()))
                    return True
            except:
                pass
            print("Wait " + str(self.wait_time_sec) + " seconds...")
            time.sleep(self.wait_time_sec)

    def close_file(self):
        if self.file_handler != win32file.INVALID_HANDLE_VALUE:
            win32file.CloseHandle(self.file_handler)
            self.file_handler = win32file.INVALID_HANDLE_VALUE
            print("{0:s} was close.".format(self.__str__()))
        else:
            print("Cant close {0:s}, some error!".format(self.__str__()))

    def read_all_file(self):
        if not self.check_file_handler_status():
            return str()
        bytes_count = 1024
        count, file_content = win32file.ReadFile(self.file_handler, bytes_count)
        while file_content:
            self.file_content += file_content
            count, file_content = win32file.ReadFile(self.file_handler, bytes_count)
        return self.file_content.decode('utf-8')

    def write_data(self, new_xml_data):
        if not self.check_file_handler_status():
            return False
        win32file.SetFilePointer(self.file_handler, 0, win32file.FILE_BEGIN)
        win32file.SetEndOfFile(self.file_handler)
        errCode, nBytesWritten = win32file.WriteFile(self.file_handler, new_xml_data)
        return nBytesWritten == len(new_xml_data)


class Folder:
    def __init__(self, folder_path):
        self.folder_path = folder_path

    def __str__(self):
        return self.folder_path

    def exists(self):
        return os.path.exists(self.folder_path)

    def delete_folder(self):
        try:
            shutil.rmtree(self.folder_path)
            print("Folder {0:s} was deleted!".format(self.folder_path))
            return True
        except:
            print("Cant delete folder {0:s}, some error!".format(self.folder_path))
            return False

parser = OptionParser()
parser.add_option("-f", "--file", dest="FileWithFolders", help="File with folder for delete.")
parser.add_option("-d", "--delfolder", dest="FolderForDelete", help="Folder which need to delete")
(options, args) = parser.parse_args()

if not options.FileWithFolders:
    print("Invald arguments!")
    exit(-1)
else:
    print("-f (file with folders): {0:s}".format(options.FileWithFolders))
    print("-d (folder which need to delete): {0:s}".format( "empty" if not options.FolderForDelete else options.FolderForDelete))

file = FileHandler(options.FileWithFolders)
if file.open_file_or_wait():
    content = file.read_all_file()
    try:
        root = ET.fromstringlist(content)
        list_of_folders = [Folder(folder.text) for folder in root.iter('folder')]
        list_of_bad_folders = []
        for folder in list_of_folders:
            if not folder.exists(): continue
            if not folder.delete_folder():
                list_of_bad_folders.append(folder)

        root = ET.Element('folders_for_delete')
        for folder in list_of_bad_folders:
            folder_tmp = ET.SubElement(root, 'folder')
            folder_tmp.text = str(folder)
    except ET.ParseError:
        root = ET.Element('folders_for_delete')
    if options.FolderForDelete:
        folder = ET.SubElement(root, 'folder')
        folder.text = options.FolderForDelete
    if file.write_data(ET.tostring(root)):
        file.close_file()