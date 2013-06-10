#!/usr/bin/env python
###############################################################################################
#  Author: 
__author__ = '<a href="mailto:debuti@gmail.com">Borja Garcia</a>'
# Program: 
__program__ = 'autotag'
# Package:
__package__ = ''
# Descrip: 
__description__ = ''''''
# Version: 
__version__ = '0.0.0'
#    Date:
__date__ = '20130610'
# License: This script doesn't require any license since it's not intended to be redistributed.
#          In such case, unless stated otherwise, the purpose of the author is to follow GPLv3.
# History: 
#          0.0.0 (20130610)
#            -Initial release
###############################################################################################

# Imports
import logging
import sys
import doctest
import datetime, time
import os
import optparse
import inspect
import ConfigParser
import glob
import traceback
import json
import urllib

# Parameters, Globals n' Constants
KIBI = 1024
MEBI = 1024 * KIBI
LOG_MODE = "Screen"
LOG_LEVEL = logging.DEBUG
LOG_MAX_BYTES = 1 * MEBI

APIKEY = "TKTD9246TZYXHOE2P"

realScriptPath = os.path.realpath(__file__)
realScriptDirectory = os.path.dirname(realScriptPath)
callingDirectory = os.getcwd()
if os.path.isabs(__file__ ):
    linkScriptPath = __file__
else:
    linkScriptPath = os.path.join(callingDirectory, __file__)
linkScriptDirectory = os.path.dirname(linkScriptPath)

propertiesName = __program__ + ".properties"
propertiesPath = os.path.join(realScriptDirectory, '..', propertiesName) 

logFileName = __program__ + '_' + time.strftime("%Y%m%d%H%M%S") + '.log'
logDirectory = os.path.join(realScriptDirectory, '..', 'logs')
logPath = os.path.join(logDirectory, logFileName)
loggerName = __package__ + "." + __program__

# User-libs imports (This is the correct way to do this)
libPath =  os.path.join(realScriptDirectory, '..', 'lib')
sys.path.insert(0, libPath)
for infile in glob.glob(os.path.join(libPath, '*.*')):
    sys.path.insert(0, infile)
    
import thepyutilities.shellutils as shellutils


# Usage function, logs, utils and check input
def openLog(mode, desiredLevel):
    '''This function is for initialize the logging job
    '''
    def openScreenLog(formatter, desiredLevel):
        logging.basicConfig(level = desiredLevel, format = formatter)
       
    def openScreenAndFileLog(fileName, formatter, desiredLevel):
        logger = logging.getLogger('')
        logger.setLevel(desiredLevel)
        # create file handler which logs even debug messages
        fh = logging.FileHandler(fileName)
        fh.setLevel(desiredLevel)
        fh.setFormatter(formatter)
        # add the handler to logger
        logger.addHandler(fh)

    def openScreenAndRotatingFileLog(fileName, formatter, desiredLevel, maxBytes):
        logger = logging.getLogger('')
        logger.setLevel(desiredLevel)
        # create file handler which logs even debug messages
        fh = logging.handlers.RotatingFileHandler(fileName, maxBytes)
        fh.setLevel(desiredLevel)
        fh.setFormatter(formatter)
        # add the handler to logger
        logger.addHandler(fh)

    format = "%(asctime)-15s - %(levelname)-6s - %(funcName)10.10s - %(message)s"
    formatter = logging.Formatter(format)
    # Clean up root logger
    for handler in logging.getLogger('').handlers:
        logging.getLogger('').removeHandler(handler)
    openScreenLog(format, desiredLevel)
    
    if mode == "File" or mode == "RollingFile":
        if not os.path.isdir(logDirectory):
            shellutils.mkdir(logDirectory)
  
        if mode == "File":
            openScreenAndFileLog(logPath, formatter, desiredLevel)
    
        elif mode == "RollingFile":
            openScreenAndRotatingFileLog(logPath, formatter, desiredLevel, LOG_MAX_BYTES)

def closeLog():
    '''This function is for shutdown the logging job
    '''
    logging.shutdown()

def checkInput():
    '''This function is for treat the user command line parameters.
    '''
    # Create instance of OptionParser Module, included in Standard Library
    p = optparse.OptionParser(description=__description__,
                              prog=__program__,
                              version=__version__,
                              usage='''%prog [options] <files>''') 
    # Define the options. Do not use -h nor -v, the are reserved to help and version automaticly
    p.add_option('--rename', '-r', action="store", type="string", dest="rename", help='If setted will rename to regexp. The wildcards matches the program options. Ex. "%a - %t" will rename to "artist - title"')
    p.add_option('--dont-erase', '-d', action="store_true", dest="donterase", help='If setted eyed3 will not call \"--remove-all\"')
    
    p.add_option('--title', '-t', action="store", type="string", dest="title", help='The title. Overwritten if the analysis returns something useful')
    p.add_option('--artist', '-a', action="store", type="string", dest="artist", help='The artist. Overwritten if the analysis returns something useful')
    p.add_option('--album','-A', action="store", type="string", dest="album", help='The album')
    p.add_option('--track-num','-n', action="store", type="int", dest="tracknum", help='The track number')
    p.add_option('--year','-Y', action="store", type="int", dest="year", help='The year')

    # Parse the commandline
    options, arguments = p.parse_args()

    # Decide what to do
    return [{'title':options.title, 
             'artist':options.artist, 
             'album':options.album, 
             'tracknum':options.tracknum, 
             'year':options.year,
            }, 
            {'rename': options.rename,
             'donterase': options.donterase,
            },
            arguments]
    

