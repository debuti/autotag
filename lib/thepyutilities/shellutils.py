#!/usr/bin/env python
###############################################################################################
#  Author:
__author__ = '<a href="mailto:debuti@gmail.com">Borja Garcia</a>'
# Program:
__program__ = 'shellutils'
# Package:
#__package__ = 'tk.ganian.thepyutilities'
# Descrip:
__description__ = '''Library for common utilities.'''
# Version:
__version__ = '0.0.2'
#    Date: 
__date__ = '2010-10-29'
# License: This script doesn't require any license since it's not intended to be redistributed.
#          In such case, unless stated otherwise, the purpose of the author is to follow GPLv3.
# History:
#           0.0.2 (2010-10-29)
#            -Added several methods
#            -Added and improved searchNreplace
#           0.0.1 (2009-03-09)
#            -Initial release
###############################################################################################

import subprocess, time
import os
import socket
import logging
import sys
import re
import shutil
import stringutils
import hashlib
import pexpect


def exists(path):    
    '''This function returns if a object exists in current working directory
    '''

    return os.path.exists(path)


def fileExists(path):    
    '''This function returns if a file exists in current working directory
    '''

    return os.path.exists(path) and os.path.isfile(path)


def dirExists(path):    
    '''This function returns if a dir exists in current working directory
    '''
    return os.path.exists(path) and os.path.isdir(path)


def rm(pathList, recurse=False):
    '''This function deletes a list of files
    '''

    try:
        if type(pathList).__name__ != 'list':
            pathList = [pathList]
        
        for entity in pathList:
            if recurse:
                if os.path.isdir(entity):
                    shutil.rmtree(entity)            

                else:
                    os.remove(entity)            
            
            else:
                if fileExists(entity):
                    os.remove(entity)
                    
                else:
                    logging.error('rm: ' + "Is a directory")
                    return - 1

        return 0
    
    except:
        logging.error('rm: ' + "Unexpected error:" + str(sys.exc_info()[0]))
        raise


def touch(fileName):
    '''Touches the file
    '''
    f = open(fileName, "w")
    f.close()


def write(fileName, text):
    '''Writes the text to the file
    '''
    f = open(fileName, "w")
    f.write(text)
    f.close()


def append(fileName, text):
    '''Appends the text to the file
    '''
    f = open(fileName, "a")
    f.write(text)
    f.close()


def cat(fileName):
    '''Reads everything in the file
    '''
    f = open(fileName, "r")
    result = f.read() # read everything in the file
    f.close()
    return result


def executableExists(execName):
    '''This function returns true if there is an executable like the parameter in the
       path (like unix which)
    '''

    assert not os.path.dirname(execName)

    extensions = os.environ.get("PATHEXT", "").split(os.pathsep)
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        base = os.path.join(directory, execName)
        options = [base] + [(base + ext) for ext in extensions]
        for filename in options:
            if os.path.exists(filename):
                return True
    return False


def which(program):
    '''This function returns the real path (like unix which)
    '''
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def mkdir(path):
    '''Makes a new directory or returns an error if its currently there
    '''
    try:
        os.makedirs(path)
        
    except:
        logging.error('mkdir: ' + "Unexpected error:" + str(sys.exc_info()[0]))
        raise


