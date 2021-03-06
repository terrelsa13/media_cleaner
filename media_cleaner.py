#!/usr/bin/env python3

import urllib.request as request
import json, urllib
import traceback
import hashlib
import time
import sys
import os
from dateutil.parser import parse
from datetime import datetime,date,timedelta,timezone

# Hash password if not hashed
#if cfg.admin_password_sha1 == '':
#     cfg.admin_password_sha1=hashlib.sha1(cfg.admin_password.encode()).hexdigest()
#auth_key=''
#print('Hash:'+ cfg.admin_password_sha1)


def convert2json(rawjson):
    #return a formatted string of the python JSON object
    ezjson = json.dumps(rawjson, sort_keys=False, indent=4)
    return(ezjson)


def print2json(rawjson):
    #create a formatted string of the python JSON object
    ezjson = convert2json(rawjson)
    print(ezjson)


#emby or jellyfin?
def get_brand():
    defaultbrand='emby'
    print('0:emby\n1:jellyfin')
    brand=input('Enter number for server branding (default ' + defaultbrand + '): ')
    if (brand == ''):
        return(defaultbrand)
    elif (brand == '0'):
        return(defaultbrand)
    elif (brand == '1'):
        return('jellyfin')
    else:
        print('Invalid choice. Default to emby.')
        return(defaultbrand)


#ip address or url?
def get_url():
    defaulturl='http://localhost'
    url=input('Enter server ip or name (default ' + defaulturl + '): ')
    if (url == ''):
        return(defaulturl)
    else:
        if (url.find('://',3,7) >= 0):
            return(url)
        else:
           #print('No http:// or https:// entered.')
           url='http://' + url
           print('Assuming server ip or name is: ' + url)
           return(url)


#http or https port?
def get_port():
    defaultport='8096'
    valid_port=False
    while (valid_port == False):
        print('If you have not explicity changed this option, press enter for default.')
        print('Space for no port.')
        port=input('Enter port (default ' + defaultport + '): ')
        if (port == ''):
            valid_port=True
            return(defaultport)
        elif (port == ' '):
            valid_port=True
            return('')
        else:
            try:
                port_float=float(port)
                if ((port_float % 1) == 0):
                    port_int=int(port_float)
                    if ((int(port_int) >= 1) and (int(port_int) <= 65535)):
                        valid_port=True
                        return(str(port_int))
                    else:
                        print('\nInvalid port. Try again.\n')
                else:
                    print('\nInvalid port. Try again.\n')
            except:
                print('\nInvalid port. Try again.\n')


#base url?
def get_base(brand):
    defaultbase='emby'
    #print('If you are using emby press enter for default.')
    if (brand == defaultbase):
        print('Using "/' + defaultbase + '" as base url')
        return(defaultbase)
    else:
        print('If you have not explicity changed this option in jellyfin, press enter for default.')
        print('For example: http://example.com/<baseurl>')
        base=input('Enter base url (default /' + defaultbase + '): ')
        if (base == ''):
            return(defaultbase)
        else:
            if (base.find('/',0,1) == 0):
                return(base[1:len(base)])
            else:
                return(base)


#admin username?
def get_admin_username():
    return(input('Enter admin username: '))


#admin password?
def get_admin_password():
    #print('Plain text password used to grab access token; hashed password stored in config file.')
    print('Plain text password used to grab access token; password not stored in config file.')
    password=input('Enter admin password: ')
    return(password)


#Blacklisting or Whitelisting
def get_cleaning_behavior():
    defaultbehavior='whitelist'
    valid_behavior=False
    while (valid_behavior == False):
        print('Choose how the script will decide which libraries to delete media items from.')
        print('0 - Whitelisting media libraries; media items can be deleted from library unless library is whitelisted.')
        print('1 - Blacklisting media libraries; media items cannot be deleted from library unless library is blacklisted (aka monitored).')
        behavior=input('Choose how the script will behave. (press enter to default to whitelisting): ')
        if (behavior == ''):
            valid_behavior=True
            return(defaultbehavior)
        elif (behavior == '0'):
            valid_behavior=True
            return(defaultbehavior)
        elif (behavior == '1'):
            valid_behavior=True
            return('blacklist')
        else:
            print('\nInvalid choice. Try again.\n')
            return(defaultbehavior)


#use of hashed password removed
#hash admin password
#def get_admin_password_sha1(password):
#    #password_sha1=password #input('Enter admin password (password will be hashed in config file): ')
#    password_sha1=hashlib.sha1(password.encode()).hexdigest()
#    return(password_sha1)


#get user input needed to build the media_cleaner_config.py file
def generate_config():
    print('-----------------------------------------------------------')
    server_brand=get_brand()

    print('-----------------------------------------------------------')
    server=get_url()
    print('-----------------------------------------------------------')
    port=get_port()
    print('-----------------------------------------------------------')
    server_base=get_base(server_brand)
    if (len(port)):
        server_url=server + ':' + port + '/' + server_base
    else:
        server_url=server + '/' + server_base
    print('-----------------------------------------------------------')

    username=get_admin_username()
    print('-----------------------------------------------------------')
    password=get_admin_password()
    print('-----------------------------------------------------------')
    auth_key=get_auth_key(server_url, username, password, server_brand)

    script_behavior=get_cleaning_behavior()
    print('-----------------------------------------------------------')

    user_keys_and_bllibs, user_keys_and_wllibs=get_users_and_paths(server_url, auth_key, script_behavior)

    userkeys_list=[]
    userbllibs_list=[]
    userkeys_wllibs_list=[]
    userwllibs_list=[]

    for userkey, userbllib in user_keys_and_bllibs.items():
        userkeys_list.append(userkey)
        userbllibs_list.append(userbllib)

    for userkey, userwllib in user_keys_and_wllibs.items():
        userkeys_wllibs_list.append(userkey)
        userwllibs_list.append(userwllib)

    if (userkeys_list == userkeys_wllibs_list):
        user_keys=json.dumps(userkeys_list)
        user_bl_libs=json.dumps(userbllibs_list)
        user_wl_libs=json.dumps(userwllibs_list)
    else:
        raise ValueError('Error! User key values do not match.')

    print('-----------------------------------------------------------')

    config_file=''
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# Delete media type once it has been played x days ago\n"
    config_file += "#   0-365000000 - number of days to wait before deleting played media\n"
    config_file += "#  -1 : to disable managing specified media type\n"
    config_file += "# (-1 : default)\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "not_played_age_movie=-1\n"
    config_file += "not_played_age_episode=-1\n"
    config_file += "not_played_age_video=-1\n"
    config_file += "not_played_age_trailer=-1\n"
    config_file += "not_played_age_audio=-1\n"
    #config_file += "#----------------------------------------------------------#\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# Decide if media set as a favorite should be deleted\n"
    config_file += "# Favoriting a series, season, or network-channel will treat all child episodes as if they are favorites\n"
    config_file += "# Favoriting an artist, album-artist, or album will treat all child tracks as if they are favorites\n"
    config_file += "# Similar logic applies for other media types (movies, trailers, etc...)\n"
    config_file += "#  0 : ok to delete media items set as a favorite\n"
    config_file += "#  1 : when single user - do not delete media items when set as a favorite; when multi-user - do not delete media item when all monitored users have set it as a favorite\n"
    config_file += "#  2 : when single user - not applicable; when multi-user - do not delete media item when any monitored users have it set as a favorite\n"
    config_file += "# (1 : default)\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "keep_favorites_movie=1\n"
    config_file += "keep_favorites_episode=1\n"
    config_file += "keep_favorites_video=1\n"
    config_file += "keep_favorites_trailer=1\n"
    config_file += "keep_favorites_audio=1\n"
    #config_file += "#----------------------------------------------------------#\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# Advanced favorites configuration bitmask\n"
    config_file += "#     Requires 'keep_favorites_*=1'\n"
    config_file += "#  xxxxxxxA - keep_favorites_audio must be enabled; keep audio tracks based on if the FIRST artist listed in the track's 'artist' metadata is favorited\n"
    config_file += "#  xxxxxxBx - keep_favorites_audio must be enabled; keep audio tracks based on if the FIRST artist listed in the tracks's 'album artist' metadata is favorited\n"
    config_file += "#  xxxxxCxx - keep_favorites_audio must be enabled; keep audio tracks based on if the FIRST genre listed in the tracks's metadata is favorited\n"
    config_file += "#  xxxxDxxx - keep_favorites_audio must be enabled; keep audio tracks based on if the FIRST genre listed in the album's metadata is favorited\n"
    config_file += "#  xxxExxxx - keep_favorites_episode must be enabled; keep episode based on if the FIRST genre listed in the series' metadata is favorited\n"
    config_file += "#  xxFxxxxx - keep_favorites_movie must be enabled; keep movie based on if the FIRST genre listed in the movie's metadata is favorited\n"
    config_file += "#  xGxxxxxx - reserved...\n"
    config_file += "#  Hxxxxxxx - reserved...\n"
    config_file += "#  0 bit - disabled\n"
    config_file += "#  1 bit - enabled\n"
    config_file += "# (00000001 - default)\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "keep_favorites_advanced='00000001'\n"
    #config_file += "#----------------------------------------------------------#\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# Advanced favorites any configuration bitmask\n"
    config_file += "#     Requires matching bit in 'keep_favorites_advanced' bitmask is enabled\n"
    config_file += "#  xxxxxxxa - xxxxxxxA must be enabled; will use ANY artists listed in the track's 'artist' metadata\n"
    config_file += "#  xxxxxxbx - xxxxxxBx must be enabled; will use ANY artists listed in the track's 'album artist' metadata\n"
    config_file += "#  xxxxxcxx - xxxxxCxx must be enabled; will use ANY genres listed in the track's metadata\n"
    config_file += "#  xxxxdxxx - xxxxDxxx must be enabled; will use ANY genres listed in the album's metadata\n"
    config_file += "#  xxxexxxx - xxxExxxx must be enabled; will use ANY genres listed in the series' metadata\n"
    config_file += "#  xxfxxxxx - xxFxxxxx must be enabled; will use ANY genres listed in the movie's metadata\n"
    config_file += "#  xgxxxxxx - reserved...\n"
    config_file += "#  hxxxxxxx - reserved...\n"
    config_file += "#  0 bit - disabled\n"
    config_file += "#  1 bit - enabled\n"
    config_file += "# (00000000 - default)\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "keep_favorites_advanced_any='00000000'\n"
    #config_file += "#----------------------------------------------------------#\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# Decide how whitelists with multiple users behave\n"
    config_file += "#  0 : do not delete media item when ALL monitored users have the parent library whitelisted\n"
    config_file += "#  1 : do not delete media item when ANY monitored users have the parent library whitelisted\n"
    config_file += "# (1 : default)\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "multiuser_whitelist_movie=1\n"
    config_file += "multiuser_whitelist_episode=1\n"
    config_file += "multiuser_whitelist_video=1\n"
    config_file += "multiuser_whitelist_trailer=1\n"
    config_file += "multiuser_whitelist_audio=1\n"
    #config_file += "#----------------------------------------------------------#\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# 0 - Disable the ability to delete media (dry run mode)\n"
    config_file += "# 1 - Enable the ability to delete media\n"
    config_file += "# (0 - default)\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "remove_files=0\n"
    #config_file += "#----------------------------------------------------------#\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# CAUTION!!!   CAUTION!!!   CAUTION!!!   CAUTION!!!   CAUTION!!!\n"
    config_file += "# Do NOT enable any max_age_xyz options unless you know what you are doing\n"
    config_file += "# Use at your own risk; You alone are responsible for your actions\n"
    config_file += "# Enabling any of these options with a low value WILL DELETE THE ENTIRE LIBRARY\n"
    config_file += "# Delete media type if its creation date is x days ago; played state is ignored; value must be greater than or equal to the corresponding not_played_age_xyz\n"
    config_file += "#   0-365000000 - number of days to wait before deleting \"old\" media\n"
    config_file += "#  -1 : to disable managing max age of specified media type\n"
    config_file += "# (-1 : default)\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "max_age_movie=-1\n"
    config_file += "max_age_episode=-1\n"
    config_file += "max_age_video=-1\n"
    config_file += "max_age_trailer=-1\n"
    config_file += "max_age_audio=-1\n"
    #config_file += "#----------------------------------------------------------#\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# Decide if max age media set as a favorite should be deleted\n"
    config_file += "#  0 : ok to delete max age media items set as a favorite\n"
    config_file += "#  1 : do not delete max age media items when set as a favorite\n"
    config_file += "# (1 : default)\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "max_keep_favorites_movie=1\n"
    config_file += "max_keep_favorites_episode=1\n"
    config_file += "max_keep_favorites_video=1\n"
    config_file += "max_keep_favorites_trailer=1\n"
    config_file += "max_keep_favorites_audio=1\n"
    #config_file += "#----------------------------------------------------------#\n"
    config_file += "\n"
    config_file += "#------------DO NOT MODIFY BELOW---------------------------#\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# Server branding; chosen during setup\n"
    config_file += "#  0 - 'emby'\n"
    config_file += "#  1 - 'jellyfin'\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "server_brand='" + server_brand + "'\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# Server URL; created during setup\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "server_url='" + server_url + "'\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# Admin username; chosen during setup\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "admin_username='" + username + "'\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# Access token; requested from server during setup\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "access_token='" + auth_key + "'\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# User key(s) of account(s) to monitor media items; chosen during setup\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "user_keys='" + user_keys + "'\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    #config_file += "# Script is using whitelists or blacklists; chosen during setup\n"
    #config_file += "#----------------------------------------------------------#\n"
    #config_file += "script_behavior='" + script_behavior + "'\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# User blacklisted libraries of corresponding user account(s) to monitor media items; chosen during setup\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "user_bl_libs='" + user_bl_libs + "'\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# User whitelisted libraries of corresponding user account(s) to exclude monitoring media items; chosen during setup\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "user_wl_libs='" + user_wl_libs + "'\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# API request attempts; number of times to retry an API request\n"
    config_file += "#  delay between initial attempt and the first retry is 1 second\n"
    config_file += "#  the delay will double with each attempt after the first retry\n"
    config_file += "#  0-16 - number of retry attempts\n"
    config_file += "#  (6 : default)\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "api_request_attempts=6\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# API return limit; large libraries sometimes cannot return all of the media metadata items in a single API call\n"
    config_file += "#  This is especially true when using the max_age_xyz options; the max_age_xyz options require every item of the specified media type send its metadata\n"
    config_file += "#  1-10000 - number of media metadata items the server will return for each API call for media item metadata; ALL items will be processed regardless of this value\n"
    config_file += "#  (100 : default)\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "api_return_limit=100\n"
    config_file += "\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "# 0 - Debug messages disabled\n"
    config_file += "# 1 - Debug messages enabled\n"
    config_file += "# (0 : default)\n"
    config_file += "#----------------------------------------------------------#\n"
    config_file += "DEBUG=0\n"

    #Create config file next to the script even when cwd (Current Working Directory) is not the same
    cwd = os.getcwd()
    script_dir = os.path.dirname(__file__)
    if (script_dir == ''):
        #script must have been run from the cwd
        #set script_dir to cwd (aka this directory) to prevent error when attempting to change to '' (aka a blank directory)
        script_dir=cwd
    os.chdir(script_dir)
    f = open("media_cleaner_config.py", "w")
    f.write(config_file)
    f.close()
    os.chdir(cwd)

    print('\n\n-----------------------------------------------------------')
    print('Config file is not setup to find played media.')
    print('-----------------------------------------------------------')
    print('To find played media open media_cleaner_config.py in a text editor:')
    print('    Set \'not_played_age_movie\' to zero or a positive number')
    print('    Set \'not_played_age_episode\' to zero or a positive number')
    print('    Set \'not_played_age_video\' to zero or a positive number')
    print('    Set \'not_played_age_trailer\' to zero or a positive number')
    print('    Set \'not_played_age_audio\' to zero or a positive number')
    print('-----------------------------------------------------------')
    print('Config file is not setup to delete played media.')
    print('Config file is in dry run mode to prevent deleting media.')
    print('-----------------------------------------------------------')
    print('To delete media open media_cleaner_config.py in a text editor:')
    print('    Set \'remove_files=1\' in media_cleaner_config.py')
    print('-----------------------------------------------------------')
    print('Edit the config file and try running again.')
    print('-----------------------------------------------------------')