# Helper functions
def areToolsInstalled():
    '''
    '''
    result = True
    softwareNeeded = [{'sw':"echoprint-codegen", 
                       'message':"""Tool needed not found. Install it by typing: 
 sudo apt-get install ffmpeg libboost-all-dev libtag1-dev zlib1g-dev git eyed3
 git clone -b release-4.12 git://github.com/echonest/echoprint-codegen.git
 cd echoprint-codegen/
 cd src/
 make
 cd ..
 cd ..
 mv echoprint-codegen /usr/local/.
 ln -s /usr/local/echoprint-codegen/echoprint-codegen /usr/bin/echoprint-codegen"""},
                      {'sw':"eyeD3", 'message':"""Tool needed not found. Install it by typing: 
 sudo apt-get install eyed3"""},
]
    for software in softwareNeeded:
        if not shellutils.executableExists(software['sw']):
            print software['message']
            result = False
            
    return result

def echoprint(audiofile):
    '''
    '''
    artist = None
    title = None
    
    logging.info("Looking up: " + audiofile)
    
    # Run echoprint
    command = ["echoprint-codegen",
                audiofile,
                "10",
                "30"];
    status, stdout, stderr = shellutils.run(command);
    stdoutDecoded = json.loads(stdout)
    if len(stdoutDecoded) > 0 and 'code' in stdoutDecoded[0]:
        code = stdoutDecoded[0]['code']
        
        # Query server
        url = "http://developer.echonest.com/api/v4/song/identify?api_key=%s&code=%s&version=%s" % (urllib.quote(APIKEY), urllib.quote(code), urllib.quote("4.12"))
        #logging.debug("URL:    " + url)
        webout = urllib.urlopen(url).read()
        #logging.debug("Result: " + webout)
        
        weboutDecoded = json.loads(webout)    
        status = weboutDecoded['response']['status']['code']
        if status == 0 and len(weboutDecoded['response']['songs']) > 0:
            artist = weboutDecoded['response']['songs'][0]['artist_name']
            title =  weboutDecoded['response']['songs'][0]['title']
    else:
        logging.error("  Error analyzing: " + stdout)   
        
    return [artist, title]
    
def writeTags(artist, title, album, tracknum, year, options, audiofile):
    '''
    '''
    
    def escapeCharacters(input):
        #return input.replace("'", "") # Not needed!
        return input
    
    # Clear tags and write new ones
    command = ["eyeD3"]
    if options['donterase'] == None:
        command.append("--remove-all")
    if artist != None:
        command.append("-a")
        command.append(escapeCharacters(artist))
    if album != None:
        command.append("-A")
        command.append(escapeCharacters(album))
    if title != None:
        command.append("-t")
        command.append(escapeCharacters(title))
    if tracknum != None:
        command.append("-n")
        command.append(str(tracknum))
    if year != None:
        command.append("-Y")
        command.append(str(year))
    command.append(audiofile)
                
    logging.debug("  %s" % " ".join(map(str, command)));
    status, stdout, stderr = shellutils.run(command);
    if status == 0:
        logging.info("File modified: " + audiofile)
        logging.info("  Artist: " + str(artist))
        logging.info("  Title:  " + str(title))
        logging.info("  Album:  " + str(album))
        logging.info("  Track#: " + str(tracknum))
        logging.info("  Year:   " + str(year))
    
def rename(artist, title, album, tracknum, year, options, audiofile):
    '''
    '''
    def escapeCharacters(input):
        return input.replace("'", "") # Not needed!
    
    newname = options['rename']
    newname = newname.replace("%a", escapeCharacters(artist))
    newname = newname.replace("%A", escapeCharacters(album))
    newname = newname.replace("%t", escapeCharacters(title))
    newname = newname.replace("%n", str(tracknum))
    newname = newname.replace("%Y", str(year))
    newname = os.path.join(shellutils.dirname(audiofile), newname + shellutils.extension(audiofile))
    shellutils.mv(audiofile, newname)
    logging.info("File renamed to: " + newname)

    
# Main function
def core(properties, options, files):
    '''This is the core, all program logic is performed here
    '''
    for audiofile in files:
        [fetchedArtist, fetchedTitle] = echoprint(audiofile)
        
        writeTags(fetchedArtist or properties['artist'], 
                  fetchedTitle or properties['title'], 
                  properties['album'], 
                  properties['tracknum'], 
                  properties['year'],
                  options,
                  audiofile)
         
        if options['rename'] != None:
            rename(fetchedArtist or properties['artist'], 
                   fetchedTitle or properties['title'], 
                   properties['album'], 
                   properties['tracknum'], 
                   properties['year'],
                   options, 
                   audiofile)

def main():
    '''This is the main procedure, is detached to provide compatibility with the updater
    '''
    openLog(LOG_MODE, LOG_LEVEL)
    [properties, options, files] = checkInput()
    logging.debug(str([properties, options, files]))
    core(properties, options, files)
    closeLog()

    
# Entry point
if __name__ == '__main__':
    try:
        if areToolsInstalled():
            main()
    
    except KeyboardInterrupt:
        print "Shutdown requested. Exiting"
    except SystemExit:
        pass
    except:
        logging.error("Unexpected error:" + traceback.format_exc())
        raise