def findNReplaceRegExp(file_name, regexp, replaceString, verbose=False, confirmationNeeded=False, surroundingLines=1):
    '''Replaces the oldString with the replaceString in the file given,\
       returns the number of replaces
    '''

    class SearchIterator:
        '''A Simple class to iterate over a text and return ocurrencies
        '''
        _text = ''
        _lastPosition = 0
        _cregexp = None

        def __init__ (self, text, regexp):
            self._text = text     
            self._lastPosition = 0  
            self._cregexp = re.compile(regexp, re.MULTILINE | re.DOTALL)
    
        def reset (self, text, regexp):
            self._text = text
            self._lastPosition = 0
            self._cregexp = re.compile(regexp, re.MULTILINE | re.DOTALL)
    
        def reset (self):
            self.reset('', '')
    
        def findNext (self):
            '''Returns the position and length of the next ocurrence
            '''
            if self.thereAreItemsLeft():
                coincidence = self._cregexp.search(self._text)
                # return from coincidence and length
                result = [self._lastPosition + coincidence.start(), coincidence.end() - coincidence.start()]
                # update last position to provide right information about position
                self._lastPosition = self._lastPosition + coincidence.end()
                self._text = self._text[coincidence.end():]
            else:
                result = None
 
            return result
 
        def shift (self, number):
            '''Shifts by a number of positions the actual indexf
            '''
            self._lastPosition = self._lastPosition + number
       
        def thereAreItemsLeft (self):
            '''Returns if there are items left to occur
            '''
            if self._cregexp.search(self._text):
                return True
            else:
                return False

    # open file for read
    file_in = open(file_name, 'r')
    myFile = file_in.read()
    file_in.close()

    # initialize local variables
    mySearchIterator = SearchIterator (myFile, regexp)
    ocurrences = 0
    isAborted = False

    while mySearchIterator.thereAreItemsLeft():
        [position, length] = mySearchIterator.findNext()
        # new string
        myNewFile = myFile [:position] + replaceString + myFile [position + length:]

        if verbose == True:
            print "found at position " + str(position)
            # calculate the segment of text in which the resolution will be done
            from_index = stringutils.extendedRFind(myFile, "\n", 0, position, surroundingLines + 1)
            to_index_old = stringutils.extendedFind(myFile, "\n", position + length, len(myFile), surroundingLines + 1)
            to_index_new = stringutils.extendedFind(myNewFile, "\n", position + len(replaceString), len(myNewFile), surroundingLines + 1)
            # do some adjusting if we fall out off the limits
            if myFile[from_index] != "\n":
                from_index = 0
            if to_index_old == len(myFile) or myFile[to_index_old] != "\n":
                to_index_old = len(myFile) - 1
            
            # print the old string and the new string
            print '- ' 
            print myFile[from_index:to_index_old]
            print '+ ' 
            print myNewFile[from_index:to_index_new]
           
            if confirmationNeeded:
                # ask user if this should be done
                question = raw_input('Accept changes? [Yes (Y), No (n), Abort (a)] ')
                # print new line
                print
                question = str.lower(question)
                if question == 'a':
                    isAborted = True
                    print "Changes to file " + file_name + " aborted"
                    break
                elif question == 'n':
                    pass
                else:
                    myFile = myNewFile
                    mySearchIterator.shift (len(replaceString) - length)
                    ocurrences = ocurrences + 1
            else:
                myFile = myNewFile
                mySearchIterator.shift (len(replaceString) - length)
                ocurrences = ocurrences + 1                
        else:
            myFile = myNewFile
            mySearchIterator.shift (len(replaceString) - length)
            ocurrences = ocurrences + 1        

    # if some text was replaced, overwrite the original file
    if ocurrences > 0 and not isAborted:
        # open the file for overwritting
        file_out = open(file_name, 'w')
        file_out.write(myFile)
        file_out.close()
        if verbose: print "File " + file_name + " written"

    return ocurrences


def findNReplace(file_name, oldString, replaceString, verbose=False, confirmationNeeded=False):
    '''Replaces the oldString with the replaceString in the file given,\
       returns the number of lines changed
    '''

    return findNReplaceRegExp(file_name, oldString, replaceString, verbose, confirmationNeeded)


def findNReplaceInFiles(file_name_list, oldString, replaceString, verbose=False, confirmationNeeded=False):
    '''Search and replace in all the files given, returns an array \
       with the number of times replaced in each file
    '''
    output = []
    if verbose == True: print '\nReplaced (verbose):\n'
    # loop on all files
    for file_name in file_name_list:
        print 'Processing: ' + file_name
        output.append(findNReplace(file_name, oldString, replaceString, verbose, confirmationNeeded))
    return output


def findNReplaceRegExpInFiles(file_name_list, regexp, replaceString, verbose=False, confirmationNeeded=False):
    '''Search and replace in all the files given, returns an array \
       with the number of times replaced in each file
    '''
    output = []
    if verbose == True: print '\nReplaced (verbose):\n'
    # loop on all files
    for file in file_name_list:
        print 'Processing: ' + file
        output.append(findNReplaceRegExp(file, regexp, replaceString, verbose, confirmationNeeded))
    return output


