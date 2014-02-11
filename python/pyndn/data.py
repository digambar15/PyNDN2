#
# Copyright (C) 2014 Regents of the University of California.
# Author: Jeff Thompson <jefft0@remap.ucla.edu>
# See COPYING for copyright and distribution information.
#

"""
This module defines the NDN Data class.
"""

from pyndn.encoding import WireFormat
from pyndn.util import Blob
from pyndn.util import SignedBlob
from pyndn.util import ChangeCounter
from pyndn.name import Name
from pyndn.meta_info import MetaInfo

class Data(object):
    def __init__(self, name = None):
        self._name = ChangeCounter(name if type(name) == Name else Name(name))
        self._metaInfo = ChangeCounter(MetaInfo())
        # TODO: Implement _signature
        self._content = Blob()
        self._defaultWireEncoding = SignedBlob()
        self._defaultWireEncodingFormat = None

        self._getDefaultWireEncodingChangeCount = 0
        self._changeCount = 0
    
    def wireEncode(self, wireFormat = WireFormat.getDefaultWireFormat()):
        """
        Encode this Data for a particular wire format. If wireFormat is the 
        default wire format, also set the defaultWireEncoding field to the 
        encoded result.
        
        :param wireFormat: (optional) A WireFormat object used to encode this 
           Interest. If omitted, use WireFormat.getDefaultWireFormat().
        :type wireFormat: A subclass of WireFormat.
        :return: The encoded buffer.
        :rtype: Blob
        """
        if (not self.getDefaultWireEncoding().isNull() and
            self.getDefaultWireEncodingFormat() == wireFormat):
            # We already have an encoding in the desired format.
            return self.getDefaultWireEncoding()
  
        (encoding, signedPortionBeginOffset, signedPortionEndOffset) = \
          wireFormat.encodeData(self)
        wireEncoding = SignedBlob(
          encoding, signedPortionBeginOffset, signedPortionEndOffset)
          
        if wireFormat == WireFormat.getDefaultWireFormat():
            # This is the default wire encoding.
            self._setDefaultWireEncoding(
              wireEncoding, WireFormat.getDefaultWireFormat())
        return wireEncoding
    
    def wireDecode(self, input, wireFormat = WireFormat.getDefaultWireFormat()):
        """
        Decode the input using a particular wire format and update this Data. 
        If wireFormat is the default wire format, also set the 
        defaultWireEncoding to another pointer to the input.
        
        :param input: The array with the bytes to decode. If input is not a 
          Blob, then copy the bytes to save the defaultWireEncoding (otherwise 
          take another pointer to the same Blob).
        :type input: An array type with int elements. 
        :param wireFormat: (optional) A WireFormat object used to decode this 
           Interest. If omitted, use WireFormat.getDefaultWireFormat().
        :type wireFormat: A subclass of WireFormat.
        """
        # If input is a blob, get its buf().
        decodeBuffer = input.buf() if isinstance(input, Blob) else input
        (signedPortionBeginOffset, signedPortionEndOffset) = \
          wireFormat.decodeData(self, decodeBuffer)
  
        if wireFormat == WireFormat.getDefaultWireFormat():
            # This is the default wire encoding.  In the Blob constructor, set
            #   copy true, but if input is already a Blob, it won't copy.
            self._setDefaultWireEncoding(SignedBlob(
                Blob(input, True), 
                signedPortionBeginOffset, signedPortionEndOffset),
            WireFormat.getDefaultWireFormat())
        else:
            self._setDefaultWireEncoding(SignedBlob(), None)

    def getName(self):
        return self._name.get()
    
    def getMetaInfo(self):
        return self._metaInfo.get()

    # TODO: Implement getSignature.

    def getContent(self):
        return self._content
    
    def getDefaultWireEncoding(self):
        """
        Return the default wire encoding, which was encoded with
        getDefaultWireEncodingFormat().
        
        :return: The default wire encoding, whose isNull() may be true if there
          is no default wire encoding.
        :rtype: SignedBlob
        """
        if self._getDefaultWireEncodingChangeCount != self.getChangeCount():
            # The values have changed, so the default wire encoding is 
            # invalidated.
            self._defaultWireEncoding = SignedBlob()
            self._defaultWireEncodingFormat = None
            self._getDefaultWireEncodingChangeCount = self.getChangeCount()
            
        return self._defaultWireEncoding
        
    def getDefaultWireEncodingFormat(self):
        """
        Get the WireFormat which is used by getDefaultWireEncoding().
        
        :return: The WireFormat, which is only meaningful if the 
          getDefaultWireEncoding() is not isNull().
        :rtype: WireFormat
        """
        return self._defaultWireEncodingFormat
        
    def setName(self, name):
        """
        Set name to a copy of the given Name.
        
        :param name: The Name which is copied.
        :type name: Name
        :return: This Data so that you can chain calls to update values.
        :rtype: Data
        """
        self._name.set(name if type(name) == Name else Name(name))
        self._changeCount += 1
        return self
        
    def setMetaInfo(self, metaInfo):
        """
        Set metaInfo to a copy of the given MetaInfo.
        
        :param metaInfo: The MetaInfo which is copied.
        :type meatInfo: MetaInfo
        :return: This Data so that you can chain calls to update values.
        :rtype: Data
        """
        self._metaInfo.set(MetaInfo() if metaInfo == None 
                                      else MetaInfo(metaInfo))
        self._changeCount += 1
        return self
        
    # TODO: Implement setSignature.
    
    def setContent(self, content):
        self._content = content if type(content) == Blob else Blob(content)
        self._changeCount += 1
    
    def getChangeCount(self):
        """
        Get the change count, which is incremented each time this object 
        (or a child object) is changed.
        
        :return: The change count.
        :rtype: int
        """
        # Make sure each of the checkChanged is called.
        changed = self._name.checkChanged()
        changed = self._metaInfo.checkChanged() or changed
        if changed:
            # A child object has changed, so update the change count.
            self._changeCount += 1

        return self._changeCount

    def _setDefaultWireEncoding(
          self, defaultWireEncoding, defaultWireEncodingFormat):
        self._defaultWireEncoding = defaultWireEncoding
        self._defaultWireEncodingFormat = defaultWireEncodingFormat
        # Set _getDefaultWireEncodingChangeCount so that the next call to 
        # getDefaultWireEncoding() won't clear _defaultWireEncoding.
        self._getDefaultWireEncodingChangeCount = self.getChangeCount()
        