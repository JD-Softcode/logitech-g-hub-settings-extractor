#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Part of this program was made with code from:
# https://github.com/gabfv/logitech-g-hub-settings-extractor
# https://pynative.com/python-sqlite-blob-insert-and-retrieve-digital-data/

import datetime
import os
import sys
import shutil
import sqlite3
import json

os.environ["TK_SILENCE_DEPRECATION"] = "1"
from tkinter import *

DEFAULT_FOLDER_LG_GHUB_SETTINGS = None


print("\n\nHi. This program will modify your G Hub preferences file to make it work with WoW Lights.")
print("Before proceeding you must prepare a World of Warcraft game profile in G Hub. Steps:")
print("\n")
print("Step : In G Hub, create a keyboard lighting profile for World of Warcraft.")
print("Step : Set the profile to use the Screen Sampler built-in lighting effect.")
print("Step : Click the \"Edit\" button to change the arrangement of the five default sampling regions.")
print("Step : Rename the default regions to be called wl11, wl12, wl13, wl14, and wl15. That's a lowercase W followed by L (for WoW Lights)")
print("Step : You need to Add a region and name it wl16. The location and size of the new region doesn't matter.")
print("Step : Add six more sampling regions named wl21, wl22, wl23, wl24, wl25, and wl26. Locations and sizes don't matter.")
print("Step : Add six more sampling regions named wl31 through wl36.")
print("Step : Close the screen sampler editor window.")
print("Step : Click on each one of the 18 regions you created and edit the keys affected by each one. See the picture included with this download.")
print("Step : Completely quit G Hub. Don't just close the window. Ensure G Hub is completely shut down (no control of your lights)")
print(" ")
confirmed = input("Confirm all steps are complete by pressing y and ENTER.  ")
if "y" not in confirmed and "Y" not in confirmed :
    print("Complete the required steps and re-run this program.")
    exit(9)

rootUI = Tk()
monitor_height = rootUI.winfo_screenheight()
monitor_width = rootUI.winfo_screenwidth()
rootUI.withdraw() # make the default UI window disappear

print("""

For systems with high-DPI screens (retina displays), enter the "apparent" resolution of your screen.
On Mac, that appears as the "Looks like" size in the Displays control panel scaling section
On Windows, that appears as the XXX in the Display control panel ZZZ section

""")

print("Detected your screen width as " + str(monitor_width))
widthScrStr = input("Enter the horizontal size (width) of your WoW game screen in pixels, or press enter to use "+str(monitor_width)+" : ")
if widthScrStr == "":
    widthScr = monitor_width
elif not widthScrStr.isdigit():
    print("That is not a valid number. Try again.")
    exit(9)
else:
    widthScr = int(widthScrStr) 
if widthScr < 640 or widthScr > 9000:
    print(str(widthScr) + " is not a valid value. Try again.")
    exit(9)


print("\nDetected your screen height as " + str(monitor_height))
heightScrStr = input("Enter the vertical size (height) of your WoW game screen in pixels, or press enter to use "+str(monitor_height)+" : ")
if heightScrStr == "":
    heightScr = monitor_height
elif not heightScrStr.isdigit():
    print("That is not a valid number. Try again.")
    exit(9)
else:
    heightScr = int(heightScrStr)   
if heightScr < 480 or heightScr > 5000:
    print(str(heightScr) + " is not a valid value. Try again.")
    exit(9)
    
print("\nUsing screen size of "+str(widthScr)+"x"+str(heightScr))

gridSize = 5
tops = {}
bottoms = {}
lefts = {}
rights = {}

for row in range(3):
    sqBot = heightScr - gridSize * (2-row)
    sqTop = sqBot - gridSize
    for col in range(6):
        sqLft = gridSize * col
        sqRit = sqLft + gridSize
        
        key = "wl" + str(row+1) + str(col+1)        
        tops[key] = sqTop/heightScr
        bottoms[key] = (heightScr-sqBot)/heightScr
        lefts[key] = sqLft/widthScr
        rights[key] = (widthScr-sqRit)/widthScr

#for s in range(18):
#   print(str(tops[s])+", "+str(bottoms[s])+", "+str(lefts[s])+", "+str(rights[s]))