#api call to delete items
def delete_item(itemID):
    url=url=cfg.server_url + '/Items/' + itemID + '?api_key=' + cfg.access_token

    req = request.Request(url,method='DELETE')

    if bool(cfg.DEBUG):
        #DEBUG
        print(itemID)
        print(url)
        print(req)
    if bool(cfg.remove_files):
        try:
            request.urlopen(req)
        except Exception:
            print('generic exception: ' + traceback.format_exc())
    else:
        return


#api call to get admin account authentication token
def get_auth_key(server_url, username, password, server_brand):
    #login info
    values = {'Username' : username, 'Pw' : password}
    #DATA = urllib.parse.urlencode(values)
    #DATA = DATA.encode('ascii')
    DATA = convert2json(values)
    DATA = DATA.encode('utf-8')

    #assuming jellyfin will eventually change this
    #if (server_brand == 'emby'):
        #xAuth = 'X-Emby-Authorization'
    #else:
        #xAuth = 'X-Jellyfin-Authorization'

    headers = {'X-Emby-Authorization' : 'Emby UserId="' + username  + '", Client="media_cleaner.py", Device="Multi-User Media Cleaner", DeviceId="MUMC", Version="1.0.2", Token=""', 'Content-Type' : 'application/json'}

    req = request.Request(url=server_url + '/Users/AuthenticateByName', data=DATA, method='POST', headers=headers)

    #api call
    data=requestURL(req, False, 'get_auth_key', 3)

    return(data['AccessToken'])


#api call to get all user accounts
#then choose account this script will use to delete played media
#choosen account does NOT need to have "Allow Media Deletion From" enabled
def get_users_and_paths(server_url, auth_key, script_behavior):
    #Get all users

    req=(server_url + '/Users?api_key=' + auth_key)

    #api call
    data=requestURL(req, False, 'get_users', 3)

    #define empty userId dictionary
    userId_dict={}
    #define empty monitored library dictionary
    userId_lib_dict={}
    #define empty whitelisted library dictionary
    userId_wllib_dict={}
    #define empty userId set
    userId_set=set()

    stop_loop=False
    single_user=False
    one_user_selected = False
    while (stop_loop == False):
        i=0
        if (len(data) > 1):
            for user in data:
                if not (user['Id'] in userId_set):
                    print(str(i) +' - '+ user['Name'] + ' - ' + user['Id'])
                    userId_dict[i]=user['Id']
                else:
                    #show blank entry
                    print(str(i) + ' - ')
                i += 1
        else:
            single_user=True
            for user in data:
                userId_dict[i]=user['Id']

        print('')

        if ((i == 0) and (single_user == True)):
            user_number='0'
        elif ((i >= 1) and (one_user_selected == False)):
            user_number=input('Enter number of user to monitor: ')
            print('')
        else: #((i >= 1) and (one_user_selected == True)):
            print('Monitoring multiple users is possible.')
            #print('When multiple users are selected; the user with the longest played since time will determine if media is deleted.')
            print('When multiple users are selected; the user with the oldest last played time will determine if media is deleted.')
            user_number=input('Enter number of user to monitor; leave blank when finished: ')
            print('')

        try:
            if ((user_number == '0') and (single_user == True)):
                stop_loop=True
                one_user_selected=True
                user_number_int=int(user_number)
                userId_set.add(userId_dict[user_number_int])

                if (script_behavior == 'blacklist'):
                    message='Enter number of library folder to blacklist (aka monitor) for the selected user.\nMedia in blacklisted library folder(s) will be monitored for deletion.'
                    userId_lib_dict[userId_dict[user_number_int]]=list_library_folders(server_url, auth_key, message, True)
                    userId_wllib_dict[userId_dict[user_number_int]]=''
                else:
                    userId_lib_dict[userId_dict[user_number_int]]=''
                    message='Enter number of library folder to whitelist for the selcted user.\nMedia in whitelisted library folder(s) will be excluded from deletion.'
                    userId_wllib_dict[userId_dict[user_number_int]]=list_library_folders(server_url, auth_key, message, False)

            elif ((user_number == '') and not (len(userId_set) == 0)):
                stop_loop=True
                print('')
            elif ((user_number == '') and (len(userId_set) == 0)):
                print('\nMust select at least one user. Try again.\n')
            elif not (user_number == ''):
                user_number_float=float(user_number)
                if ((user_number_float % 1) == 0):
                    user_number_int=int(user_number_float)
                if ((user_number_int >= 0) and (user_number_int < i)):
                    one_user_selected=True
                    userId_set.add(userId_dict[user_number_int])

                    if (script_behavior == 'blacklist'):
                        message='Enter number of library folder to blacklist (aka monitor) for the selected user.\nMedia in blacklisted library folder(s) will be monitored for deletion.'
                        userId_lib_dict[userId_dict[user_number_int]]=list_library_folders(server_url, auth_key, message, True)
                        userId_wllib_dict[userId_dict[user_number_int]]=''
                    else:
                        userId_lib_dict[userId_dict[user_number_int]]=''
                        message='Enter number of library folder to whitelist for the selcted user.\nMedia in whitelisted library folder(s) will be excluded from deletion.'
                        userId_wllib_dict[userId_dict[user_number_int]]=list_library_folders(server_url, auth_key, message, False)

                    if (len(userId_set) >= i):
                        stop_loop=True
                    else:
                        stop_loop=False
                else:
                    print('\nInvalid value. Try again.\n')
            else:
                print('\nInvalid value. Try again.\n')
        except:
            print('\nInvalid value. Try again.\n')

    return(userId_lib_dict, userId_wllib_dict)


#api call to get library folders
#then choose which folders to whitelist
def list_library_folders(server_url, auth_key, infotext, mandatory):
    #get all library paths

    req=(server_url + '/Library/VirtualFolders?api_key=' + auth_key)

    #api call
    data = requestURL(req, False, 'get_libraries', 3)

    #define empty dictionary
    libraryfolders_dict={}
    #define empty set
    libraryfolders_set=set()

    stop_loop=False
    first_run=True
    while (stop_loop == False):
        i=0
        for path in data:
            for subpath in range(len(path['LibraryOptions']['PathInfos'])):
                if ('NetworkPath' in path['LibraryOptions']['PathInfos'][subpath]):
                    if not (path['LibraryOptions']['PathInfos'][subpath]['NetworkPath'] in libraryfolders_set):
                        print(str(i) + ' - ' + path['LibraryOptions']['PathInfos'][subpath]['Path'] + ' - (' + path['LibraryOptions']['PathInfos'][subpath]['NetworkPath'] +')')
                        libraryfolders_dict[i]=path['LibraryOptions']['PathInfos'][subpath]['NetworkPath']
                    else:
                        #show blank entry
                        print(str(i) + ' - ')
                else: #('Path' in path['LibraryOptions']['PathInfos'][subpath]):
                    if not(path['LibraryOptions']['PathInfos'][subpath]['Path'] in libraryfolders_set):
                        print(str(i) + ' - ' + path['LibraryOptions']['PathInfos'][subpath]['Path'])
                        libraryfolders_dict[i]=path['LibraryOptions']['PathInfos'][subpath]['Path']
                    else:
                        #show blank entry
                        print(str(i) + ' - ')
                i += 1

        print('')

        if (i >= 1):
            #print('Enter number of library folder to whitelist.')
            #print('Media in whitelisted library folders will NOT be deleted.')
            print(infotext)
            if ((mandatory) and (first_run)):
                first_run=False
                path_number=input('Must select at least one library to monitor: ')
            elif (mandatory):
                path_number=input('Leave blank when finished: ')
            else:
                path_number=input('Leave blank for none or when finished: ')

        try:
            if ((path_number == '') and (len(libraryfolders_set) == 0) and (mandatory)):
                print('\nMust select at least one library to monitor for this user. Try again.\n')
            elif (path_number == ''):
                stop_loop=True
                print('')
            else:
                path_number_float=float(path_number)
                if ((path_number_float % 1) == 0):
                    path_number_int=int(path_number_float)
                    if ((path_number_int >= 0) and (path_number_int < i)):
                        libraryfolders_set.add(libraryfolders_dict[path_number_int])
                        if (len(libraryfolders_set) >= i):
                            stop_loop=True
                        else:
                            stop_loop=False
                        print('')

                        #DEBUG
                        #print('selected library folders')
                        #print(libraryfolders_set)
                    else:
                        print('\nInvalid value. Try again.\n')
                else:
                    print('\nInvalid value. Try again.\n')
        except:
            print('\nInvalid value. Try again.\n')

    if (libraryfolders_set == set()):
        return('')
    else:
        i=0
        libraryPaths=''
        for libfolders in libraryfolders_set:
            if (i == 0):
                libraryPaths = libfolders.replace('\\','/')
                i += 1
            else:
                libraryPaths = libfolders.replace('\\','/') + "," + libraryPaths

        return(libraryPaths)


#Check if json key exists
def does_key_exist(item, keyvalue):
    try:
        exists = item[keyvalue]
    except KeyError:
        return(False)
    return(True)


#Check if json index exists
def does_index_exist(item, indexvalue):
    try:
        exists = item[indexvalue]
    except IndexError:
        return(False)
    return(True)


#Check if json key and index exist
def does_key_index_exist(item, keyvalue, indexvalue):
    return(does_key_exist(item, keyvalue) and does_index_exist(item[keyvalue], indexvalue))


#Get count of days since last played
def get_days_since_played(date_last_played):
    #Get current time
    date_time_now = datetime.utcnow()

    #Keep the year, month, day, hour, minute, and seconds
      #split date_last_played after seconds
    try:
        split_date_micro_tz = date_last_played.split(".")
        date_time_last_played = datetime.strptime(date_last_played, '%Y-%m-%dT%H:%M:%S.' + split_date_micro_tz[1])
    except (ValueError):
        date_time_last_played = 'unknown date time format'

    if bool(cfg.DEBUG):
        #DEBUG
        print(date_time_last_played)

    if not (date_time_last_played == 'unknown date time format'):
        date_time_delta = date_time_now - date_time_last_played
        s_date_time_delta = str(date_time_delta)
        days_since_played = s_date_time_delta.split(' day')[0]
        if ':' in days_since_played:
            days_since_played = 'Played <1 day ago'
        elif days_since_played == '1':
            days_since_played = 'Played ' + days_since_played + ' day ago'
        else:
            days_since_played = 'Played ' + days_since_played + ' days ago'
    else:
        days_since_played='0'
    return(days_since_played)


#Get count of days since last played
def get_days_since_created(date_last_created):
    return(get_days_since_played(date_last_created).replace('Played', 'Created', 1))


#get season and episode numbers
def get_season_episode(season_number, episode_number):
    season_num = str(season_number)
    season_num_len=len(str(season_number))

    episode_num = str(episode_number)
    episode_num_len=len(str(episode_num))

    #at the least; print season.episode with 2-digits zero padded
    #if season or episode has more than 2-digits print x-digits zero padded
    if (season_num_len <= 2) and (episode_num_len <= 2):
        season_num = season_num.zfill(2)
        episode_num = episode_num.zfill(2)
    elif (season_num_len >= episode_num_len):
        season_num = season_num.zfill(season_num_len)
        episode_num = episode_num.zfill(season_num_len)
    else: #(season_num_len < episode_num_len):
        season_num = season_num.zfill(episode_num_len)
        episode_num = episode_num.zfill(episode_num_len)

    season_episode = 's' + season_num + '.e' + episode_num
    return(season_episode)


#send url request
def requestURL(url, debugBool, debugMessage, retries):

    #first delay if needed
        #delay value doubles each time the same API request is resent
    delay = 1
    #number of times after the intial API request to retry if an exception occurs
    retryAttempts = int(retries)

    getdata = True
    #try sending url request specified number of times
        #starting with a 1 second delay if an exception occurs and doubling the delay each attempt
    while(getdata):
        with request.urlopen(url) as response:
            if response.getcode() == 200:
                try:
                    source = response.read()
                    data = json.loads(source)
                    getdata = False
                    if bool(debugBool):
                        #DEBUG
                        print(debugMessage)
                        print2json(data)
                    return(data)
                except Exception as err:
                    time.sleep(delay)
                    #delay value doubles each time the same API request is resent
                    delay += delay
                    if (delay >= (2**retryAttempts)):
                        print('An error occured, a maximum of ' + str(retryAttempts) + ' attempts met, and no data retrieved from the \"' + debugMessage + '\" lookup.')
                        return(err)
            else:
                getdata = False
                print('An error occurred while attempting to retrieve data from the API.')
                return('Attempt to get data at: ' + debugMessage + '. Server responded with code: ' + str(response.getcode()))


#get additional item info needed to determine if parent of item is favorite
#get additional item info needed to determine if media item is in whitelist
def get_additional_item_info(server_url, user_key, itemId, auth_key, lookupTopic):
    #Get additonal item information
    #url=server_url + '/Users/' + user_key  + '/Items/' + str(itemId) + '?fields=SeriesStudio,Studios,Genres,Path&enableImages=False&api_key=' + auth_key
    url=server_url + '/Users/' + user_key  + '/Items/' + str(itemId) + '?enableImages=False&api_key=' + auth_key

    if bool(cfg.DEBUG):
        #DEBUG
        print('-----------------------------------------------------------')
        print(url)

    itemInfo=requestURL(url, cfg.DEBUG, lookupTopic, cfg.api_request_attempts)

    return(itemInfo)


#get additional channel/network/studio info needed to determine if item is favorite
def get_studio_item_info(server_url, user_key, studioName, auth_key):
    #Encode studio name
    networkchannel_name=urllib.parse.quote(studioName)

    #Get studio item information
    url=server_url + '/Studios/' + networkchannel_name + '?userId=' + user_key + '&enableImages=False&api_key=' + auth_key

    if bool(cfg.DEBUG):
        #DEBUG
        print('-----------------------------------------------------------')
        print(url)

    itemInfo=requestURL(url, cfg.DEBUG, 'get_studio_item_info', cfg.api_request_attempts)

    return(itemInfo)


#determine if track, album, or artist are set to favorite
def get_isfav_AUDIOtaa(isfav_AUDIOtaa, item, server_url, user_key, auth_key):
    #Set bitmasks
    adv_settings=int(cfg.keep_favorites_advanced, 2)
    adv_settings_any=int(cfg.keep_favorites_advanced_any, 2)
    trackartist_mask=int('00000001', 2)
    albumartist_mask=int('00000010', 2)
    trackgenre_mask=int('00000100', 2)
    albumgenre_mask=int('00001000', 2)
    trackartist_any_mask=trackartist_mask
    albumartist_any_mask=albumartist_mask
    trackgenre_any_mask=trackgenre_mask
    albumgenre_any_mask=albumgenre_mask

