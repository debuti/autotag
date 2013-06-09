#!/usr/bin/env python
###############################################################################################
#  Author:
_author = '<a href="mailto:debuti@gmail.com">Borja Garcia</a>'
# Program:
_name = 'stringutils'
# Descrip:
_description = '''Library for string related utilities.'''
# Version:
_version = '0.0.2'
#    Date: 
_date = '2010-10-29'
# License: This script doesn't require any license since it's not intended to be redistributed.
#          In such case, unless stated otherwise, the purpose of the author is to follow GPLv3.
# History:
#          0.0.2 (2010-10-29)
#            -Fixed some errors
#          0.0.1 (2009-11-27)
#            -Initial release
###############################################################################################

import subprocess
import os
import socket
import logging
import string
import sys
import re
import shutil

def extendedFind(stringToAnalize, substringToSearch, startPosition, endPosition, numberOfCoincidence = 1):
    '''Finds a substring in a string, like find, but adds support to search\
       for the second or consecutive coincidences. If not found return the last encountered
    '''
    coincidencesCounted = 0
    lastCoincidencePosition = startPosition

    while coincidencesCounted < numberOfCoincidence:
        index = stringToAnalize.find(substringToSearch, lastCoincidencePosition, endPosition)
        #print "Busco desde " + str(lastCoincidencePosition) + " hasta " + str(endPosition) + " y encuentro el salto de linea en la posicion " + str(index)
        if index <= startPosition or index >= endPosition: 
            break
        else:
            lastCoincidencePosition = index + 1
            coincidencesCounted = coincidencesCounted + 1

    if coincidencesCounted != numberOfCoincidence:
        return lastCoincidencePosition
    else:
        return index

def extendedRFind(stringToAnalize, substringToSearch, startPosition, endPosition, numberOfCoincidence = 1):
    '''Finds a substring in a string, like find, but adds support to search\
       for the second or consecutive coincidences. If not found return the last encountered
    '''
    coincidencesCounted = 0
    lastCoincidencePosition = endPosition
    
    while coincidencesCounted < numberOfCoincidence:
        index = stringToAnalize.rfind(substringToSearch, startPosition, lastCoincidencePosition)
        #print "Busco desde " + str(startPosition) + " hasta " + str(lastCoincidencePosition) + " y encuentro el salto de linea en la posicion " + str(index)
        if index <= startPosition or index >= endPosition: 
            break
        else:
            lastCoincidencePosition = index - 1
            coincidencesCounted = coincidencesCounted + 1
     
    if coincidencesCounted != numberOfCoincidence:
        return lastCoincidencePosition
    else:
        return index


def list2str(list):
    '''This function turn a list into a str
    '''
    if type(list).__name__ != 'list':
        return None
    else:
        result = ""
        for element in list:
            result += element
            result += "\n"
        return result