if sys.platform.startswith('win'): # Windows
    DEFAULT_FOLDER_LG_GHUB_SETTINGS = os.path.expandvars('%LOCALAPPDATA%/LGHUB/') # Must end with /
elif sys.platform.startswith('darwin'): # MacOS
    DEFAULT_FOLDER_LG_GHUB_SETTINGS = os.path.expandvars('$HOME/Library/Application Support/lghub/') # Must end with /
else:
    error_message = """
ERROR: Unsupported platform
{platform}
    """
    print(error_message.format(platform=sys.platform))
    exit(1)

DEFAULT_FILENAME_SETTINGS_DB = 'settings.db'
DEFAULT_FILENAME_SETTINGS_JSON = 'wow_lights_prior.json'
DEFAULT_MODDED_FILENAME_SETTINGS_JSON = 'wow_lights_changed.json'
DEFAULT_PATH_SETTINGS_DB = DEFAULT_FOLDER_LG_GHUB_SETTINGS + DEFAULT_FILENAME_SETTINGS_DB


def make_backup(file_path):
    backup_file_path = file_path + datetime.datetime.now().strftime('.%Y-%m-%d_%H-%M-%S')
    try:
        shutil.copy(file_path, backup_file_path)
        backup_message = """
A backup of the settings.db file has been made to:
{backup_file_path}        
        """
        print(backup_message.format(backup_file_path=backup_file_path))
    except Exception as error:
        error_message = """
ERROR: Failed to make a backup of the settings.db file! From:
{source_path}
To:
{destination_path}
Since this is a critical failure, the program will quit.
Error:
{exception_message}
        """
        print(error_message.format(source_path=file_path, destination_path=backup_file_path, exception_message=error))
        exit(42)

def get_latest_id(file_path):
    sqlite_connection = 0
    try:
        sqlite_connection = sqlite3.connect(file_path)
        cursor = sqlite_connection.cursor()

        sql_get_latest_id = 'select MAX(_id) from DATA'
        cursor.execute(sql_get_latest_id)
        record = cursor.fetchall()
        latest_id = record[0][0]

        return latest_id
    except sqlite3.Error as error:
        error_message = """
ERROR: Failed to read latest id from the table inside settings.db file:
{file_path}
This program will quit.
Error:
{exception_message}
        """
        print(error_message.format(file_path=file_path, exception_message=error))
    finally:
        if sqlite_connection:
            sqlite_connection.close()


def write_to_file(data, file_path):
    # Convert binary data to proper format and write it on Hard Disk
    try:
        with open(file_path, 'wb') as file:
            file.write(data)
        print("Stored blob data into: ", file_path, "\n")
    except Exception as error:
        error_message = """
ERROR: Failed to write the following file:
{file_path}
Error:
{exception_message}
        """
        print(error_message.format(file_path=file_path, exception_message=error))