### Track #########################################################################################

    #Check if track's favorite value already exists in dictionary
    if not item['Id'] in isfav_AUDIOtaa['track']:
        #Store if this track is marked as a favorite
        isfav_AUDIOtaa['track'][item['Id']] = item['UserData']['IsFavorite']

    if (does_key_index_exist(item, 'GenreItems', 0)):
        #Check if bitmask for favotires by track genre is enabled
        if (adv_settings & trackgenre_mask):
            #Check if bitmask for any or first track genre is enabled
            if not (adv_settings_any & trackgenre_any_mask):
                genre_track_item_info = get_additional_item_info(server_url, user_key, item['GenreItems'][0]['Id'], auth_key, 'track_genre')
                #Check if track genre's favorite value already exists in dictionary
                if not item['GenreItems'][0]['Id'] in isfav_AUDIOtaa['trackgenre']:
                    #Store if first track genre is marked as favorite
                    isfav_AUDIOtaa['trackgenre'][item['GenreItems'][0]['Id']] = genre_track_item_info['UserData']['IsFavorite']
            else:
                for trackgenre in range(len(item['GenreItems'])):
                    genre_track_item_info = get_additional_item_info(server_url, user_key, item['GenreItems'][trackgenre]['Id'], auth_key, 'track_genre_any')
                    #Check if track genre's favorite value already exists in dictionary
                    if not item['GenreItems'][trackgenre]['Id'] in isfav_AUDIOtaa['trackgenre']:
                        #Store if any track genre is marked as a favorite
                        isfav_AUDIOtaa['trackgenre'][item['GenreItems'][trackgenre]['Id']] = genre_track_item_info['UserData']['IsFavorite']

### End Track #####################################################################################

### Album #########################################################################################

    album_item_info = get_additional_item_info(server_url, user_key, item['AlbumId'], auth_key, 'album_info')

    #Check if album's favorite value already exists in dictionary
    if not item['AlbumId'] in isfav_AUDIOtaa['album']:
        #Store if the album is marked as a favorite
        isfav_AUDIOtaa['album'][item['AlbumId']] = album_item_info['UserData']['IsFavorite']

    if (does_key_index_exist(album_item_info, 'GenreItems', 0)):
        #Check if bitmask for favotires by album genre is enabled
        if (adv_settings & albumgenre_mask):
            #Check if bitmask for any or first album genre is enabled
            if not (adv_settings_any & albumgenre_any_mask):
                genre_album_item_info = get_additional_item_info(server_url, user_key, album_item_info['GenreItems'][0]['Id'], auth_key, 'ablum_genre')
                #Check if album genre's favorite value already exists in dictionary
                if not album_item_info['GenreItems'][0]['Id'] in isfav_AUDIOtaa['albumgenre']:
                    #Store if first album genre is marked as favorite
                    isfav_AUDIOtaa['albumgenre'][album_item_info['GenreItems'][0]['Id']] = genre_album_item_info['UserData']['IsFavorite']
            else:
                for albumgenre in range(len(album_item_info['GenreItems'])):
                    genre_album_item_info = get_additional_item_info(server_url, user_key, album_item_info['GenreItems'][albumgenre]['Id'], auth_key, 'album_genre_any')
                    #Check if album genre's favorite value already exists in dictionary
                    if not album_item_info['GenreItems'][albumgenre]['Id'] in isfav_AUDIOtaa['albumgenre']:
                        #Store if any album genre is marked as a favorite
                        isfav_AUDIOtaa['albumgenre'][album_item_info['GenreItems'][albumgenre]['Id']] = genre_album_item_info['UserData']['IsFavorite']

### End Album #####################################################################################

### Artist ########################################################################################

    if (does_key_index_exist(item, 'ArtistItems', 0)):
        #Check if bitmask for favorites by track artist is enabled
        if (adv_settings & trackartist_mask):
            #Check if bitmask for any or first track artist is enabled
            if not (adv_settings_any & trackartist_any_mask):
                artist_item_info = get_additional_item_info(server_url, user_key, item['ArtistItems'][0]['Id'], auth_key, 'artist_info')
                #Check if artist's favorite value already exists in dictionary
                if not item['ArtistItems'][0]['Id'] in isfav_AUDIOtaa['artist']:
                    #Store if first track artist is marked as favorite
                    isfav_AUDIOtaa['artist'][item['ArtistItems'][0]['Id']] = artist_item_info['UserData']['IsFavorite']
            else:
                for artist in range(len(item['ArtistItems'])):
                    artist_item_info = get_additional_item_info(server_url, user_key, item['ArtistItems'][artist]['Id'], auth_key, 'artist_info_any')
                    #Check if artist's favorite value already exists in dictionary
                    if not item['ArtistItems'][artist]['Id'] in isfav_AUDIOtaa['artist']:
                        #Store if any track artist is marked as a favorite
                        isfav_AUDIOtaa['artist'][item['ArtistItems'][artist]['Id']] = artist_item_info['UserData']['IsFavorite']

    if (does_key_index_exist(item, 'AlbumArtists', 0)):
        #Check if bitmask for favotires by album artist is enabled
        if (adv_settings & albumartist_mask):
            #Check if bitmask for any or first album artist is enabled
            if not (adv_settings_any & albumartist_any_mask):
                artist_item_info = get_additional_item_info(server_url, user_key, item['AlbumArtists'][0]['Id'], auth_key, 'album_info')
                #Check if artist's favorite value already exists in dictionary
                if not item['AlbumArtists'][0]['Id'] in isfav_AUDIOtaa['artist']:
                    #Store if first album artist is marked as favorite
                    isfav_AUDIOtaa['artist'][item['AlbumArtists'][0]['Id']] = artist_item_info['UserData']['IsFavorite']
            else:
                for albumartist in range(len(item['AlbumArtists'])):
                    artist_item_info = get_additional_item_info(server_url, user_key, item['AlbumArtists'][albumartist]['Id'], auth_key, 'album_info_any')
                    #Check if artist's favorite value already exists in dictionary
                    if not item['AlbumArtists'][albumartist]['Id'] in isfav_AUDIOtaa['artist']:
                        #Store if any album artist is marked as a favorite
                        isfav_AUDIOtaa['artist'][item['AlbumArtists'][albumartist]['Id']] = artist_item_info['UserData']['IsFavorite']

### End Artist ####################################################################################

    if bool(cfg.DEBUG):
        #DEBUG
        print('-----------------------------------------------------------')
        print('     Track is favorite: ' + str(isfav_AUDIOtaa['track'][item['Id']]))
        if (does_key_exist(item, 'AlbumId')):
            print('     Album is favorite: ' + str(isfav_AUDIOtaa['album'][item['AlbumId']]))

        if (does_key_index_exist(item, 'ArtistItems', 0)):
            if (adv_settings & trackartist_mask):
                if not (adv_settings_any & trackartist_any_mask):
                    print(' TrkArtist is favorite: ' + str(isfav_AUDIOtaa['artist'][item['ArtistItems'][0]['Id']]))
                else:
                    i=0
                    for artist in range(len(item['ArtistItems'])):
                        print('TrkArtist' + str(i) + ' is favorite: ' + str(isfav_AUDIOtaa['artist'][item['ArtistItems'][artist]['Id']]))
                        i+=1

        if (does_key_index_exist(item, 'AlbumArtists', 0)):
            if (adv_settings & albumartist_mask):
                if not (adv_settings_any & albumartist_any_mask):
                    print(' AlbArtist is favorite: ' + str(isfav_AUDIOtaa['artist'][item['AlbumArtists'][0]['Id']]))
                else:
                    i=0
                    for albumartist in range(len(item['AlbumArtists'])):
                        print('AlbArtist' + str(i) + ' is favorite: ' + str(isfav_AUDIOtaa['artist'][item['AlbumArtists'][albumartist]['Id']]))
                        i+=1

        if (does_key_index_exist(item, 'GenreItems', 0)):
            if (adv_settings & trackgenre_mask):
                if not (adv_settings_any & trackgenre_any_mask):
                    print('  TrkGenre is favorite: ' + str(isfav_AUDIOtaa['trackgenre'][item['GenreItems'][0]['Id']]))
                else:
                    i=0
                    for trackgenre in range(len(item['GenreItems'])):
                        print(' TrkGenre' + str(i) + ' is favorite: ' + str(isfav_AUDIOtaa['trackgenre'][item['GenreItems'][trackgenre]['Id']]))
                        i+=1

        if (does_key_index_exist(album_item_info, 'GenreItems', 0)):
            if (adv_settings & albumgenre_mask):
                if not (adv_settings_any & albumgenre_any_mask):
                    print('  AlbGenre is favorite: ' + str(isfav_AUDIOtaa['albumgenre'][album_item_info['GenreItems'][0]['Id']]))
                else:
                    i=0
                    for albumgenre in range(len(album_item_info['GenreItems'])):
                        print(' AlbGenre' + str(i) + ' is favorite: ' + str(isfav_AUDIOtaa['albumgenre'][album_item_info['GenreItems'][albumgenre]['Id']]))
                        i+=1


    #Check if track or album was stored as a favorite
    itemisfav_AUDIOtrackalbum=False
    if (does_key_exist(item, 'AlbumId')):
        if (
           (isfav_AUDIOtaa['track'][item['Id']]) or
           (isfav_AUDIOtaa['album'][item['AlbumId']])
           ):
            #Either the track or album was stored as a favorite
            itemisfav_AUDIOtrackalbum=True

    #Check if track artist was stored as a favorite
    itemisfav_AUDIOartist=False
    if (does_key_index_exist(item, 'ArtistItems', 0)):
        if (adv_settings & trackartist_mask):
            if not (adv_settings_any & trackartist_any_mask):
                if (isfav_AUDIOtaa['artist'][item['ArtistItems'][0]['Id']]):
                    itemisfav_AUDIOartist=True
            else:
                #Check if any track artist was stored as a favorite
                for artist in range(len(item['ArtistItems'])):
                    if (isfav_AUDIOtaa['artist'][item['ArtistItems'][artist]['Id']]):
                        itemisfav_AUDIOartist=True

    #Check if album artist was stored as a favorite
    itemisfav_AUDIOalbumartist=False
    if (does_key_index_exist(item, 'AlbumArtists', 0)):
        if (adv_settings & albumartist_mask):
            if not (adv_settings_any & albumartist_any_mask):
                if (isfav_AUDIOtaa['artist'][item['AlbumArtists'][0]['Id']]):
                    itemisfav_AUDIOalbumartist=True
            else:
                #Check if any album artist was stored as a favorite
                for albumartist in range(len(item['AlbumArtists'])):
                    if (isfav_AUDIOtaa['artist'][item['AlbumArtists'][albumartist]['Id']]):
                        itemisfav_AUDIOalubmartist=True

    #Check if track genre was stored as a favorite
    itemisfav_AUDIOtrackgenre=False
    if (does_key_index_exist(item, 'GenreItems', 0)):
        if (adv_settings & trackgenre_mask):
            if not (adv_settings_any & trackgenre_any_mask):
                if (isfav_AUDIOtaa['trackgenre'][item['GenreItems'][0]['Id']]):
                    itemisfav_AUDIOtrackgenre=True
            else:
                #Check if any track genre was stored as a favorite
                for trackgenre in range(len(item['GenreItems'])):
                    if (isfav_AUDIOtaa['trackgenre'][item['GenreItems'][trackgenre]['Id']]):
                        itemisfav_AUDIOtrackgenre=True

    #Check if album genre was stored as a favorite
    itemisfav_AUDIOalbumgenre=False
    if (does_key_index_exist(album_item_info, 'GenreItems', 0)):
        if (adv_settings & albumgenre_mask):
            if not (adv_settings_any & albumgenre_any_mask):
                if (isfav_AUDIOtaa['albumgenre'][album_item_info['GenreItems'][0]['Id']]):
                    itemisfav_AUDIOalbumgenre=True
            else:
                #Check if any album genre was stored as a favorite
                for albumgenre in range(len(album_item_info['GenreItems'])):
                    if (isfav_AUDIOtaa['albumgenre'][album_item_info['GenreItems'][albumgenre]['Id']]):
                        itemisfav_AUDIOalbumgenre=True

    #Check if track, album, or artist are a favorite
    itemisfav_AUDIOtaa=False
    if (
       (itemisfav_AUDIOtrackalbum) or
       (itemisfav_AUDIOartist) or
       (itemisfav_AUDIOalbumartist) or
       (itemisfav_AUDIOtrackgenre) or
       (itemisfav_AUDIOalbumgenre)
       ):
        #Either the track, album, artist(s), track genre(s), or album genre(s) are set as a favorite
        itemisfav_AUDIOtaa=True

    return(itemisfav_AUDIOtaa)


#determine if episode, season, series, or network are set to favorite
def get_isfav_TVessn(isfav_TVessn, item, server_url, user_key, auth_key):
    adv_settings=int(cfg.keep_favorites_advanced, 2)
    adv_settings_any=int(cfg.keep_favorites_advanced_any, 2)
    seriesgenre_mask=int('00010000', 2)
    seriesgenre_any_mask=seriesgenre_mask

### Episode #######################################################################################

    #Check if episode's favorite value already exists in dictionary
    if not item['Id'] in isfav_TVessn['episode']:
        #Store if this episode is marked as a favorite
        isfav_TVessn['episode'][item['Id']] = item['UserData']['IsFavorite']

### End Episode ###################################################################################

### Season ########################################################################################

    if (does_key_exist(item, 'SeasonId')):
        #Check if season's favorite value already exists in dictionary
        if not item['SeasonId'] in isfav_TVessn['season']:
            #Store if the season is marked as a favorite
            isfav_TVessn['season'][item['SeasonId']] = get_additional_item_info(server_url, user_key, item['SeasonId'], auth_key, 'season_info')['UserData']['IsFavorite']

### End Season ####################################################################################

### Series ########################################################################################

    series_item_info = get_additional_item_info(server_url, user_key, item['SeriesId'], auth_key, 'series_info')

    if (does_key_exist(item, 'SeriesId')):
        #Check if series' favorite value already exists in dictionary
        if not item['SeriesId'] in isfav_TVessn['series']:
            #Store if the series is marked as a favorite
            isfav_TVessn['series'][item['SeriesId']] = series_item_info['UserData']['IsFavorite']

    if (does_key_index_exist(series_item_info, 'GenreItems', 0)):
        #Check if bitmask for favotires by series genre is enabled
        if (adv_settings & seriesgenre_mask):
            #Check if bitmask for any or first series genre is enabled
            if not (adv_settings_any & seriesgenre_any_mask):
                genre_series_item_info = get_additional_item_info(server_url, user_key, series_item_info['GenreItems'][0]['Id'], auth_key, 'series_genre')
                #Check if series genre's favorite value already exists in dictionary
                if not series_item_info['GenreItems'][0]['Id'] in isfav_TVessn['seriesgenre']:
                    #Store if first series genre is marked as favorite
                    isfav_TVessn['seriesgenre'][series_item_info['GenreItems'][0]['Id']] = genre_series_item_info['UserData']['IsFavorite']
            else:
                for seriesgenre in range(len(series_item_info['GenreItems'])):
                    genre_series_item_info = get_additional_item_info(server_url, user_key, series_item_info['GenreItems'][seriesgenre]['Id'], auth_key, 'series_genre_any')
                    #Check if series genre's favorite value already exists in dictionary
                    if not series_item_info['GenreItems'][seriesgenre]['Id'] in isfav_TVessn['seriesgenre']:
                        #Store if any series genre is marked as a favorite
                        isfav_TVessn['seriesgenre'][series_item_info['GenreItems'][seriesgenre]['Id']] = genre_series_item_info['UserData']['IsFavorite']

### End Series ####################################################################################

