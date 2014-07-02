#!/usr/bin/env python
###############################################################################################
#  Author: 
__author__ = '<a href="mailto:debuti@gmail.com">Borja Garcia</a>'
# Program: 
__program__ = 'autotag'
# Package:
__package__ = ''
# Descrip: 
__description__ = '''CLI application for tagging and guessing tags on music files. Also implements 
a pattern renamer.'''
# Version: 
__version__ = '1.0.0'
#    Date:
__date__ = '20140702'
# License: This script doesn't require any license since it's not intended to be redistributed.
#          In such case, unless stated otherwise, the purpose of the author is to follow GPLv3.
# History: 
#          1.0.0 (20140702)
#            -First stable version
#            -Added auto numbering
#            -Fixed some bugs
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
    # Custom parser to show epilog info
    class MyParser(optparse.OptionParser):
        def format_epilog(self, formatter):
            return self.epilog

    examples = """
 Examples:
  - Make a custom album
     autotag -N -s -r %n\ -\ %a\ -\ %t -A My\ album -Y 2014 -T Various\ Artists <dir>\*mp3
  - Make BorjueloMix
     autotag -N -s -r %n\ -\ %a\ -\ %t -A BorjueloMix2011 -Y 2011 -T Various\ Artists /media/dropbox/Queues/nettop/Music/youtubeSingles/2011/*mp3
"""

    # Create instance of OptionParser Module, included in Standard Library
    p = MyParser(description=__description__,
                 prog=__program__,
                 version=__version__,
                 usage='''%prog [options] <files>''', 
                 epilog=examples) 

    # Define the options. Do not use -h nor -v, the are reserved to help and version automaticly
    p.add_option('--rename', '-r', action="store", type="string", dest="rename", help='If setted will rename to regexp. The wildcards matches the program options. Ex. "%a - %t" will rename to "artist - title"')
    p.add_option('--auto-track-num','-N', action="store_true", dest="autotracknum", help='Auto track number: Use a consecutive number for each file (Caution, this superseed -n)')
    p.add_option('--dont-erase', '-d', action="store_true", dest="donterase", help='If setted eyed3 will not call \"--remove-all\"')
    p.add_option('--ask', '-s', action="store_true", dest="ask", help='Ask for confirmation before doing anything')
    
    p.add_option('--artist', '-a', action="store", type="string", dest="artist", help='The artist. Overwritten if the analysis returns something useful')
    p.add_option('--title', '-t', action="store", type="string", dest="title", help='The title. Overwritten if the analysis returns something useful')
    p.add_option('--album','-A', action="store", type="string", dest="album", help='The album')
    p.add_option('--track-num','-n', action="store", type="int", dest="tracknum", help='The track number')
    p.add_option('--year','-Y', action="store", type="int", dest="year", help='The year')
    p.add_option('--albumartist','-T', action="store", type="string", dest="albumartist", help='The album artist')
    
    # Parse the commandline
    options, arguments = p.parse_args()

    # Decide what to do
    if len(arguments) == 0:
        p.print_help()
        sys.exit(-1)
    else:
        # Return as [properties, options, files]
        return [{'artist':options.artist, 
                 'title':options.title, 
                 'album':options.album, 
                 'tracknum':options.tracknum, 
                 'year':options.year,
                 'albumartist':options.albumartist,
                }, 
                {'rename':options.rename,
                 'donterase':options.donterase,
                 'ask':options.ask,
                 'autotracknum':options.autotracknum,
                },
                arguments]
    

# Helper functions
def areToolsInstalled():
    '''
    '''
    result = True
    softwareNeeded = [{'sw':"echoprint-codegen", 
                       'message':"""Tool needed not found. Install it by typing: 
 sudo apt-get install ffmpeg libboost-all-dev libtag1-dev zlib1g-dev git
 git clone -b release-4.12 http://github.com/echonest/echoprint-codegen.git
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
            logging.info("Nothing found for: " + audiofile)
    else:
        logging.error("  Error analyzing: " + stdout)   
        
    return [artist, title]

def writeTags(properties, options, audiofile):
    ''' Write tags with eyed3
    '''
    def escapeCharacters(input):
        return str(input)
    
    # Clear tags and write new ones
    command = ["eyeD3"]
    if options['donterase'] == None:
        command.append("--remove-all")
    if properties['artist'] != None:
        command.append("-a")
        command.append(escapeCharacters(properties['artist']))
    if properties['title'] != None:
        command.append("-t")
        command.append(escapeCharacters(properties['title']))
    if properties['album'] != None:
        command.append("-A")
        command.append(escapeCharacters(properties['album']))
    if properties['tracknum'] != None:
        command.append("-n")
        command.append(str(properties['tracknum']))
    if properties['year'] != None:
        command.append("-Y")
        command.append(str(properties['year']))
    if properties['albumartist'] != None:
        command.append("--set-user-text-frame=ALBUMARTISTSORT:" + escapeCharacters(properties['albumartist']))
    command.append(audiofile)
                
    logging.debug("  %s" % " ".join(map(str, command)));
    status, stdout, stderr = shellutils.run(command);
    if status == 0:
        for key in properties.keys():
            if properties[key] != None:
                logging.info("  "+key+": \t" + str(properties[key]))
        logging.info("File modified: " + audiofile)

def rename(properties, options, audiofile):
    '''
    '''
    def escapeCharacters(input):
        return input.replace("'", "")
    
    # Import the regular expression
    newname = options['rename']

    # TODO: Check if something would remain unchanged in the filename
    # Substitute every item
    newname = newname.replace("%a", escapeCharacters(properties['artist']))
    newname = newname.replace("%t", escapeCharacters(properties['title']))
    newname = newname.replace("%A", escapeCharacters(properties['album']))
    newname = newname.replace("%n", str(properties['tracknum']))
    newname = newname.replace("%Y", str(properties['year']))
    newname = newname.replace("%T", str(properties['albumartist']))
    newname = os.path.join(shellutils.dirname(audiofile), newname + shellutils.extension(audiofile))
    shellutils.mv(audiofile, newname)
    logging.info("File renamed to: " + newname)

    
# Main function
def core(properties, options, files):
    '''This is the core, all program logic is performed here
    '''
    for index, audiofile in enumerate(files):
        # Do dict initialization
        values = {}

        [fetchedArtist, fetchedTitle] = echoprint(audiofile)
                
        values['artist'] = fetchedArtist or properties['artist']
        values['title'] = fetchedTitle or properties['title']
        values['album'] = properties['album']
        if options['autotracknum']:
            values['tracknum'] = "%03d" % (index + 1)
        else:
            values['tracknum'] = properties['tracknum']
        values['albumartist'] = properties['albumartist']
        values['year'] = properties['year']
        
        if values['album'] == None and \
           values['title'] == None and \
           values['artist'] == None and \
           values['tracknum'] == None and \
           values['albumartist'] == None and \
           values['year'] == None:
           
            logging.info("File not modified: " + audiofile)
            
        else:
            if options['ask'] != None:
                print "I'm going to set this tags to this file " + audiofile
                for key in values.keys():
                    if values[key] != None:
                        print "  "+key+": \t" + str(values[key])
                if options['rename'] != None:
                    print "And I'm going to rename it too."
                print "Do you want it? (Y/n)"
                ok = raw_input().lower()
                if ok is not None and ok == 'n':
                    print "Ok, i won't do that.."
                    continue
                
            writeTags(values,
                      options,
                      audiofile)
         
            if options['rename'] != None:
                rename(values,
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
