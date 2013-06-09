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
LOG_LEVEL = logging.INFO
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

import eyed3


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
            arguments]
    

# Helper functions
def areToolsInstalled():
    '''
    '''
    return shellutils.executableExists("echoprint-codegen")

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
    
def writeTags(artist, title, album, tracknum, year, audiofile):
    '''
    '''
    def toUnicode(input):
        '''
        '''
        try:
            # translate an Unicode string into a sequence of bytes is called encoding
            def to_unicode_or_bust(obj, encoding='utf-8'):
                if isinstance(obj, basestring):
                    if not isinstance(obj, unicode):
                        obj = unicode(obj, encoding)
                return obj
         
            return to_unicode_or_bust(input)

        except UnicodeDecodeError as e:
            print ("toUnicode: UnicodeDecodeError: " + e.reason + " on string \"" + e.object + "\" positions: " + str(e.start) + "-" + str(e.end))
        
    audiofileLoaded = eyed3.load(audiofile)
    if audiofileLoaded.tag != None:
        audiofileLoaded.tag.artist = toUnicode(artist)
        audiofileLoaded.tag.album = toUnicode(album)
        audiofileLoaded.tag.title = toUnicode(title)
        audiofileLoaded.tag.track_num = tracknum
        audiofileLoaded.tag.year = year
        audiofileLoaded.tag.save()
        logging.info("File modified: " + audiofile)
        logging.info("  Artist: " + str(artist))
        logging.info("  Title:  " + str(title))
        logging.info("  Album:  " + str(album))
        logging.info("  Track#: " + str(tracknum))
        logging.info("  Year:   " + str(year))
    else:
        logging.error("File has no tag info: " + audiofile)

    
# Main function
def core(properties, files):
    '''This is the core, all program logic is performed here
    '''
    for audiofile in files:
        [fetchedArtist, fetchedTitle] = echoprint(audiofile)
        
        writeTags(fetchedArtist or properties['artist'], 
                  fetchedTitle or properties['title'], 
                  properties['album'], 
                  properties['tracknum'], 
                  properties['year'],
                  audiofile)

def main():
    '''This is the main procedure, is detached to provide compatibility with the updater
    '''
    openLog(LOG_MODE, LOG_LEVEL)
    [properties, files] = checkInput()
    core(properties, files)
    closeLog()

    
# Entry point
if __name__ == '__main__':
    try:
        if areToolsInstalled():
            main()
        else:
            print """Tools needed not found. Install it by typing: 
sudo apt-get install ffmpeg libboost-all-dev libtag1-dev zlib1g-dev git eyed3
git clone -b release-4.12 git://github.com/echonest/echoprint-codegen.git
cd echoprint-codegen/
cd src/
make
cd ..
cd ..
mv echoprint-codegen /usr/local/.
ln -s /usr/local/echoprint-codegen/echoprint-codegen /usr/bin/echoprint-codegen"""
    
    except KeyboardInterrupt:
        print "Shutdown requested. Exiting"
    except SystemExit:
        pass
    except:
        logging.error("Unexpected error:" + traceback.format_exc())
        raise