### Network #######################################################################################

    if (does_key_exist(item, 'SeriesStudio')):
        #Check if network's favorite value already exists in dictionary
        if not item['SeriesStudio'] in isfav_TVessn['networkchannel']:
            #Store if the channel/network/studio is marked as a favorite
            isfav_TVessn['networkchannel'][item['SeriesStudio']] = get_studio_item_info(server_url, user_key, item['SeriesStudio'], auth_key)['UserData']['IsFavorite']

### End Network ###################################################################################

    if bool(cfg.DEBUG):
        #DEBUG
        print('-----------------------------------------------------------')
        print('  Episode is favorite: ' + str(isfav_TVessn['episode'][item['Id']]))
        if (does_key_exist(item, 'SeasonId')):
            print('   Season is favorite: ' + str(isfav_TVessn['season'][item['SeasonId']]))
        if (does_key_exist(item, 'SeriesId')):
            print('   Series is favorite: ' + str(isfav_TVessn['series'][item['SeriesId']]))
        if (does_key_exist(item, 'SeriesStudio')):
            print('  Network is favorite: ' + str(isfav_TVessn['networkchannel'][item['SeriesStudio']]))
        if (does_key_index_exist(series_item_info, 'GenreItems', 0)):
            if (adv_settings & seriesgenre_mask):
                if not (adv_settings_any & seriesgenre_any_mask):
                    print(' SerGenre is favorite: ' + str(isfav_TVessn['seriesgenre'][series_item_info['GenreItems'][0]['Id']]))
                else:
                    i=0
                    for seriesgenre in range(len(series_item_info['GenreItems'])):
                        print('SerGenre' + str(i) + ' is favorite: ' + str(isfav_TVessn['seriesgenre'][series_item_info['GenreItems'][seriesgenre]['Id']]))
                        i+=1

    seasonId_bool=False
    if (does_key_exist(item, 'SeasonId')):
        seasonId_bool=isfav_TVessn['season'][item['SeasonId']]
    seriesId_bool=False
    if (does_key_exist(item, 'SeriesId')):
        seriesId_bool=isfav_TVessn['series'][item['SeriesId']]
    networkchannel_bool=False
    if (does_key_exist(item, 'SeriesStudio')):
        networkchannel_bool=isfav_TVessn['networkchannel'][item['SeriesStudio']]

    #Check if episode, season, or series are a favorite
    itemisfav_TVepiseasernet=False
    if (
       (isfav_TVessn['episode'][item['Id']]) or
       (seasonId_bool) or
       (seriesId_bool) or
       (networkchannel_bool) #or
       ):
        #Either the episode, season, series, or network are set as a favorite
        itemisfav_TVepiseasernet=True

    itemisfav_TVseriesgenre=False
    if (does_key_index_exist(series_item_info, 'GenreItems', 0)):
        #Check if track genre was stored as a favorite
        if (adv_settings & seriesgenre_mask):
            if not (adv_settings_any & seriesgenre_any_mask):
                if (isfav_TVessn['seriesgenre'][series_item_info['GenreItems'][0]['Id']]):
                    itemisfav_TVseriesgenre=True
            else:
                #Check if any track genre was stored as a favorite
                for seriesgenre in range(len(series_item_info['GenreItems'])):
                    if (isfav_TVessn['seriesgenre'][series_item_info['GenreItems'][seriesgenre]['Id']]):
                        itemisfav_TVseriesgenre=True

    #Check if episode, season, series, series genre(s), or network/channel are a favorite
    itemisfav_TVessn=False
    if (
       (itemisfav_TVepiseasernet) or
       (itemisfav_TVseriesgenre)
       ):
        #Either the episode, season, series, series genre(s), or network/channel are set as a favorite
        itemisfav_TVessn=True

    return(itemisfav_TVessn)


#determine if movie is set to favorite
def get_isfav_MOVIE(isfav_MOVIE, item, server_url, user_key, auth_key):
    adv_settings=int(cfg.keep_favorites_advanced, 2)
    adv_settings_any=int(cfg.keep_favorites_advanced_any, 2)
    moviegenre_mask=int('00100000', 2)
    moviegenre_any_mask=moviegenre_mask

### Movie #######################################################################################

    #Check if movie's favorite value already exists in dictionary
    if not item['Id'] in isfav_MOVIE['movie']:
        #Store if this movie is marked as a favorite
        isfav_MOVIE['movie'][item['Id']] = item['UserData']['IsFavorite']

    if (does_key_index_exist(item, 'GenreItems', 0)):
        #Check if bitmask for favotires by movie genre is enabled
        if (adv_settings & moviegenre_mask):
            #Check if bitmask for any or first movie genre is enabled
            if not (adv_settings_any & moviegenre_any_mask):
                genre_movie_item_info = get_additional_item_info(server_url, user_key, item['GenreItems'][0]['Id'], auth_key, 'movie_genre')
                #Check if movie genre's favorite value already exists in dictionary
                if not item['GenreItems'][0]['Id'] in isfav_MOVIE['moviegenre']:
                    #Store if first movie genre is marked as favorite
                    isfav_MOVIE['moviegenre'][item['GenreItems'][0]['Id']] = genre_movie_item_info['UserData']['IsFavorite']
            else:
                for moviegenre in range(len(item['GenreItems'])):
                    genre_movie_item_info = get_additional_item_info(server_url, user_key, item['GenreItems'][moviegenre]['Id'], auth_key, 'movie_genre_any')
                    #Check if movie genre's favorite value already exists in dictionary
                    if not item['GenreItems'][moviegenre]['Id'] in isfav_MOVIE['moviegenre']:
                        #Store if any movie genre is marked as a favorite
                        isfav_MOVIE['moviegenre'][item['GenreItems'][moviegenre]['Id']] = genre_movie_item_info['UserData']['IsFavorite']

### End Movie ###################################################################################

    if bool(cfg.DEBUG):
        #DEBUG
        print('-----------------------------------------------------------')
        print('    Movie is favorite: ' + str(isfav_MOVIE['movie'][item['Id']]))

        if (does_key_index_exist(item, 'GenreItems', 0)):
            if (adv_settings & moviegenre_mask):
                if not (adv_settings_any & moviegenre_any_mask):
                    print(' MovGenre is favorite: ' + str(isfav_MOVIE['moviegenre'][item['GenreItems'][0]['Id']]))
                else:
                    i=0
                    for moviegenre in range(len(item['GenreItems'])):
                        print('MovGenre' + str(i) + ' is favorite: ' + str(isfav_MOVIE['moviegenre'][item['GenreItems'][moviegenre]['Id']]))
                        i+=1

    #Check if movie is a favorite
    itemisfav_MOVIEmovie=False
    if (
       (isfav_MOVIE['movie'][item['Id']])
       ):
        #Movie is set as a favorite
        itemisfav_MOVIEmovie=True

    #Check if movie genre was stored as a favorite
    itemisfav_MOVIEgenre=False
    if (does_key_index_exist(item, 'GenreItems', 0)):
        if (adv_settings & moviegenre_mask):
            if not (adv_settings_any & moviegenre_any_mask):
                if (isfav_MOVIE['moviegenre'][item['GenreItems'][0]['Id']]):
                    itemisfav_MOVIEgenre=True
            else:
                #Check if any movie genre was stored as a favorite
                for moviegenre in range(len(item['GenreItems'])):
                    if (isfav_MOVIE['moviegenre'][item['GenreItems'][moviegenre]['Id']]):
                        itemisfav_MOVIEgenre=True

    #Check if movie or movie genre(s) are a favorite
    itemisfav_MOVIE=False
    if (
       (itemisfav_MOVIEmovie) or
       (itemisfav_MOVIEgenre)
       ):
        #Either the movie or movie genre(s) are set as a favorite
        itemisfav_MOVIE=True

    return(itemisfav_MOVIE)


#Handle favorites across multiple users
def get_isfav_MultiUser(userkey, isfav_byUserId, deleteItems):
    deleteIndexes=[]

    #compare favorited items across users
    #remove from deleteItems list if configured to keep media item when any user has it set as a favorite
    for userId in userkey:
        for usersItemId in isfav_byUserId[userId]:
            #remove all occurance of this items Id from deleteItems if favorited
            if (isfav_byUserId[userId][usersItemId]):
                for delItems in range(len(deleteItems)):
                    if (usersItemId == deleteItems[delItems]['Id']):
                        deleteIndexes.append(delItems)

    #convert to set then back to list to remove duplicates
    deleteIndexes=list(set(deleteIndexes))

    #sort indexes needed to remove items from deletion that we want to keep
    deleteIndexes.sort()

    #reverse the order to not worry about shifting indexes when removing items from deleteItems list
    deleteIndexes.reverse()

    #remove favorited items we want to keep
    for favItem in deleteIndexes:
        try:
           deleteItems.pop(favItem)
        except IndexError as err:
           print(str(err))
           print(favItem)
           print(deleteIndexes)
           print2json(deleteItems)
           exit(0)

    deleteIndexes=[]

    #find duplicates
    for item0 in range(len(deleteItems)):
        for item1 in range(len(deleteItems)):
            if (item0 < item1):
               if (deleteItems[item0]['Id'] == deleteItems[item1]['Id']):
                   deleteIndexes.append(item1)

    #convert to set then back to list to remove duplicates
    deleteIndexes=list(set(deleteIndexes))

    #sort indexes needed to remove items from deletion that we want to keep
    deleteIndexes.sort()

    #reverse the order so not worry about shifting indexes when removing items from deleteItems list
    deleteIndexes.reverse()

    #remove duplicates
    for favItem in deleteIndexes:
        try:
            deleteItems.pop(favItem)
        except IndexError as err:
            print(str(err))
            print(favItem)
            print(deleteIndexes)
            print2json(deleteItems)
            exit(0)

    return(deleteItems)


#Handle whitelists across multiple users by userId
def get_iswhitelist_MultiUser_byId(userkeys, iswhitelist_byUserId, deleteItems):
    return(get_isfav_MultiUser(userkeys, iswhitelist_byUserId, deleteItems))


#Handle whitelists across multiple users by Path
def get_iswhitelist_MultiUser_byPath(userkeys, whitelists, deleteItems):
    all_whitelists=set()
    deleteIndexes=[]

    #len_userkeys=len(userkeys)
    len_deleteItems=len(deleteItems)

    #build whitelist dictionary
    for whitelist in whitelists:
        #read and split paths to compare to
        whitelist_split=whitelist.split(',')
        #add whitelist paths to set
        for wlist in whitelist_split:
            if not (wlist == ''):
                all_whitelists.add(wlist)

    #loop thru all whitelists and items to be deleted
    #remove item if it matches a whitelisted path
    for delIndex in range(len(deleteItems)):
        for whitelist in all_whitelists:
            delItemIsWhitelisted, delItemWhitelistedPath=get_isWhitelisted(deleteItems[delIndex]['Path'], whitelist)
            if (delItemIsWhitelisted):
                deleteIndexes.append(delIndex)

    #convert to set then back to list to remove duplicates
    deleteIndexes=list(set(deleteIndexes))

    #sort indexes needed to remove items from deletion that we want to keep
    deleteIndexes.sort()

    #reverse the order to not worry about shifting indexes when removing items from deleteItems list
    deleteIndexes.reverse()

    #remove favorited items we want to keep
    for wlItem in deleteIndexes:
        try:
           deleteItems.pop(wlItem)
        except IndexError as err:
           print(str(err))
           print(wlItem)
           print(deleteIndexes)
           print2json(deleteItems)
           exit(0)

    return(deleteItems)


#determine if media item is in library folder
def get_isPathMatching(itemPath, comparePath):

    #for paths in Microsoft Windows, replace double forward slashes in item's path with a single back slash
    itemPath = itemPath.replace('\\','/')

    #read and split paths to compare to
    comparePathEntries=comparePath.split(',')

    matchingPath=''
    item_path_matches=False
    #determine if media item's path matches one of the whitelist folders
    for path in comparePathEntries:
        if not (path == ''):
            if (itemPath.startswith(path)):
                matchingPath=path
                item_path_matches=True

                if bool(cfg.DEBUG):
                    #DEBUG
                    print('media item folder/path comparison')
                    print(path + ' : ' + itemPath)

                return(item_path_matches, matchingPath)

    return(item_path_matches, matchingPath)


#determine if item is whitelisted
def get_isWhitelisted(itemPath, comparePath):
    pathResult, pathString=get_isPathMatching(itemPath, comparePath)
    return(pathResult, pathString)


#determine if item is blacklisted (aka monitored)
def get_isBlacklisted(itemPath, comparePath):
    if (comparePath == ''):
        return(True)
    else:
        pathResult, pathString=get_isPathMatching(itemPath, comparePath)
        return(pathResult)

#get played media items; track media items ready to be deleted
def get_items(server_url, user_keys, auth_key):
    #Get list of all played items
    print('')
    print('-----------------------------------------------------------')
    print('Start...')
    print('Cleaning media for server at: ' + server_url)
    print('-----------------------------------------------------------')
    print('')

    all_media_disabled=False

    if (
       (cfg.not_played_age_movie == -1) and
       (cfg.not_played_age_episode == -1) and
       (cfg.not_played_age_video == -1) and
       (cfg.not_played_age_trailer == -1) and
       (cfg.not_played_age_audio == -1) and
       (cfg.max_age_movie == -1) and
       (cfg.max_age_episode == -1) and
       (cfg.max_age_video == -1) and
       (cfg.max_age_trailer == -1) and
       (cfg.max_age_audio == -1)
       ):
        print('* ATTENTION!!!                             *')
        print('* No media types are being monitored.      *')
        print('* not_played_age_movie=-1                  *')
        print('* not_played_age_episode=-1                *')
        print('* not_played_age_video=-1                  *')
        print('* not_played_age_trailer=-1                *')
        print('* not_played_age_audio=-1                  *')
        print('* Open config file in text editor.         *')
        print('* Set at least one media type to >=0 days. *')
        print('-----------------------------------------------------------')
        all_media_disabled=True

    #list of items to be deleted
    deleteItems=[]
    #dictionary of favorited items by userId
    isfav_byUserId={}
    #dictionary of whitelisted items by userId
    iswhitelist_byUserId={}
    #whitelisted paths per media type according to media types metadata
    movie_whitelists=set()
    episode_whitelists=set()
    video_whitelists=set()
    trailer_whitelists=set()
    audio_whitelists=set()

    #load user_keys to json
    user_keys_json=json.loads(user_keys)
    #load user_bl_libs to json
    user_bllib_json=json.loads(cfg.user_bl_libs)
    #load_user_wl_libs to json
    user_wllib_json=json.loads(cfg.user_wl_libs)

    #get number of user_keys and user_libs
    userkey_count=len(user_keys_json)
    userbllib_count=len(user_bllib_json)
    userwllib_count=len(user_wllib_json)

    #establish deletion date for played media items
    cut_off_date_movie=datetime.now(timezone.utc) - timedelta(cfg.not_played_age_movie)
    cut_off_date_episode=datetime.now(timezone.utc) - timedelta(cfg.not_played_age_episode)
    cut_off_date_video=datetime.now(timezone.utc) - timedelta(cfg.not_played_age_video)
    cut_off_date_trailer=datetime.now(timezone.utc) - timedelta(cfg.not_played_age_trailer)
    cut_off_date_audio=datetime.now(timezone.utc) - timedelta(cfg.not_played_age_audio)

    adv_settings=int(cfg.keep_favorites_advanced, 2)

    currentPosition=0
    for user_key in user_keys_json:
        url=server_url + '/Users/' + user_key  + '/?api_key=' + auth_key

        if bool(cfg.DEBUG):
            #DEBUG
            print(url)

        data=requestURL(url, cfg.DEBUG, 'current_user', cfg.api_request_attempts)

        print('')
        print('-----------------------------------------------------------')
        print('Get List Of Media For:')
        print(data['Name'] + ' - ' + data['Id'])
        print('-----------------------------------------------------------')

        media_found=False

        #define empty dictionary for favorited Movies
        isfav_MOVIE={'movie':{},'moviegenre':{}}
        #define empty dictionary for favorited TV Series, Seasons, Episodes, and Channels/Networks
        isfav_TVessn={'episode':{},'season':{},'series':{},'networkchannel':{},'seriesgenre':{}}
        #define empty dictionary for favorited Tracks, Albums, Artists
        isfav_AUDIOtaa={'track':{},'album':{},'artist':{},'trackgenre':{},'albumgenre':{}}

        #define dictionary user_key to store media item favorite states by userId and itemId
        isfav_byUserId[user_key]={}
        #define dictionary user_key to store media item whitelisted states by userId and itemId
        iswhitelist_byUserId[user_key]={}