def findNReplaceOrAppend(file, regexp, new_text):
    '''Replaces the regexp regexp with the new_text if found, \
       if not simply appends it to the end of the file given
       '''
    if findNReplaceRegExp(file, regexp, new_text) == 0:
        f = open(file, 'a')
        print >> f, new_text


def addLinuxPermanentEnvVar(key, value, index="Global"):
    '''Adds a permanent enviroment value in the bash shell for all users (needs privileges)
    '''
    if index == "Global":
        file = '/etc/environment'
    elif index == "Local":
        file = os.environ['HOME'] + '/.profile'
    else:
        return None 

    findNReplaceOrAppend(file, '^' +str(key) + '=[^\n]+', str(key) + '=' + str(value))


def run(command, timeout=0): 
    ''' Run commands. The command is a array of strings WITHOUT SPACES
        NOTE: This proc is not adecuate to run commands like ffmpeg
        ie. status, stdout, stderr = shellutils.run(["ffmpeg", "-ss", start, "-t", end, "-i", input, "-s", res, "-b", "4000k", output]);
        ie. status, stdout, stderr = shellutils.run(command.split());
    '''
    proc = subprocess.Popen(command, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if timeout != 0 :
        poll_seconds = .250
        deadline = time.time() + timeout
        while time.time() < deadline and proc.poll() == None:
            time.sleep(poll_seconds)

        if proc.poll() == None:
            if float(sys.version[:3]) >= 2.6:
                proc.terminate()

    stdout, stderr = proc.communicate()       
    return proc.returncode, stdout, stderr 


def runCLI(cmd):
    '''This function takes cli commands and returns the output
    '''

    status, stdout, stderr = run(cmd, timeout=30)

    return status, stdout, stderr

    
def runExpect(cmd, token = pexpect.EOF, live=False):
    '''This function takes hard handling cli commands and returns the output
       WARNING: Only Linux
       To pipe commands use: child = pexpect.spawn('/bin/bash -c "ls -l | grep LOG > log_list.txt"')
    '''
        
    if type(cmd).__name__ == 'list' or type(cmd).__name__ == 'tuple':
        cmd = " ".join(map(str, cmd))
    child = pexpect.spawn (cmd,  timeout=None)
    if live: 
        child.logfile = sys.stdout
    child.expect(token)
    child.close()
    return child.exitstatus, child.logfile, None


# Deprecated
def runBash(cmd):
    '''This function takes Bash commands and returns the output
    '''
    status, stdout, stderr = runCLI(cmd)
    return stdout


def getSystemName():
    '''This function returns the name of the system (like uname -n)
    '''
    if socket.gethostname() is None:
        if os.getenv('HOSTNAME') is None:
            if os.getenv('COMPUTERNAME') is None:
                logging.error('getSystemName: ' + 'Computer name not fetched')
                return None

            else:
                return os.getenv('COMPUTERNAME')

        else:
            return os.getenv('HOSTNAME')
    else:
        return socket.gethostname()


def cp(source, destination): 
    '''This function takes a file or directory and copy it to a destination
    '''
    try:
        # Check the source
        if type(source).__name__ == 'list':
            return - 1

        if os.path.isfile(source):
            shutil.copy(source, destination)

        elif os.path.isdir(source):
            shutil.copytree(source, destination)

        else:
            logging.error('cp: ' + "source is not file nor directory: " + source) 
            return - 1
        
        logging.debug("cp: " + source + " -> " + destination)
        return 0

    except:
        logging.error('cp: ' + "Unexpected error:" + str(sys.exc_info()[0]) + " for input (" + source + ", " + destination + ")")
        raise


def hash(file):
    '''Returns the hash digest of a file
    '''
    if os.path.isfile(file):
        md5 = hashlib.md5()
        f = open(file)
    
        while True:
            data = f.read(128)
            if not data:
                break
            md5.update(data)
        
        return md5.digest()

    else:
        return 0


def mv(sourceList, destination): 
    '''This function takes a list of files and directories and moves them to a destination
    '''
    def oneToOne (source, destination):
        initialHash = hash(source)
        tempDestination = destination + '.tmp'
        cp(source, tempDestination)
        finalHash = hash(tempDestination)
                    
        # Check that the copy is ok
        if initialHash != finalHash:
            logging.error('mv: ' + "Hash error for the file " + source + ". InitHash:" + initialHash + "  FinalHash:" + finalHash)
            # Remove the temporary file
            rm(tempDestination, recurse=True)
            return - 1

        else:
            # Rename the destination file
            shutil.move(tempDestination, destination)
            # Remove the source file
            rm(source, recurse=True)

    try:
        # Adapt the source
        if type(sourceList).__name__ != 'list':
            sourceList = [sourceList]
            
        logging.debug("mv: " + str(sourceList) + " -> " + destination)
        
        if not exists(destination):
            if len(sourceList) > 1: # From several to unknown name
                logging.error('mv: ' + "cannot move several items to an unknown destination") 
                return - 1

            elif os.path.isfile(sourceList[0]) or os.path.isdir(sourceList[0]): # From one (whatever) to unknown name
                return oneToOne(sourceList[0], destination)

            else:
                logging.error('mv: ' + "source is not file nor directory: " + sourceList[0]) 
                return - 1

        elif os.path.isfile(destination):
            if len(sourceList) > 1: # From several items to file
                logging.error('mv: ' + "cannot move several items to file") 
                return - 1

            elif os.path.isfile(sourceList[0]): # From one file to file (overwrite)
                return oneToOne(sourceList[0], destination)
            
            elif os.path.isdir(sourceList[0]):  # From dir to file
                logging.error('mv: ' + "cannot move a dir to a file: " + sourceList[0]) 
                return - 1

            else:
                logging.error('mv: ' + "source is not file nor directory: " + sourceList[0]) 
                return - 1
 
        elif os.path.isdir(destination):
            # For every source in the path
            for source in sourceList:
    
                sourceName = basename(source)

                if os.path.isfile(source):
                    initialHash = hash(source)
                    # Replace this by cp to .tmp and then verify and then remove
                    theDestination = os.path.join(destination, sourceName)
                    tempDestination = theDestination + '.tmp'
                    cp(source, tempDestination)
                    finalHash = hash(tempDestination)
                
                    # Check that the copy is ok
                    if initialHash != finalHash:
                        logging.error('mv: ' + "Hash error for the file " + source + ". InitHash:" + initialHash + "  FinalHash:" + finalHash)
                        # Remove the temporary file
                        rm(tempDestination, recurse=True)
                        return - 1

                    else:
                        # Rename the destination file
                        shutil.move(tempDestination, theDestination)
                        # Remove the source file
                        rm(source, recurse=True)
                
                elif os.path.isdir(source):
                    theDestination = os.path.join(destination, sourceName) 
                    mkdir(theDestination)
                    for entity in ls(source):
                        if mv(os.path.join(source, entity), theDestination) != 0:
                            return - 1
                    #If successfull remove the dir from source
                    rm(source, recurse=True)

                else:
                    logging.error('mv: ' + "object is not file nor directory: " + source) 
                    return - 1
            
            return 0

        else:
            logging.error('mv: ' + "path not file nor directory: " + destination)
            return - 1

    except:
        logging.error('mv: ' + "Unexpected error:" + str(sys.exc_info()[0]) + " for input (" + str(sourceList) + ", " + destination + ")")
        raise
    
def pwd(): 
    '''This function returns the current working directory
    '''
    return os.getcwd()
    
def walk (path=pwd()):
    '''This function returns a list of files and directories under the path passed as parameter (without full path)
       NOTE: It wont include . and .. but it shows all hidden files
    '''
    files = []
    dirs = []
    for artifact in os.listdir(path):
        if os.path.isfile(os.path.join(path, artifact)):
            files.append(artifact)
        elif os.path.isdir(os.path.join(path, artifact)):
            dirs.append(artifact)
        else:
            logging.error('walk: ' + "object is not file nor directory: " + os.path.join(path, artifact)) 

    # Do some sorting
    if files != [] : 
        files.sort()
    if dirs != [] : 
        dirs.sort()
    
    return path, dirs, files
    
def fullPath(path): 
    '''This function returns 
    '''
    if type(path) != type('str'):
        return None
    else:
        if os.path.isabs(path):
            return path
        else:
            return os.path.realpath(os.path.join(pwd(), path))
    
def ls(path=pwd(), fullPath=False, recurse=False, type="all"): 
    '''This function returns a list of files and directories under the path passed as parameter (without full path)
       NOTE: It wont include . and .. but it shows all hidden files
    '''
    
    def setFullPath (path, files):
        '''Aux function to fullpath a set of files
        '''
        result = []
        for artifact in files:
            artifact = os.path.join(path, artifact)
            result.append(os.path.abspath(artifact))
        return result

    path = os.path.abspath(path)

    if exists(path) and os.path.isdir(path) and type in ["all", "files", "dirs"]:
        logging.debug('ls: ' + "Listing directory " + path)
       
        path, dirs, files = walk (path)
  
        if type == "files":
            result = files
        elif type == "dirs":
            result = dirs
        else:
            result = dirs + files
            
        if fullPath:
            result = setFullPath(path, result)
                   
        if recurse:            
            for dir in dirs:
                result += ls(path=os.path.join(path, dir), fullPath=fullPath, recurse=True, type=type)
 
        return result

    else: 
        return None
    
def isDirEmpty(path, emptyOfFilesOnly=False):
    '''This function returns true if a directory is empty, accepts an argument that querys
       if its empty or empty of files (only directories inside)
    '''
    if (emptyOfFilesOnly == True):
        path, dirs, files = walk (path)
        return ((files == []) and (dirs != []))
    
    else:
        return (os.listdir(path) == [])


def getSystemVariable(name, defaultValue=None):
    '''This function returns the system variable or defaultValue if not found
    '''
    envVar = os.getenv(name)
    
    if envVar is None:
        logging.error('getSystemVariable: ' + 'Envvar not fetched')
        envVar = defaultValue

    return envVar


def filename(name):
    '''This function returns the basename without the extension
    '''
    fileName, fileExtension = os.path.splitext(basename(name))
    return fileName


def extension(name):
    '''This function returns just the extension
    '''
    fileName, fileExtension = os.path.splitext(basename(name))
    return fileExtension


def basename(name):
    '''This function returns the basename for a path
    '''
    if os.path.basename(name) is None:
        logging.error('basename: ' + 'Basename failed')

    return os.path.basename(name)


def dirname(name):
    '''This function returns the dirname for a path
    '''
    if os.path.dirname(name) is None:
        logging.error('dirname: ' + 'dirname failed')

    return os.path.dirname(name)


def isDriveConnected(name):
    '''This function returns if a certain drive is connected to the system
    '''
    path = getSystemVariable(name) 
    if path is None:
        return False
    
    else:
        return (ls() != None and ls() != [])


def du(path):
    '''This function returns the number of bytes used by this dir/file
    '''
    folder_size = 0
    if os.path.isdir(path):
        for file in ls(path, fullPath=True):
            folder_size += du(file)
    else:
        try:
            folder_size += os.path.getsize(path)
        except:
            logging.error('du: ' + "Unexpected error:" + str(sys.exc_info()[0]))
        
    return folder_size
 

def cd(path):
    '''This function changes the current wd
    '''
    path = os.path.abspath(path)
    
    if dirExists(path) is False:
        logging.error('cd: ' + 'cd failed because ' + path + ' does not exists')
        return False

    else:  
        os.chdir(path)
        if os.path.realpath(path) == pwd():
            logging.debug('cd: ' + 'Succesfully changed to ' + path)
            return True
        else:
            logging.error('cd: ' + 'cd failed because i can not change to ' + path)
            return False


def grep(match, object):
    '''This function returns the matched line of the file
    '''
    result = []
    
    if fileExists(object):
        object = open(object)
        
    for line in object.splitlines():
        if match in line:
            result.append(line)
        
    if result == []:
        return None
    
    else:
        return result

def egrep(match, object):
    '''This function returns the matched line of the file with re
    '''
    result = []
    
    if fileExists(object):
        object = open(object)
        
    for line in object.splitlines():
        if re.match(match, line) != None:
            result.append(line)
        
    if result == []:
        return None
    
    else:
        return result

def find(rootPath):
    '''This function returns the find output
    '''
    result = []
    
    path, dirs, files = walk (rootPath)
  
    for file in files:
        result.append(os.path.join(rootPath, file))
        
    for dir in dirs:
        result.append(os.path.join(rootPath, dir))
        result += find(os.path.join(rootPath, dir))
        
    if result == []:
        return None
    else:
        return result


def checkPidRunning(pid):        
    '''Check For the existence of a unix pid.
    '''
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


