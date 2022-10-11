#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Part of WoW Lights from JD*Softcode      http://www.jdsoftcode.net      Copyright 2022
APP_VERSION = 0.1
# Part of this program was made with code from:
# https://github.com/gabfv/logitech-g-hub-settings-extractor
# https://pynative.com/python-sqlite-blob-insert-and-retrieve-digital-data/
# Released under the terms of the MIT Licence.

import datetime
import os
import sys
import shutil
import sqlite3
import json

os.environ["TK_SILENCE_DEPRECATION"] = "1"
from tkinter import *

DEFAULT_FOLDER_LG_GHUB_SETTINGS = None

if sys.platform.startswith('win'): # Windows
    DEFAULT_FOLDER_LG_GHUB_SETTINGS = os.path.expandvars('%LOCALAPPDATA%\LGHUB\')
elif sys.platform.startswith('darwin'): # MacOS
    DEFAULT_FOLDER_LG_GHUB_SETTINGS = os.path.expandvars('$HOME/Library/Application Support/lghub/')
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
A backup of the G Hub settings.db file has been made to:
{backup_file_path}        
        """
        print(backup_message.format(backup_file_path=backup_file_path))
    except Exception as error:
        error_message = """
ERROR: Failed to make a backup of the settings.db file! From:
{source_path}
To:
{destination_path}
Error:
{exception_message}

Since this is a critical failure, the program will quit.
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
Error:
{exception_message}

The G Hub settings have been left unmodified.
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
            print("The G Hub preferences file appears to be too short. To be safe, we'll stop here.")
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

    print("Could not locate a lighting profile in the G Hub preferences containing 18 screen sampler regions named wl11 to wl36")
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
                            # continue the loop changing all 18-segment screen samplers with the correct names

        # After changing everything, create a file with the modified preferences:                            
        with open( prefDataMod, 'w' ) as j:
        # with open( prefDataMod, mode='w', encoding='utf-8' ) as j:
            json.dump( content, j, indent = 2, ensure_ascii=False )
            return totalSamplerEffectsChanged
    print("Encountered a read or write error with the editable preference files.\n")
    return -1


if __name__ == '__main__':
    if not os.path.exists(DEFAULT_PATH_SETTINGS_DB):
        failure_to_find_settings_db = """
ERROR: The file settings.db was not found! The path below was checked:
{path}
The G Hub settings have been left unmodified.
        """
        print(failure_to_find_settings_db.format(path=DEFAULT_PATH_SETTINGS_DB))
        exit(10)

    print("\nWoW Lights G Hub Settings, version ", APP_VERSION)
    print("""
    
Hi. This program will modify your G Hub preferences file to make it work with WoW Lights.
Before proceeding you must prepare a World of Warcraft game profile in G Hub following these steps:

Step 1: In G Hub, create a keyboard lighting profile for World of Warcraft.
Step 2: Set the profile to use the Screen Sampler built-in lighting effect.
Step 3: Click the \"Edit\" button to edit the five default sampling regions.
Step 4: Rename the default regions to be called wl11, wl12, wl13, wl14, and wl15. That's a lowercase W followed by L (for 
        WoW Lights)
Step 5: You need to Add a region and name it wl16. The location and size of the new region doesn't matter.
Step 6: Add six more sampling regions named wl21, wl22, wl23, wl24, wl25, and wl26. Locations and sizes don't matter.
Step 7: Add six more sampling regions named wl31 through wl36.
Step 8: Close the screen sampler editor window.
Step 9: Assign appropriate keys to each of the 18 regions you created. See the picture in the instructions sheet.
Step 10: Completely quit G Hub. Don't just close the window!
         Ensure G Hub is completely shut down (no control of your lights)
    """)

    confirmed = input("Confirm all steps are complete by pressing y and ENTER.  ")
    if "y" not in confirmed and "Y" not in confirmed :
        print("\nComplete the required steps and re-run this program.\n")
        exit(9)

    rootUI = Tk()
    monitor_height = rootUI.winfo_screenheight()
    monitor_width = rootUI.winfo_screenwidth()
    rootUI.withdraw() # make the default UI window disappear

    print("""

    For systems with high-DPI screens (retina displays), enter the "apparent" resolution of your screen.
    On Mac, that appears as the "Looks like" size in the Displays control panel scaling section.
    On Windows, that appears as the "Display resolution" in the Display control panel "Scale and layout" section.
    
    Also note, G Hub only allows sampling your main screen. You must play WoW on your main screen to use WoW Lights.

    """)

    print("Detected your screen width as ",monitor_width)
    widthScrStr = input("Enter the horizontal size (width) of your main screen in pixels, or press enter to use "+str(monitor_width)+" : ")
    if widthScrStr == "":
        widthScr = monitor_width
    elif not widthScrStr.isdigit():
        print("That is not a valid number. Try again.")
        exit(9)
    else:
        widthScr = int(widthScrStr) 
    if widthScr < 1024 or widthScr > 9000:
        print(str(widthScr) + " is not a valid value. Try again.")
        exit(9)

    print("\nDetected your screen height as ",monitor_height)
    heightScrStr = input("Enter the vertical size (height) of your main screen in pixels, or press enter to use "+str(monitor_height)+" : ")
    if heightScrStr == "":
        heightScr = monitor_height
    elif not heightScrStr.isdigit():
        print("That is not a valid number. Try again.")
        exit(9)
    else:
        heightScr = int(heightScrStr)   
    if heightScr < 768 or heightScr > 5000:
        print(str(heightScr) + " is not a valid value. Try again.")
        exit(9)
    
    print("\nUsing screen size of ", widthScr, " by ", heightScr)

    gridSize = 5 # the smallest screen area G Hub will sample, 5x5 pixels
    
    # Create collections for the sample region coordinates
    tops = {}
    bottoms = {}
    lefts = {}
    rights = {}

    # Generate the coordinates of the 6x3 screen sample regions
    hScale = 1.0 # good for Mac
    winShift = 0 # no shift for Mac
    if sys.platform.startswith('win'):
        hScale = 1.2
        winShift = 2

    for row in range(3): # 0-2
        sqBot = heightScr - gridSize * (2-row)
        sqTop = sqBot - gridSize + 1    # +1 might be for windows only
        for col in range(6): # 0-5
            sqLft = hScale * gridSize * col + winShift
            #sqRit = sqLft + gridSize
            sqRit = hScale * (gridSize * (col + 1) - 1) + winShift
            key = "wl" + str(row+1) + str(col+1)        
            tops[key] = sqTop / heightScr
            bottoms[key] = ( heightScr - sqBot ) / heightScr
            lefts[key] = sqLft / widthScr
            rights[key] = ( widthScr - sqRit ) / widthScr
    #for s in range(18):
    #   print(str(tops[s])+", "+str(bottoms[s])+", "+str(lefts[s])+", "+str(rights[s]))

    print("Extracting the existing settings from the database...")
    latest_id = get_latest_id(DEFAULT_PATH_SETTINGS_DB)
    file_written = read_blob_data(latest_id, DEFAULT_PATH_SETTINGS_DB)
    file_modded = DEFAULT_FOLDER_LG_GHUB_SETTINGS + DEFAULT_MODDED_FILENAME_SETTINGS_JSON
    make_backup(DEFAULT_PATH_SETTINGS_DB)
    
    editError = verify_sample_regions(file_written)
    
    if editError != 0:
        print("\nNothing will be changed until this is corrected and this program is run again.")
        exit(editError)
    
    print("\nChanging coordinates of the 18 screen sampler regions...\n")
    
    samplesChanged = modify_sample_regions(file_written, file_modded)
    
    print("Number of screen sampler preset groups changed: ", samplesChanged)
    
    if samplesChanged > 0:    
        insert_blob(latest_id, file_modded, DEFAULT_PATH_SETTINGS_DB)
        print("\nThe G Hub settings have been updated. You can restart G Hub now.\n")
    else:
        print("\nThe G Hub settings have been left unmodified.\n")
        
    exit(0)