############# Movies #############

        if ((cfg.not_played_age_movie >= 0) or (cfg.max_age_movie >= 0)):

            moviegenre_mask=int('00100000', 2)

            IsPlayedState='True'
            #FieldsState='Type,Name,Id,UserData,Studios,ParentId,DateCreated,Path,MediaSource'
            FieldsState='Id,Path'
            if (cfg.max_age_movie >= 0):
                IsPlayedState=''
            #if (moviegenre_mask & adv_settings):
                #FieldsState=FieldsState + ',Genres'

            StartIndex=0
            TotalItems=1
            ItemsChunk=1

            while (ItemsChunk > 0):

                url=(server_url + '/Users/' + user_key  + '/Items?includeItemTypes=Movie&StartIndex=' + str(StartIndex) + '&Limit=' + str(ItemsChunk) + '&IsPlayed=' + str(IsPlayedState) + '&Fields=' + str(FieldsState) +
                    '&Recursive=true&SortBy=ParentIndexNumber,IndexNumber,Name&SortOrder=Ascending&enableImages=False&api_key=' + auth_key)

                if bool(cfg.DEBUG):
                    #DEBUG
                    print(url)

                data=requestURL(url, cfg.DEBUG, 'movie_media_data', cfg.api_request_attempts)

                TotalItems = data['TotalRecordCount']
                StartIndex = StartIndex + ItemsChunk
                ItemsChunk = cfg.api_return_limit
                if ((StartIndex + ItemsChunk) >= (TotalItems)):
                    ItemsChunk = TotalItems - StartIndex

                #Determine if media item is to be deleted or kept
                for item in data['Items']:

                    media_found=True

                    #Get if media item path is monitored
                    item_info=get_additional_item_info(server_url, user_key, item['Id'], auth_key, 'movie_item')

                    for mediasource in item_info['MediaSources']:

                        if (does_key_exist(mediasource, 'Type') and does_key_exist(mediasource, 'Size')):
                            if ((mediasource['Type'] == 'Placeholder') and (mediasource['Size'] == 0)):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        elif (does_key_exist(mediasource, 'Type')):
                            if (mediasource['Type'] == 'Placeholder'):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        elif (does_key_exist(mediasource, 'Size')):
                            if (mediasource['Size'] == 0):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        else:
                            itemIsMonitored=False
                            #itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])

                    #find movie media items ready to delete
                    if ((item_info['Type'] == 'Movie') and (itemIsMonitored)):

                        #establish max cutoff date for media item
                        if (cfg.max_age_movie >= 0):
                            max_cut_off_date_movie=datetime.strptime(item_info['DateCreated'], '%Y-%m-%dT%H:%M:%S.' + item_info['DateCreated'].split(".")[1]) + timedelta(cfg.max_age_movie)
                        else:
                            max_cut_off_date_movie=date_time_now = datetime.utcnow() + timedelta(1)

                        #Get if movie is set as favorite
                        itemisfav_MOVIE=get_isfav_MOVIE(isfav_MOVIE, item_info, server_url, user_key, auth_key)

                        #Get if media item path is whitelisted
                        itemIsWhiteListed, itemWhiteListedPath=get_isWhitelisted(item_info['Path'], user_wllib_json[currentPosition])

                        #Store media item's favorite state when multiple users are monitored and we want to keep media items based on any user favoriting the media item
                        if (cfg.keep_favorites_movie == 2):
                            isfav_byUserId[user_key][item_info['Id']] = itemisfav_MOVIE

                        #Store media item's whitelist state when multiple users are monitored and we want to keep media items based on any user whitelisting the parent library
                        if (cfg.multiuser_whitelist_movie == 1):
                            iswhitelist_byUserId[user_key][item_info['Id']] = itemIsWhiteListed
                            movie_whitelists.add(itemWhiteListedPath)

                        if (
                           ((cfg.not_played_age_movie >= 0) and
                           (item_info['UserData']['PlayCount'] >= 1) and
                           (cut_off_date_movie > parse(item_info['UserData']['LastPlayedDate'])) and
                           (not bool(cfg.keep_favorites_movie) or (not itemisfav_MOVIE)) and 
                           (not itemIsWhiteListed))
                           or
                           ((cfg.max_age_movie >= 0) and
                           (max_cut_off_date_movie <= datetime.utcnow()) and
                           (((not bool(cfg.keep_favorites_movie)) or (not itemisfav_MOVIE)) and
                           ((not bool(cfg.max_keep_favorites_movie)) or (not itemisfav_MOVIE))) and
                           (not itemIsWhiteListed))
                           ):
                            try:
                                if (does_key_exist(item_info['UserData'], 'LastPlayedDate')):
                                    item_details=('  ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + item_info['Studios'][0]['Name'] + ' - ' + get_days_since_played(item_info['UserData']['LastPlayedDate']) +
                                                  ' - ' + get_days_since_created(item_info['DateCreated']) + ' - Favorite: ' + str(itemisfav_MOVIE) + ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'MovieID: ' + item_info['Id'])
                                else:
                                    item_details=('  ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + item_info['Studios'][0]['Name'] + ' - ' + get_days_since_created(item_info['DateCreated']) +
                                                  ' - Favorite: ' + str(itemisfav_MOVIE) + ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'MovieID: ' + item_info['Id'])
                            except (KeyError, IndexError):
                                item_details='  ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + item_info['Id']
                                if bool(cfg.DEBUG):
                                    #DEBUG
                                    print('\nError encountered - Delete Movie: \nitem: ' + str(item) + '\nitem_info' + str(item_info))
                            print(':*[DELETE] - ' + item_details)
                            deleteItems.append(item)
                        else:
                            try:
                                if (does_key_exist(item_info['UserData'], 'LastPlayedDate')):
                                    item_details=('  ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + item_info['Studios'][0]['Name'] + ' - ' + get_days_since_played(item_info['UserData']['LastPlayedDate']) +
                                                  ' - ' + get_days_since_created(item_info['DateCreated']) + ' - Favorite: ' + str(itemisfav_MOVIE) + ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'MovieID: ' + item_info['Id'])
                                else:
                                    item_details=('  ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + item_info['Studios'][0]['Name'] + ' - ' + get_days_since_created(item_info['DateCreated']) +
                                                  ' - Favorite: ' + str(itemisfav_MOVIE) + ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'MovieID: ' + item_info['Id'])
                            except (KeyError, IndexError):
                                item_details='  ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + item_info['Id']
                                if bool(cfg.DEBUG):
                                    #DEBUG
                                    print('\nError encountered - Keep Movie: \nitem: ' + str(item) + '\nitem_info' + str(item_info))
                            print(':[KEEPING] - ' + item_details)

############# Episodes #############

        if ((cfg.not_played_age_episode >= 0) or (cfg.max_age_episode >= 0)):

            IsPlayedState='True'
            #FieldsState='Type,Name,Id,UserData,SeriesStudio,ParentId,DateCreated'
            FieldsState='Id,Path,SeriesStudio'
            if (cfg.max_age_episode >= 0):
                IsPlayedState=''

            StartIndex=0
            TotalItems=1
            ItemsChunk=1

            while (ItemsChunk > 0):

                if (cfg.server_brand == 'emby'):
                    url=(server_url + '/Users/' + user_key  + '/Items?includeItemTypes=Episode&StartIndex=' + str(StartIndex) + '&Limit=' + str(ItemsChunk) + '&IsPlayed=' + str(IsPlayedState) + '&Fields=' + str(FieldsState) +
                        '&Recursive=true&SortBy=SeriesName,ParentIndexNumber,IndexNumber,Name&SortOrder=Ascending&enableImages=False&api_key=' + auth_key)
                else: #jellyfin API will not allow episodes to use the enableImages=False option; separating for now until jellyfin is able to investigate why
                    url=(server_url + '/Users/' + user_key  + '/Items?includeItemTypes=Episode&StartIndex=' + str(StartIndex) + '&Limit=' + str(ItemsChunk) + '&IsPlayed=' + str(IsPlayedState) + '&Fields=' + str(FieldsState) +
                        '&Recursive=true&SortBy=SeriesName,ParentIndexNumber,IndexNumber,Name&SortOrder=Ascending&api_key=' + auth_key)

                if bool(cfg.DEBUG):
                    #DEBUG
                    print(url)

                data=requestURL(url, cfg.DEBUG, 'episode_media_data', cfg.api_request_attempts)

                TotalItems = data['TotalRecordCount']
                StartIndex = StartIndex + ItemsChunk
                ItemsChunk = cfg.api_return_limit
                if ((StartIndex + ItemsChunk) >= (TotalItems)):
                    ItemsChunk = TotalItems - StartIndex

                #Determine if media item is to be deleted or kept
                for item in data['Items']:

                    media_found=True

                    #Get if media item path is monitored
                    item_info=get_additional_item_info(server_url, user_key, item['Id'], auth_key, 'episode_item')

                    for mediasource in item_info['MediaSources']:

                        if (does_key_exist(mediasource, 'Type') and does_key_exist(mediasource, 'Size')):
                            if ((mediasource['Type'] == 'Placeholder') and (mediasource['Size'] == 0)):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        elif (does_key_exist(mediasource, 'Type')):
                            if (mediasource['Type'] == 'Placeholder'):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        elif (does_key_exist(mediasource, 'Size')):
                            if (mediasource['Size'] == 0):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        else:
                            itemIsMonitored=False
                            #itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])

                    #find tv-episode media items ready to delete
                    if ((item_info['Type'] == 'Episode') and (itemIsMonitored)):

                        #establish max cutoff date for media item
                        if (cfg.max_age_episode >= 0):
                            max_cut_off_date_episode=datetime.strptime(item_info['DateCreated'], '%Y-%m-%dT%H:%M:%S.' + item_info['DateCreated'].split(".")[1]) + timedelta(cfg.max_age_episode)
                        else:
                            max_cut_off_date_episode=date_time_now = datetime.utcnow() + timedelta(1)

                        #Get if episode, season, or series is set as favorite
                        itemisfav_TVessn=get_isfav_TVessn(isfav_TVessn, item_info, server_url, user_key, auth_key)

                        #Get if media item path is whitelisted
                        itemIsWhiteListed, itemWhiteListedPath=get_isWhitelisted(item_info['Path'], user_wllib_json[currentPosition])

                        #Store media item's favorite state when multiple users are monitored and we want to keep media items based on any user favoriting the media item
                        if (cfg.keep_favorites_episode == 2):
                            isfav_byUserId[user_key][item_info['Id']] = itemisfav_TVessn

                        #Store media item's whitelist state when multiple users are monitored and we want to keep media items based on any user whitelisting the parent library
                        if (cfg.multiuser_whitelist_episode == 1):
                            iswhitelist_byUserId[user_key][item_info['Id']] = itemIsWhiteListed
                            episode_whitelists.add(itemWhiteListedPath)

                        if (
                           ((cfg.not_played_age_episode >= 0) and
                           (item_info['UserData']['PlayCount'] >= 1) and
                           (cut_off_date_episode > parse(item_info['UserData']['LastPlayedDate'])) and
                           (not bool(cfg.keep_favorites_episode) or (not itemisfav_TVessn)) and
                           (not itemIsWhiteListed))
                           or
                           ((cfg.max_age_episode >= 0) and
                           (max_cut_off_date_episode <= datetime.utcnow()) and
                           (((not bool(cfg.keep_favorites_episode)) or (not itemisfav_TVessn)) and
                           ((not bool(cfg.max_keep_favorites_episode)) or (not itemisfav_TVessn))) and
                           (not itemIsWhiteListed))
                           ):
                            try:
                                if (does_key_exist(item_info['UserData'], 'LastPlayedDate')):
                                    item_details=(item_info['Type'] + ' - ' + item_info['SeriesName'] + ' - ' + get_season_episode(item_info['ParentIndexNumber'], item_info['IndexNumber']) + ' - ' + item_info['Name'] + ' - ' + item['SeriesStudio'] +
                                                  ' - ' + get_days_since_played(item_info['UserData']['LastPlayedDate']) + ' - ' + get_days_since_created(item_info['DateCreated']) + ' - Favorite: ' + str(itemisfav_TVessn) +
                                                  ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'EpisodeID: ' + item_info['Id'])
                                else:
                                    item_details=(item_info['Type'] + ' - ' + item_info['SeriesName'] + ' - ' + get_season_episode(item_info['ParentIndexNumber'], item_info['IndexNumber']) + ' - ' + item_info['Name'] + ' - ' + item['SeriesStudio'] +
                                                 ' - ' + get_days_since_created(item_info['DateCreated']) + ' - Favorite: ' + str(itemisfav_TVessn) + ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' +
                                                 'EpisodeID: ' + item_info['Id'])
                            except (KeyError, IndexError):
                                item_details='  ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + item_info['Id']
                                if bool(cfg.DEBUG):
                                    #DEBUG
                                    print('\nError encountered - Delete Episode: \nitem: ' + str(item) + '\nitem_info' + str(item_info))
                            print(':*[DELETE] - ' + item_details)
                            deleteItems.append(item)
                        else:
                            try:
                                if (does_key_exist(item_info['UserData'], 'LastPlayedDate')):
                                    item_details=(item_info['Type'] + ' - ' + item_info['SeriesName'] + ' - ' + get_season_episode(item_info['ParentIndexNumber'], item_info['IndexNumber']) + ' - ' + item_info['Name'] + ' - ' + item['SeriesStudio'] +
                                                  ' - ' + get_days_since_played(item_info['UserData']['LastPlayedDate']) + ' - ' + get_days_since_created(item_info['DateCreated']) + ' - Favorite: ' + str(itemisfav_TVessn) +
                                                  ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'EpisodeID: ' + item_info['Id'])
                                else:
                                    item_details=(item_info['Type'] + ' - ' + item_info['SeriesName'] + ' - ' + get_season_episode(item_info['ParentIndexNumber'], item_info['IndexNumber']) + ' - ' + item_info['Name'] + ' - ' + item['SeriesStudio'] +
                                                 ' - ' + get_days_since_created(item_info['DateCreated']) + ' - Favorite: ' + str(itemisfav_TVessn) + ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' +
                                                 'EpisodeID: ' + item_info['Id'])
                            except (KeyError, IndexError):
                                item_details='  ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + item_info['Id']
                                if bool(cfg.DEBUG):
                                    #DEBUG
                                    print('\nError encountered - Keep Episode: \nitem: ' + str(item) + '\nitem_info' + str(item_info))
                            print(':[KEEPING] - ' + item_details)