def read_blob_data(data_id, file_path):
    sqlite_connection = 0
    try:
        sqlite_connection = sqlite3.connect(file_path)
        cursor = sqlite_connection.cursor()

        sql_fetch_blob_query = """SELECT _id, FILE from DATA where _id = ?"""
        cursor.execute(sql_fetch_blob_query, (data_id,))
        record = cursor.fetchall()
        settings_file_path = DEFAULT_FOLDER_LG_GHUB_SETTINGS + DEFAULT_FILENAME_SETTINGS_JSON
        for row in record:
            print("Id = ", row[0])
            settings_data = row[1]
            write_to_file(settings_data, settings_file_path)
        cursor.close()

        return settings_file_path
    except sqlite3.Error as error:
        print("Failed to read blob data from sqlite table", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()


def convert_to_binary_data(file_path):
    try:
        with open(file_path, 'rb') as file:
            blob_data = file.read()
        return blob_data
    except Exception as error:
        error_message = """
ERROR: Failed to read the following file:
{file_path}
This program will quit.
Error:
{exception_message}
        """
        print(error_message.format(file_path=file_path, exception_message=error))
        exit(24)


def insert_blob(data_id, updated_settings_file_path, db_file_path):
    sqlite_connection = 0
    try:
        sqlite_connection = sqlite3.connect(db_file_path)
        cursor = sqlite_connection.cursor()
        sqlite_replace_blob_query = """ Replace INTO DATA
                                  (_id, _date_created, FILE) VALUES (?, ?, ?)"""

        blob = convert_to_binary_data(updated_settings_file_path)
        # Convert data into tuple format
        data_tuple = (data_id, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), blob)
        cursor.execute(sqlite_replace_blob_query, data_tuple)
        sqlite_connection.commit()
        cursor.close()
    except sqlite3.Error as error:
        print("Failed to insert blob data into sqlite table", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()
   
            
def verify_sample_regions(prefData):
    with open(prefData) as f:
        content = json.load(f)
    
        if len(content) < 10:
            print("The G Hub preferences file appears to be too short and it's not safe to continue.")
            return 9
    
        for topKey in content:
            if "lighting_effects" in topKey:
                if "screenSamplerInfo" in content[topKey]:
                    if "regionMap" in content[topKey]["screenSamplerInfo"]:
                        regions = 0
                        for region in content[topKey]["screenSamplerInfo"]["regionMap"]:
                            regions = regions + 1
                        
                        if regions == 18:
                            allGoodNames = True
                            for region in content[topKey]["screenSamplerInfo"]["regionMap"]:
                                key = content[topKey]["screenSamplerInfo"]["regionMap"][region]["name"]
                                if not(key in tops):
                                    allGoodNames = False
                            
                            if allGoodNames:
                                print("Good format of the G Hub preferences file!")
                                return 0

    print("Could not locate a lighting profile in the preferences file containing 18 screen sampler regions named wl11 to wl36")
    return 9                                    

            
def modify_sample_regions(prefData, prefDataMod):
    with open(prefData) as f:
        content = json.load(f)
    
        totalSamplerEffectsChanged = 0
        
        for topKey in content:
            if "lighting_effects" in topKey:
                if "screenSamplerInfo" in content[topKey]:
                    if "regionMap" in content[topKey]["screenSamplerInfo"]:
                        regions = 0
                        for region in content[topKey]["screenSamplerInfo"]["regionMap"]:
                            regions = regions + 1
                        if regions == 18:
                            for region in content[topKey]["screenSamplerInfo"]["regionMap"]:
                                this = content[topKey]["screenSamplerInfo"]["regionMap"][region]
                                thisName = this["name"]
                                if thisName in tops:
                                    this["top"] = tops[thisName]
                                    this["bottom"] = bottoms[thisName]
                                    this["left"] = lefts[thisName]
                                    this["right"] = rights[thisName]
                            totalSamplerEffectsChanged = totalSamplerEffectsChanged + 1
                            # don't return; allow all 18-segment screen samplers to be changed
                            
        with open(prefDataMod,'w') as j:
#       with open(prefDataMod,mode='w',encoding='utf-8') as j:
            json.dump(content,j,indent = 2,ensure_ascii=False)
            return totalSamplerEffectsChanged
    print("Encountered read or write error with the modified preferences.\n")
    return -1


if __name__ == '__main__':
    if not os.path.exists(DEFAULT_PATH_SETTINGS_DB):
        failure_to_find_settings_db = """
ERROR: The file settings.db was not found! The path below was checked:
{path}
Quitting...
        """
        print(failure_to_find_settings_db.format(path=DEFAULT_PATH_SETTINGS_DB))
        exit(10)

    print("Extracting the settings from the database...")
    latest_id = get_latest_id(DEFAULT_PATH_SETTINGS_DB)
    file_written = read_blob_data(latest_id, DEFAULT_PATH_SETTINGS_DB)
    make_backup(DEFAULT_PATH_SETTINGS_DB)
    file_modded = DEFAULT_FOLDER_LG_GHUB_SETTINGS + DEFAULT_MODDED_FILENAME_SETTINGS_JSON
    
    editError = verify_sample_regions(file_written)
    
    if editError != 0:
        print("\nNothing will be changed until this is corrected and this program is run again.")
        exit(0)
    
    print("\nChanging coordinates of the 18 screen scan regions...\n")
    
    samplesChanged = modify_sample_regions(file_written, file_modded)
    
    print("Screen sampler preset groups changed: ",samplesChanged)
    
    if samplesChanged > 0:    
        insert_blob(latest_id, file_modded, DEFAULT_PATH_SETTINGS_DB)
        print("\nThe G Hub settings have been updated. You can restart G Hub now.")
    else:
        print("\nThe G Hub settings have been left unmodified.")
        
    exit(0)
    