############# Videos #############

        if ((cfg.not_played_age_video >= 0) or (cfg.max_age_video >= 0)):

            IsPlayedState='True'
            #FieldsState='Type,Name,Id,UserData,ParentId,DateCreated'
            FieldsState='Id,Path'
            if (cfg.max_age_video >= 0):
                IsPlayedState=''

            StartIndex=0
            TotalItems=1
            ItemsChunk=1

            while (ItemsChunk > 0):

                url=(server_url + '/Users/' + user_key  + '/Items?includeItemTypes=Video&StartIndex=' + str(StartIndex) + '&Limit=' + str(ItemsChunk) + '&IsPlayed=' + str(IsPlayedState) + '&Fields=' + str(FieldsState) +
                    '&Recursive=true&SortBy=ParentIndexNumber,IndexNumber,Name&SortOrder=Ascending&enableImages=False&api_key=' + auth_key)

                if bool(cfg.DEBUG):
                    #DEBUG
                    print(url)

                data=requestURL(url, cfg.DEBUG, 'video_media_data', cfg.api_request_attempts)

                TotalItems = data['TotalRecordCount']
                StartIndex = StartIndex + ItemsChunk
                ItemsChunk = cfg.api_return_limit
                if ((StartIndex + ItemsChunk) >= (TotalItems)):
                    ItemsChunk = TotalItems - StartIndex

                #Determine if media item is to be deleted or kept
                for item in data['Items']:

                    media_found=True

                    #Get if media item path is monitored
                    item_info=get_additional_item_info(server_url, user_key, item['Id'], auth_key, 'video_item')

                    for mediasource in item_info['MediaSources']:

                        if (does_key_exist(mediasource, 'Type') and does_key_exist(mediasource, 'Size')):
                            if ((mediasource['Type'] == 'Placeholder') and (mediasource['Size'] == 0)):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        elif (does_key_exist(mediasource, 'Type')):
                            if (mediasource['Type'] == 'Placeholder'):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        elif (does_key_exist(mediasource, 'Size')):
                            if (mediasource['Size'] == 0):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        else:
                            itemIsMonitored=False
                            #itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])

                    #find video media items ready to delete
                    if ((item_info['Type'] == 'Video') and (itemIsMonitored)):

                        #establish max cutoff date for media item
                        if (cfg.max_age_video >= 0):
                            max_cut_off_date_video=datetime.strptime(item_info['DateCreated'], '%Y-%m-%dT%H:%M:%S.' + item_info['DateCreated'].split(".")[1]) + timedelta(cfg.max_age_video)
                        else:
                            max_cut_off_date_video=date_time_now = datetime.utcnow() + timedelta(1)

                        #Store media item's favorite state when multiple users are monitored and we want to keep media items based on any user favoriting the media item
                        if (cfg.keep_favorites_video == 2):
                            isfav_byUserId[user_key][item_info['Id']] = cfg.keep_favorites_video

                        #Get if media item path is whitelisted
                        itemIsWhiteListed, itemWhiteListedPath=get_isWhitelisted(item_info['Path'], user_wllib_json[currentPosition])

                        #Store media item's whitelist state when multiple users are monitored and we want to keep media items based on any user whitelisting the parent library
                        if (cfg.multiuser_whitelist_video == 1):
                            iswhitelist_byUserId[user_key][item_info['Id']] = itemIsWhiteListed
                            video_whitelists.add(itemWhiteListedPath)

                        if (
                           ((cfg.not_played_age_video >= 0) and
                           (item_info['UserData']['PlayCount'] >= 1) and
                           (cut_off_date_video > parse(item_info['UserData']['LastPlayedDate'])) and
                           (not bool(cfg.keep_favorites_video) or not item_info['UserData']['IsFavorite']) and
                           (not itemIsWhiteListed))
                           or
                           ((cfg.max_age_video >= 0) and
                           (max_cut_off_date_video <= datetime.utcnow()) and
                           (((not bool(cfg.keep_favorites_video)) or (not not item_info['UserData']['IsFavorite'])) and
                           ((not bool(cfg.max_keep_favorites_video)) or (not item_info['UserData']['IsFavorite']))) and
                           (not itemIsWhiteListed))
                           ):
                            try:
                                if (does_key_exist(item_info['UserData'], 'LastPlayedDate')):
                                    item_details=('  ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + get_days_since_played(item_info['UserData']['LastPlayedDate']) + ' - ' + get_days_since_created(item_info['DateCreated']) +
                                                  ' -  Favorite: ' + str(item_info['UserData']['IsFavorite']) + ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'VideoID: ' + item_info['Id'])
                                else:
                                    item_details=('  ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + get_days_since_created(item_info['DateCreated']) +
                                                  ' -  Favorite: ' + str(item_info['UserData']['IsFavorite']) + ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'VideoID: ' + item_info['Id'])
                            except (KeyError, IndexError):
                                item_details='  ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + item_info['Id']
                                if bool(cfg.DEBUG):
                                    #DEBUG
                                    print('\nError encountered - Delete Video: \nitem: ' + str(item) + '\nitem_info' + str(item_info))
                            print(':*[DELETE] - ' + item_details)
                            deleteItems.append(item)
                        else:
                            try:
                                if (does_key_exist(item_info['UserData'], 'LastPlayedDate')):
                                    item_details=('  ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + get_days_since_played(item_info['UserData']['LastPlayedDate']) + ' - ' + get_days_since_created(item_info['DateCreated']) +
                                                  ' -  Favorite: ' + str(item_info['UserData']['IsFavorite']) + ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'VideoID: ' + item_info['Id'])
                                else:
                                    item_details=('  ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + get_days_since_created(item_info['DateCreated']) +
                                                  ' -  Favorite: ' + str(item_info['UserData']['IsFavorite']) + ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'VideoID: ' + item_info['Id'])
                            except (KeyError, IndexError):
                                item_details='  ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + item_info['Id']
                                if bool(cfg.DEBUG):
                                    #DEBUG
                                    print('\nError encountered - Keep Video: \nitem: ' + str(item) + '\nitem_info' + str(item_info))
                            print(':[KEEPING] - ' + item_details)

############# Trailers #############

        if ((cfg.not_played_age_trailer >= 0) or (cfg.max_age_trailer >= 0)):

            IsPlayedState='True'
            #FieldsState='Type,Name,Id,UserData,ParentId,DateCreated'
            FieldsState='Id,Path'
            if (cfg.max_age_trailer >= 0):
                IsPlayedState=''

            StartIndex=0
            TotalItems=1
            ItemsChunk=1

            while (ItemsChunk > 0):

                url=(server_url + '/Users/' + user_key  + '/Items?includeItemTypes=Trailer&StartIndex=' + str(StartIndex) + '&Limit=' + str(ItemsChunk) + '&IsPlayed=' + str(IsPlayedState) + '&Fields=' + str(FieldsState) +
                    '&Recursive=true&SortBy=ParentIndexNumber,IndexNumber,Name&SortOrder=Ascending&enableImages=False&api_key=' + auth_key)

                if bool(cfg.DEBUG):
                    #DEBUG
                    print(url)

                data=requestURL(url, cfg.DEBUG, 'trailer_media_data', cfg.api_request_attempts)

                TotalItems = data['TotalRecordCount']
                StartIndex = StartIndex + ItemsChunk
                ItemsChunk = cfg.api_return_limit
                if ((StartIndex + ItemsChunk) >= (TotalItems)):
                    ItemsChunk = TotalItems - StartIndex

                #Determine if media item is to be deleted or kept
                for item in data['Items']:

                    media_found=True

                    #Get if media item path is monitored
                    item_info=get_additional_item_info(server_url, user_key, item['Id'], auth_key, 'trailer_item')

                    for mediasource in item_info['MediaSources']:

                        if (does_key_exist(mediasource, 'Type') and does_key_exist(mediasource, 'Size')):
                            if ((mediasource['Type'] == 'Placeholder') and (mediasource['Size'] == 0)):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        elif (does_key_exist(mediasource, 'Type')):
                            if (mediasource['Type'] == 'Placeholder'):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        elif (does_key_exist(mediasource, 'Size')):
                            if (mediasource['Size'] == 0):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        else:
                            itemIsMonitored=False
                            #itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])

                    #find trailer media items ready to delete
                    if ((item_info['Type'] == 'Trailer') and (itemIsMonitored)):

                        #establish max cutoff date for media item
                        if (cfg.max_age_trailer >= 0):
                            max_cut_off_date_trailer=datetime.strptime(item_info['DateCreated'], '%Y-%m-%dT%H:%M:%S.' + item_info['DateCreated'].split(".")[1]) + timedelta(cfg.max_age_trailer)
                        else:
                            max_cut_off_date_trailer=date_time_now = datetime.utcnow() + timedelta(1)

                        #Store media item's favorite state when multiple users are monitored and we want to keep media items based on any user favoriting the media item
                        if (cfg.keep_favorites_trailer == 2):
                            isfav_byUserId[user_key][item_info['Id']] = cfg.keep_favorites_trailer

                        #Get if media item path is whitelisted
                        itemIsWhiteListed, itemWhiteListedPath=get_isWhitelisted(item_info['Path'], user_wllib_json[currentPosition])

                        #Store media item's whitelist state when multiple users are monitored and we want to keep media items based on any user whitelisting the parent library
                        if (cfg.multiuser_whitelist_trailer == 1):
                            iswhitelist_byUserId[user_key][item_info['Id']] = itemIsWhiteListed
                            trailer_whitelists.add(itemWhiteListedPath)

                        if (
                           ((cfg.not_played_age_trailer >= 0) and
                           (item_info['UserData']['PlayCount'] >= 1) and
                           (cut_off_date_trailer > parse(item_info['UserData']['LastPlayedDate'])) and
                           (not bool(cfg.keep_favorites_trailer) or not item_info['UserData']['IsFavorite']) and
                           (not itemIsWhiteListed))
                           or
                           ((cfg.max_age_trailer >= 0) and
                           (max_cut_off_date_trailer <= datetime.utcnow()) and
                           (((not bool(cfg.keep_favorites_trailer)) or (not not item_info['UserData']['IsFavorite'])) and
                           ((not bool(cfg.max_keep_favorites_trailer)) or (not item_info['UserData']['IsFavorite']))) and
                           (not itemIsWhiteListed))
                           ):
                            try:
                                if (does_key_exist(item_info['UserData'], 'LastPlayedDate')):
                                    item_details=(' ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + get_days_since_played(item_info['UserData']['LastPlayedDate']) + ' - ' + get_days_since_created(item_info['DateCreated']) +
                                                  ' -  Favorite: ' + str(item_info['UserData']['IsFavorite']) + ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'TrailerID: ' + item_info['Id'])
                                else:
                                    item_details=(' ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + get_days_since_created(item_info['DateCreated']) +
                                                  ' -  Favorite: ' + str(item_info['UserData']['IsFavorite']) + ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'TrailerID: ' + item_info['Id'])
                            except (KeyError, IndexError):
                                item_details=' ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + item_info['Id']
                                if bool(cfg.DEBUG):
                                    #DEBUG
                                    print('\nError encountered - Delete Trailer: \nitem: ' + str(item) + '\nitem_info' + str(item_info))
                            print(':*[DELETE] - ' + item_details)
                            deleteItems.append(item)
                        else:
                            try:
                                if (does_key_exist(item_info['UserData'], 'LastPlayedDate')):
                                    item_details=(' ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + get_days_since_played(item_info['UserData']['LastPlayedDate']) + ' - ' + get_days_since_created(item_info['DateCreated']) +
                                                  ' -  Favorite: ' + str(item_info['UserData']['IsFavorite']) + ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'TrailerID: ' + item_info['Id'])
                                else:
                                    item_details=(' ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + get_days_since_created(item_info['DateCreated']) +
                                                  ' -  Favorite: ' + str(item_info['UserData']['IsFavorite']) + ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'TrailerID: ' + item_info['Id'])
                            except (KeyError, IndexError):
                                item_details=' ' + item_info['Type'] + ' - ' + item_info['Name'] + ' - ' + item_info['Id']
                                if bool(cfg.DEBUG):
                                    #DEBUG
                                    print('\nError encountered - Keep Trailer: \nitem: ' + str(item) + '\nitem_info' + str(item_info))
                            print(':[KEEPING] - ' + item_details)

############# Audio #############

        if ((cfg.not_played_age_audio >= 0) or (cfg.max_age_audio >= 0)):

            trackgenre_mask=int('00000100', 2)
            albumgenre_mask=int('00001000', 2)

            IsPlayedState='True'
            #FieldsState='Type,Name,Id,UserData,Studios,Artists,Album,ParentId,DateCreated'
            FieldsState='Id,Path'
            if (cfg.max_age_audio >= 0):
                IsPlayedState=''
            #if ((trackgenre_mask & adv_settings) or (albumgenre_mask & adv_settings)):
                #FieldsState=FieldsState + ',Genres'

            StartIndex=0
            TotalItems=1
            ItemsChunk=1

            while (ItemsChunk > 0):

                url=(server_url + '/Users/' + user_key  + '/Items?includeItemTypes=Audio&StartIndex=' + str(StartIndex) + '&Limit=' + str(ItemsChunk) + '&IsPlayed=' + str(IsPlayedState) + '&Fields=' + str(FieldsState) +
                    '&Recursive=true&SortBy=AlbumArtist,ParentIndexNumber,IndexNumber,Name&SortOrder=Ascending&enableImages=False&api_key=' + auth_key)

                if bool(cfg.DEBUG):
                    #DEBUG
                    print(url)

                data=requestURL(url, cfg.DEBUG, 'audio_media_data', cfg.api_request_attempts)

                TotalItems = data['TotalRecordCount']
                StartIndex = StartIndex + ItemsChunk
                ItemsChunk = cfg.api_return_limit
                if ((StartIndex + ItemsChunk) >= (TotalItems)):
                    ItemsChunk = TotalItems - StartIndex

                #Determine if media item is to be deleted or kept
                for item in data['Items']:

                    media_found=True

                    #Get if media item path is monitored
                    item_info=get_additional_item_info(server_url, user_key, item['Id'], auth_key, 'audio_item')

                    for mediasource in item_info['MediaSources']:

                        if (does_key_exist(mediasource, 'Type') and does_key_exist(mediasource, 'Size')):
                            if ((mediasource['Type'] == 'Placeholder') and (mediasource['Size'] == 0)):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        elif (does_key_exist(mediasource, 'Type')):
                            if (mediasource['Type'] == 'Placeholder'):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        elif (does_key_exist(mediasource, 'Size')):
                            if (mediasource['Size'] == 0):
                                itemIsMonitored=False
                            else:
                                itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])
                        else:
                            itemIsMonitored=False
                            #itemIsMonitored=get_isBlacklisted(item_info['Path'], user_bllib_json[currentPosition])

                    #find audio media items ready to delete
                    if ((item_info['Type'] == 'Audio') and (itemIsMonitored)):

                        #establish max cutoff date for media item
                        if (cfg.max_age_audio >= 0):
                            max_cut_off_date_audio=datetime.strptime(item_info['DateCreated'], '%Y-%m-%dT%H:%M:%S.' + item_info['DateCreated'].split(".")[1]) + timedelta(cfg.max_age_audio)
                        else:
                            max_cut_off_date_audio=date_time_now = datetime.utcnow() + timedelta(1)

                        #Get if track, album, or artist is set as favorite
                        itemisfav_AUDIOtaa=get_isfav_AUDIOtaa(isfav_AUDIOtaa, item, server_url, user_key, auth_key)

                        #Get if media item path is whitelisted
                        itemIsWhiteListed, itemWhiteListedPath=get_isWhitelisted(item_info['Path'], user_wllib_json[currentPosition])

                        #Store media item's favorite state when multiple users are monitored and we want to keep media items based on any user favoriting the media item
                        if (cfg.keep_favorites_audio == 2):
                            isfav_byUserId[user_key][item_info['Id']] = itemisfav_AUDIOtaa

                        #Store media item's whitelist state when multiple users are monitored and we want to keep media items based on any user whitelisting the parent library
                        if (cfg.multiuser_whitelist_audio == 1):
                            iswhitelist_byUserId[user_key][item_info['Id']] = itemIsWhiteListed
                            audio_whitelists.add(itemWhiteListedPath)

                        if (
                           ((cfg.not_played_age_audio >= 0) and
                           (item_info['UserData']['PlayCount'] >= 1) and
                           (cut_off_date_audio > parse(item_info['UserData']['LastPlayedDate'])) and
                           (not bool(cfg.keep_favorites_audio) or (not itemisfav_AUDIOtaa)) and
                           (not itemIsWhiteListed))
                           or
                           ((cfg.max_age_movie >= 0) and
                           (max_cut_off_date_movie <= datetime.utcnow()) and
                           (((not bool(cfg.keep_favorites_audio)) or (not itemisfav_AUDIOtaa)) and
                           ((not bool(cfg.max_keep_favorites_audio)) or (not itemisfav_AUDIOtaa))) and
                           (not itemIsWhiteListed))
                           ):
                            try:
                                if (does_key_exist(item_info['UserData'], 'LastPlayedDate')):
                                    item_details=('  ' + item_info['Type'] + ' - Track: ' + item_info['Name'] + ' - Album: ' + item_info['Album'] + ' - Artist: ' + item_info['Artists'][0] + ' - Record Label: ' + item_info['Studios'][0]['Name'] +
                                                  ' - ' + get_days_since_played(item_info['UserData']['LastPlayedDate']) + ' - ' + get_days_since_created(item_info['DateCreated']) + ' - Favorite: ' + str(itemisfav_AUDIOtaa) +
                                                  ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'TrackID: ' + item_info['Id'])
                                else:
                                    item_details=('  ' + item_info['Type'] + ' - Track: ' + item_info['Name'] + ' - Album: ' + item_info['Album'] + ' - Artist: ' + item_info['Artists'][0] + ' - Record Label: ' + item_info['Studios'][0]['Name'] +
                                                  ' - ' + get_days_since_created(item_info['DateCreated']) + ' - Favorite: ' + str(itemisfav_AUDIOtaa) +
                                                  ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'TrackID: ' + item_info['Id'])
                            except (KeyError, IndexError):
                                item_details='  ' + item_info['Type'] + ' - Track: ' + item_info['Name'] + ' - ' + item_info['Id']
                                if bool(cfg.DEBUG):
                                    #DEBUG
                                    print('\nError encountered - Delete Audio: \nitem: ' + str(item) + '\nitem_info' + str(item_info))
                            print(':*[DELETE] - ' + item_details)
                            deleteItems.append(item)
                        else:
                            try:
                                if (does_key_exist(item_info['UserData'], 'LastPlayedDate')):
                                    item_details=('  ' + item_info['Type'] + ' - Track: ' + item_info['Name'] + ' - Album: ' + item_info['Album'] + ' - Artist: ' + item_info['Artists'][0] + ' - Record Label: ' + item_info['Studios'][0]['Name'] +
                                                  ' - ' + get_days_since_played(item_info['UserData']['LastPlayedDate']) + ' - ' + get_days_since_created(item_info['DateCreated']) + ' - Favorite: ' + str(itemisfav_AUDIOtaa) +
                                                  ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'TrackID: ' + item_info['Id'])
                                else:
                                    item_details=('  ' + item_info['Type'] + ' - Track: ' + item_info['Name'] + ' - Album: ' + item_info['Album'] + ' - Artist: ' + item_info['Artists'][0] + ' - Record Label: ' + item_info['Studios'][0]['Name'] +
                                                  ' - ' + get_days_since_created(item_info['DateCreated']) + ' - Favorite: ' + str(itemisfav_AUDIOtaa) +
                                                  ' - Whitelisted: ' + str(itemIsWhiteListed) + ' - ' + 'TrackID: ' + item_info['Id'])
                            except (KeyError, IndexError):
                                item_details='  ' + item_info['Type'] + ' - Track: ' + item_info['Name'] + ' - ' + item_info['Id']
                                if bool(cfg.DEBUG):
                                    #DEBUG
                                    print('\nError encountered - Keep Audio: \nitem: ' + str(item) + '\nitem_info' + str(item_info))
                            print(':[KEEPING] - ' + item_details)

        if (not all_media_disabled):
            if not (media_found):
                print('[NO PLAYED ITEMS]')

        print('-----------------------------------------------------------')
        currentPosition+=1

    #When multiple users and keep_favorite_xyz==2 Determine media items to keep and remove them from deletion list
    #When not multiple users this will just clean up the deletion list
    deleteItems=get_isfav_MultiUser(user_keys_json, isfav_byUserId, deleteItems)

    #When multiple users and multiuser_whitelist_xyz==1 Determine media items to keep and remove them from deletion list
    #When not multiple users this will just clean up the deletion list
    #deleteItems=get_iswhitelist_MultiUser_byId(user_keys_json, iswhitelist_byUserId, deleteItems)

    #When multiple users and multiuser_whitelist_xyz==1 Determine media items to keep and remove them from deletion list
    deleteItems=get_iswhitelist_MultiUser_byPath(user_keys_json, list(movie_whitelists), deleteItems)
    deleteItems=get_iswhitelist_MultiUser_byPath(user_keys_json, list(episode_whitelists), deleteItems)
    deleteItems=get_iswhitelist_MultiUser_byPath(user_keys_json, list(video_whitelists), deleteItems)
    deleteItems=get_iswhitelist_MultiUser_byPath(user_keys_json, list(trailer_whitelists), deleteItems)
    deleteItems=get_iswhitelist_MultiUser_byPath(user_keys_json, list(audio_whitelists), deleteItems)

    if bool(cfg.DEBUG):
        print('-----------------------------------------------------------')
        print('')
        print('isfav_MOVIE: ')
        print(isfav_MOVIE)
        print('')
        print('isfav_TVessn: ')
        print(isfav_TVessn)
        print('')
        print('isfav_AUDIOtaa: ')
        print(isfav_AUDIOtaa)
        print('')

    print('\n')
    return(deleteItems)


#list and delete items past played threshold
def list_delete_items(deleteItems):
    #List items to be deleted
    print('-----------------------------------------------------------')
    print('Summary Of Deleted Media:')
    if not bool(cfg.remove_files):
        print('* Trial Run            ')
        print('* remove_files=0       ')
        print('* No Media Deleted     ')
        print('* Items = ' + str(len(deleteItems)))
        print('-----------------------------------------------------------')
    else:
        print('* Items Deleted = ' + str(len(deleteItems)) + '    *')
        print('-----------------------------------------------------------')

    if len(deleteItems) > 0:
        for item in deleteItems:
            if item['Type'] == 'Movie':
                item_details='  ' + item['Type'] + ' - ' + item['Name'] + ' - ' + item['Id']
            elif item['Type'] == 'Episode':
                try:
                    item_details=item['Type'] + ' - ' + item['SeriesName'] + ' - ' + get_season_episode(item['ParentIndexNumber'], item['IndexNumber']) + ' - ' + item['Name'] + ' - ' + item['Id']
                except (KeyError, IndexError):
                    item_details='  ' + item['Type'] + ' - ' + item['Name'] + ' - ' + item['Id']
                    if bool(cfg.DEBUG):
                        #DEBUG
                        print('Error encountered - Delete Episode: \n\n' + str(item))
            elif item['Type'] == 'Video':
                item_details='  ' + item['Type'] + ' - ' + item['Name'] + ' - ' + item['Id']
            elif item['Type'] == 'Trailer':
                item_details=item['Type'] + ' - ' + item['Name'] + ' - ' + item['Id']
            elif item['Type'] == 'Audio':
                item_details=item['Type'] + ' - ' + item['Name'] + ' - ' + item['Id']
            else: # item['Type'] == 'Unknown':
                pass
            #Delete media item
            delete_item(item['Id'])
            print('[DELETED] ' + item_details)
    else:
        print('[NO ITEMS TO DELETE]')

    print('-----------------------------------------------------------')
    print('\n')
    print('-----------------------------------------------------------')
    print('Done.')
    print('-----------------------------------------------------------')
    print('')


#Check select config variables are an expected value
def cfgCheck():

    errorfound=False
    error_found_in_media_cleaner_config_py=''
    #need to find clean way to put cfg.variable_names in a dict/list/etc... and use the dict/list/etc... to call the varibles by name in a for loop
    check=cfg.not_played_age_movie
    check_not_played_age_movie=check
    if (
        not ((type(check) is int) and
        (check >= -1) and
        (check <= 365000000))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: not_played_age_movie must be an integer; valid range -1 thru 365000000\n'

    check=cfg.not_played_age_episode
    check_not_played_age_episode=check
    if (
        not ((type(check) is int) and
        (check >= -1) and
        (check <= 365000000))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: not_played_age_episode must be an integer; valid range -1 thru 365000000\n'

    check=cfg.not_played_age_video
    check_not_played_age_video=check
    if (
        not ((type(check) is int) and
        (check >= -1) and
        (check <= 365000000))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: not_played_age_video must be an integer; valid range -1 thru 365000000\n'

    check=cfg.not_played_age_trailer
    check_not_played_age_trailer=check
    if (
        not ((type(check) is int) and
        (check >= -1) and
        (check <= 365000000))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: not_played_age_trailer must be an integer; valid range -1 thru 365000000\n'

    check=cfg.not_played_age_audio
    check_not_played_age_audio=check
    if (
        not ((type(check) is int) and
        (check >= -1) and
        (check <= 365000000))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: not_played_age_audio must be an integer; valid range -1 thru 365000000\n'

    check=cfg.keep_favorites_movie
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 2))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: keep_favorites_movie must be an integer; valid range 0 thru 2\n'

    check=cfg.keep_favorites_episode
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 2))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: keep_favorites_episode must be an integer; valid range 0 thru 2\n'

    check=cfg.keep_favorites_video
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 2))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: keep_favorites_video must be an integer; valid range 0 thru 2\n'

    check=cfg.keep_favorites_trailer
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 2))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: keep_favorites_trailer must be an integer; valid range 0 thru 2\n'

    check=cfg.keep_favorites_audio
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 2))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: keep_favorites_audio must be an integer; valid range 0 thru 2\n'

    check=cfg.keep_favorites_advanced
    if (
        not ((type(check) is str) and
        (int(check, 2) >= 0) and
        (int(check, 2) <= 255) and
        (len(check) >= 6) and
        (len(check) <= 8))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: keep_favorites_advanced should be an 8-digit binary string; valid range binary - 00000000 thru 11111111 (decimal - 0 thru 255)\n'

    check=cfg.keep_favorites_advanced_any
    if (
        not ((type(check) is str) and
        (int(check, 2) >= 0) and
        (int(check, 2) <= 255) and
        (len(check) >= 6) and
        (len(check) <= 8))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: keep_favorites_advanced_any should be an 8-digit binary string; valid range binary - 00000000 thru 11111111 (decimal - 0 thru 255)\n'

    check=cfg.multiuser_whitelist_movie
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 1))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: multiuser_whitelist_movie must be an integer; valid range 0 thru 1\n'

    check=cfg.multiuser_whitelist_episode
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 1))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: multiuser_whitelist_episode must be an integer; valid range 0 thru 1\n'

    check=cfg.multiuser_whitelist_video
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 1))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: multiuser_whitelist_video must be an integer; valid range 0 thru 1\n'

    check=cfg.multiuser_whitelist_trailer
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 1))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: multiuser_whitelist_trailer must be an integer; valid range 0 thru 1\n'

    check=cfg.multiuser_whitelist_audio
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 1))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: multiuser_whitelist_audio must be an integer; valid range 0 thru 1\n'

    check=cfg.remove_files
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 1))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: remove_files must be an integer; valid values 0 and 1\n'

    check=cfg.max_age_movie
    if (
        not ((type(check) is int) and
        (check >= -1) and
        (check <= 365000000) and
        (((check >= check_not_played_age_movie) and (check >= 0)) or
        (check == -1)))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: max_age_movie must be an integer greater than corresponding not_played_age_xyz; valid range -1 thru 365000000\n'

    check=cfg.max_age_episode
    if (
        not ((type(check) is int) and
        (check >= -1) and
        (check <= 365000000) and
        (((check >= check_not_played_age_episode) and (check >= 0)) or
        (check == -1)))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: max_age_episode must be an integer greater than corresponding not_played_age_xyz; valid range -1 thru 365000000\n'

    check=cfg.max_age_video
    if (
        not ((type(check) is int) and
        (check >= -1) and
        (check <= 365000000) and
        (((check >= check_not_played_age_video) and (check >= 0)) or
        (check == -1)))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: max_age_video must be an integer greater than corresponding not_played_age_xyz; valid range -1 thru 365000000\n'

    check=cfg.max_age_trailer
    if (
        not ((type(check) is int) and
        (check >= -1) and
        (check <= 365000000) and
        (((check >= check_not_played_age_trailer) and (check >= 0)) or
        (check == -1)))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: max_age_trailer must be an integer greater than corresponding not_played_age_xyz; valid range -1 thru 365000000\n'

    check=cfg.max_age_audio
    if (
        not ((type(check) is int) and
        (check >= -1) and
        (check <= 365000000) and
        (((check >= check_not_played_age_audio) and (check >= 0)) or
        (check == -1)))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: max_age_audio must be an integer greater than corresponding not_played_age_xyz; valid range -1 thru 365000000\n'

    check=cfg.max_keep_favorites_movie
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 1))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: max_keep_favorites_movie must be an integer; valid range 0 thru 1\n'

    check=cfg.max_keep_favorites_episode
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 1))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: max_keep_favorites_episode must be an integer; valid range 0 thru 1\n'

    check=cfg.max_keep_favorites_video
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 1))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: max_keep_favorites_video must be an integer; valid range 0 thru 1\n'

    check=cfg.max_keep_favorites_trailer
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 1))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: max_keep_favorites_trailer must be an integer; valid range 0 thru 1\n'

    check=cfg.max_keep_favorites_audio
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 1))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: max_keep_favorites_audio must be an integer; valid range 0 thru 1\n'

    check=cfg.server_brand
    if (
        not (type(check) is str)
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: server_brand must be a string\n'

    check=cfg.server_url
    if (
        not (type(check) is str)
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: server_url must be a string\n'

    check=cfg.admin_username
    if (
        not (type(check) is str)
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: admin_username must be a string\n'

    check=cfg.access_token
    if (
        not ((type(check) is str) and
        (len(check) == 32) and
        (str(check).isalnum()))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: access_token must be a 32-character alphanumeric string\n'

    check=cfg.user_keys
    check_list=json.loads(check)
    check_user_keys_length=len(check_list)
    for check_irt in check_list:
        if (
            not ((type(check_irt) is str) and
            (len(check_irt) == 32) and
            (str(check_irt).isalnum()))
           ):
            errorfound=True
            error_found_in_media_cleaner_config_py+='TypeError: user_keys must be a single list with commas separating multiple users\' keys; each user key must be a 32-character alphanumeric string\n'

    #check=cfg.script_behavior
    #if (
        #not ((type(check_irt) is str) and
        #((check == 'whitelist') or (check == 'blacklist')))
       #):
            #errorfound=True
            #error_found_in_media_cleaner_config_py+='TypeError: script_behavior must be a string; valid values \'whitelist\' or \'blacklist\'\n'

    check=cfg.user_bl_libs
    check_list=json.loads(check)
    check_user_bllibs_length=len(check_list)
    for check_irt in check_list:
        if (
            not ((type(check_irt) is str) and
            (check_user_keys_length == check_user_bllibs_length))
           ):
            errorfound=True
            error_found_in_media_cleaner_config_py+='TypeError: user_bl_libs must be a single list with commas separating multiple users\' monitored libraries; each user\'s libraries must also be comma seperated within the string\n'

    check=cfg.user_wl_libs
    check_list=json.loads(check)
    check_user_wllibs_length=len(check_list)
    for check_irt in check_list:
        if (
            not ((type(check_irt) is str) and
            (check_user_keys_length == check_user_wllibs_length))
           ):
            errorfound=True
            error_found_in_media_cleaner_config_py+=('TypeError: user_wl_libs must be a single list with commas separating multiple users\' whitelisted libraries; each user\'s whitelisted libraries must also be comma seperated within the string\n')

    check=cfg.api_request_attempts
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 16))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: api_request_attempts must be an integer; valid range 0 thru 16\n'

    check=cfg.api_return_limit
    if (
        not ((type(check) is int) and
        (check >= 1) and
        (check <= 10000))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: api_return_limit must be an integer; valid range 0 thru 10000\n'

    check=cfg.DEBUG
    if (
        not ((type(check) is int) and
        (check >= 0) and
        (check <= 1))
       ):
        errorfound=True
        error_found_in_media_cleaner_config_py+='TypeError: DEBUG must be an integer; valid values 0 and 1'

    if (errorfound):
        error_found_in_media_cleaner_config_py=error_found_in_media_cleaner_config_py.replace('TypeError: ','',1)
        raise TypeError(error_found_in_media_cleaner_config_py)

############# START OF SCRIPT #############

try:
    #try importing the media_cleaner_config.py file
    #if media_cleaner_config.py file does not exsit go to except and create one
    import media_cleaner_config as cfg

    #try setting DEBUG variable from media_cleaner_config.py file
    #if DEBUG does not exsit go to except and completely rebuild the media_cleaner_config.py file
    check=cfg.DEBUG
    #removing DEBUG from media_cleaner_config.py file is sort of configuration reset

    #depending on what is missing from media_cleaner_config.py file; try to only ask for certain input
    if (
        not hasattr(cfg, 'not_played_age_movie') or
        not hasattr(cfg, 'not_played_age_episode') or
        not hasattr(cfg, 'not_played_age_video') or
        not hasattr(cfg, 'not_played_age_trailer') or
        not hasattr(cfg, 'not_played_age_audio') or

        not hasattr(cfg, 'keep_favorites_movie') or
        not hasattr(cfg, 'keep_favorites_episode') or
        not hasattr(cfg, 'keep_favorites_video') or
        not hasattr(cfg, 'keep_favorites_trailer') or
        not hasattr(cfg, 'keep_favorites_audio') or

        not hasattr(cfg, 'keep_favorites_advanced') or
        not hasattr(cfg, 'keep_favorites_advanced_any') or

        not hasattr(cfg, 'multiuser_whitelist_movie') or
        not hasattr(cfg, 'multiuser_whitelist_episode') or
        not hasattr(cfg, 'multiuser_whitelist_video') or
        not hasattr(cfg, 'multiuser_whitelist_trailer') or
        not hasattr(cfg, 'multiuser_whitelist_audio') or

        not hasattr(cfg, 'remove_files') or

        not hasattr(cfg, 'max_age_movie') or
        not hasattr(cfg, 'max_age_episode') or
        not hasattr(cfg, 'max_age_video') or
        not hasattr(cfg, 'max_age_trailer') or
        not hasattr(cfg, 'max_age_audio') or

        not hasattr(cfg, 'max_keep_favorites_movie') or
        not hasattr(cfg, 'max_keep_favorites_episode') or
        not hasattr(cfg, 'max_keep_favorites_video') or
        not hasattr(cfg, 'max_keep_favorites_trailer') or
        not hasattr(cfg, 'max_keep_favorites_audio') or

        not hasattr(cfg, 'server_brand') or
        not hasattr(cfg, 'server_url') or

        not hasattr(cfg, 'admin_username') or
        not hasattr(cfg, 'access_token') or

        not hasattr(cfg, 'user_keys') or

        #not hasattr(cfg, 'script_behavior') or

        not hasattr(cfg, 'user_bl_libs') or
        not hasattr(cfg, 'user_wl_libs') or

        not hasattr(cfg, 'api_request_attempts') or
        not hasattr(cfg, 'api_return_limit')
       ):
        if (
            not hasattr(cfg, 'server_brand') or
            not hasattr(cfg, 'server_url') or

            not hasattr(cfg, 'admin_username') or
            not hasattr(cfg, 'access_token') or

            not hasattr(cfg, 'user_keys') or

            #not hasattr(cfg, 'script_behavior') or

            not hasattr(cfg, 'user_bl_libs') or
            not hasattr(cfg, 'user_wl_libs') or

            not hasattr(cfg, 'api_request_attempts') or
            not hasattr(cfg, 'api_return_limit')
           ):

            if hasattr(cfg, 'server_brand'):
                delattr(cfg, 'server_brand')
            if hasattr(cfg, 'server_url'):
                delattr(cfg, 'server_url')

            if hasattr(cfg, 'admin_username'):
                delattr(cfg, 'admin_username')
            if hasattr(cfg, 'access_token'):
                delattr(cfg, 'access_token')

            if hasattr(cfg, 'user_keys'):
                delattr(cfg, 'user_keys')

            #if hasattr(cfg, 'script_behavior'):
                #delattr(cfg, 'script_behavior')

            if hasattr(cfg, 'user_bl_libs'):
                delattr(cfg, 'user_bl_libs')
            if hasattr(cfg, 'user_wl_libs'):
                delattr(cfg, 'user_wl_libs')

            if hasattr(cfg, 'api_request_attempts'):
                delattr(cfg, 'api_request_attempts')
            if hasattr(cfg, 'api_return_limit'):
                delattr(cfg, 'api_return_limit')

            print('-----------------------------------------------------------')
            server_brand=get_brand()

            print('-----------------------------------------------------------')
            server=get_url()
            print('-----------------------------------------------------------')
            port=get_port()
            print('-----------------------------------------------------------')
            server_base=get_base(server_brand)
            if (len(port)):
                server_url=server + ':' + port + '/' + server_base
            else:
                server_url=server + '/' + server_base
            print('-----------------------------------------------------------')

            username=get_admin_username()
            print('-----------------------------------------------------------')
            password=get_admin_password()
            print('-----------------------------------------------------------')
            auth_key=get_auth_key(server_url, username, password, server_brand)

            script_behavior=get_cleaning_behavior()
            print('-----------------------------------------------------------')

            user_keys_and_bllibs, user_keys_and_wllibs=get_users_and_paths(server_url, auth_key)

            userkeys_list=[]
            userbllibs_list=[]
            userkeys_wllibs_list=[]
            userwllibs_list=[]

            for userkey, userlib in user_keys_and_bllibs.items():
                userkeys_list.append(userkey)
                userbllibs_list.append(userbllib)

            for userkey, userwllib in user_keys_and_wllibs.items():
                userkeys_wllibs_list.append(userkey)
                userwllibs_list.append(userwllib)

            user_keys=json.dumps(userkeys_list)
            user_bl_libs=json.dumps(userbllibs_list)
            user_wl_libs=json.dumps(userwllibs_list)

            print('-----------------------------------------------------------')

        #warn user the configuration file is not complete
        #the missing varibles are not saved and the setup data will need to be manually entered the next time the script is run
        #a new media_cleaner_config.py file will need to be completed or manually updated without duplicates
        print('\n')
        print('-----------------------------------------------------------')
        print('ATTENTION!!!')
        print('Old or incomplete config in use.')
        print('1) Delete media_cleaner_config.py and run this again to create a new config.')
        print('   Or')
        print('2) Delete DEBUG from media_cleaner_config.py and run this again to create a new config.')
        print('-----------------------------------------------------------')
        print('Matching value(s) in media_cleaner_config.py ignored.')
        print('Using the below config value(s) for this run:')
        print('-----------------------------------------------------------')

        if not hasattr(cfg, 'not_played_age_movie'):
            print('not_played_age_movie=-1')
            setattr(cfg, 'not_played_age_movie', -1)
        if not hasattr(cfg, 'not_played_age_episode'):
            print('not_played_age_episode=-1')
            setattr(cfg, 'not_played_age_episode', -1)
        if not hasattr(cfg, 'not_played_age_video'):
            print('not_played_age_video=-1')
            setattr(cfg, 'not_played_age_video', -1)
        if not hasattr(cfg, 'not_played_age_trailer'):
            print('not_played_age_trailer=-1')
            setattr(cfg, 'not_played_age_trailer', -1)
        if not hasattr(cfg, 'not_played_age_audio'):
            print('not_played_age_audio=-1')
            setattr(cfg, 'not_played_age_audio', -1)

        if not hasattr(cfg, 'keep_favorites_movie'):
            print('keep_favorites_movie=1')
            setattr(cfg, 'keep_favorites_movie', 1)
        if not hasattr(cfg, 'keep_favorites_episode'):
            print('keep_favorites_episode=1')
            setattr(cfg, 'keep_favorites_episode', 1)
        if not hasattr(cfg, 'keep_favorites_video'):
            print('keep_favorites_video=1')
            setattr(cfg, 'keep_favorites_video', 1)
        if not hasattr(cfg, 'keep_favorites_trailer'):
            print('keep_favorites_trailer=1')
            setattr(cfg, 'keep_favorites_trailer', 1)
        if not hasattr(cfg, 'keep_favorites_audio'):
            print('keep_favorites_audio=1')
            setattr(cfg, 'keep_favorites_audio', 1)

        if not hasattr(cfg, 'keep_favorites_advanced'):
            print('keep_favorites_advanced=00000001')
            setattr(cfg, 'keep_favorites_advanced', '00000001')
        if not hasattr(cfg, 'keep_favorites_advanced_any'):
            print('keep_favorites_advanced_any=00000000')
            setattr(cfg, 'keep_favorites_advanced_any', '00000000')

        if not hasattr(cfg, 'multiuser_whitelist_movie'):
            print('multiuser_whitelist_movie=1')
            setattr(cfg, 'multiuser_whitelist_movie', 1)

        if not hasattr(cfg, 'multiuser_whitelist_episode'):
            print('multiuser_whitelist_episode=1')
            setattr(cfg, 'multiuser_whitelist_episode', 1)

        if not hasattr(cfg, 'multiuser_whitelist_video'):
            print('multiuser_whitelist_video=1')
            setattr(cfg, 'multiuser_whitelist_video', 1)

        if not hasattr(cfg, 'multiuser_whitelist_trailer'):
            print('multiuser_whitelist_trailer=1')
            setattr(cfg, 'multiuser_whitelist_trailer', 1)

        if not hasattr(cfg, 'multiuser_whitelist_audio'):
            print('multiuser_whitelist_audio=1')
            setattr(cfg, 'multiuser_whitelist_audio', 1)

        if not hasattr(cfg, 'remove_files'):
            print('remove_files=0')
            setattr(cfg, 'remove_files', 0)

        if not hasattr(cfg, 'max_age_movie'):
            print('max_age_movie=-1')
            setattr(cfg, 'max_age_movie', -1)
        if not hasattr(cfg, 'max_age_episode'):
            print('max_age_episode=-1')
            setattr(cfg, 'max_age_episode', -1)
        if not hasattr(cfg, 'max_age_video'):
            print('max_age_video=-1')
            setattr(cfg, 'max_age_video', -1)
        if not hasattr(cfg, 'max_age_trailer'):
            print('max_age_trailer=-1')
            setattr(cfg, 'max_age_trailer', -1)
        if not hasattr(cfg, 'max_age_audio'):
            print('max_age_audio=-1')
            setattr(cfg, 'max_age_audio', -1)

        if not hasattr(cfg, 'max_keep_favorites_movie'):
            print('max_keep_favorites_movie=1')
            setattr(cfg, 'max_keep_favorites_movie', 1)
        if not hasattr(cfg, 'max_keep_favorites_episode'):
            print('max_keep_favorites_episode=1')
            setattr(cfg, 'max_keep_favorites_episode', 1)
        if not hasattr(cfg, 'max_keep_favorites_video'):
            print('max_keep_favorites_video=1')
            setattr(cfg, 'max_keep_favorites_video', 1)
        if not hasattr(cfg, 'max_keep_favorites_trailer'):
            print('max_keep_favorites_trailer=1')
            setattr(cfg, 'max_keep_favorites_trailer', 1)
        if not hasattr(cfg, 'max_keep_favorites_audio'):
            print('max_keep_favorites_audio=1')
            setattr(cfg, 'max_keep_favorites_audio', 1)

        if not hasattr(cfg, 'server_brand'):
            print('server_brand=\'' + str(server_brand) + '\'')
            setattr(cfg, 'server_brand', server_brand)
        if not hasattr(cfg, 'server_url'):
            print('server_url=\'' + str(server_url) + '\'')
            setattr(cfg, 'server_url', server_url)

        if not hasattr(cfg, 'admin_username'):
            print('admin_username=\'' + str(username) + '\'')
            setattr(cfg, 'admin_username', username)
        if not hasattr(cfg, 'access_token'):
            print('access_token=\'' + str(auth_key) + '\'')
            setattr(cfg, 'access_token', auth_key)

        if not hasattr(cfg, 'user_keys'):
            print('user_keys=\'' + str(user_keys) + '\'')
            setattr(cfg, 'user_keys', user_keys)

        #if not hasattr(cfg, 'script_behavior'):
            #print('script_behavior=\'' + str(script_behavior) + '\'')
            #setattr(cfg, 'script_behavior', script_behavior)

        if not hasattr(cfg, 'user_bl_libs'):
            print('user_bl_libs=\'' + str(user_bl_libs) + '\'')
            setattr(cfg, 'user_bl_libs', user_bl_libs)
        if not hasattr(cfg, 'user_wl_libs'):
            print('user_wl_libs=\'' + str(user_wl_libs) + '\'')
            setattr(cfg, 'user_wl_libs', user_wl_libs)

        if not hasattr(cfg, 'api_request_attempts'):
            print('api_request_attempts=\'' + str(api_request_attempts) + '\'')
            setattr(cfg, 'api_request_attempts', api_request_attempts)
        if not hasattr(cfg, 'api_return_limit'):
            print('api_return_limit=\'' + str(api_return_limit) + '\'')
            setattr(cfg, 'api_return_limit', api_return_limit)

        #print('DEBUG=' + str(cfg.DEBUG))

        print('-----------------------------------------------------------')
        print ('\n')

#the except
except (AttributeError, ModuleNotFoundError):
    #we are here because the media_cleaner_config.py file does not exist
    #this is either the first time the script is running or media_cleaner_config.py file was deleted
    #when this happens create a new media_cleaner_config.py file
    #another possible reason we are here...
    #the above attempt to set check=cfg.DEBUG failed likely because DEBUG is missing from the media_cleaner_config.py file
    #when this happens create a new media_cleaner_config.py file
    generate_config()

    #exit gracefully after setup
    exit(0)

#check config values are what we expect them to be
cfgCheck()

#now we can get media items that are ready to be deleted;
deleteItems=get_items(cfg.server_url, cfg.user_keys, cfg.access_token)

#show and delete media items
list_delete_items(deleteItems)

############# END OF SCRIPT #############
