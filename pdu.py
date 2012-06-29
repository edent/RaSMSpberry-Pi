# This Python file uses the following encoding: utf-8
"""
© 2012 Terence Eden

Adapted from http://rednaxela.net/pdu.php Version 1.5 r9aja
Original JavaScript (c) BPS & co, 2003. Written by Swen-Peter Ekkebus, edited by Ing. Milan Chudik, fixes and functionality by Andrew Alexander.
Original licence http://rednaxela.net/pdu.php "Feel free to use this code as you wish."

Python version © 2012 Terence Eden - released as MIT License
***
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
***

Note - this is my first Python program - I am quite happy to be corrected on True Pythonic Style etc. :-)
"""

"""
This program allows the user to craft a PDU when sending an SMS.
The user enters the destination number, the message, the class, and the SMSC.
The program generates the commands needed to instruct a modem to deliver the SMS.
"""

# This is pyserial which is needed to communicate with the 3G USB Dongle http://pyserial.sourceforge.net/
import serial


# Array with the default 7 bit alphabet
# @ = 0 = 0b00000000, a = 97 = 0b1100001, etc
# Alignment is purely an attempt at readability
SEVEN_BIT_ALPHABET_ARRAY = (
    '@', '£', '$', '¥', 'è', 'é', 'ù', 'ì', 'ò', 'Ç', '\n', 'Ø', 'ø', '\r','Å', 'å',
    '\u0394', '_', '\u03a6', '\u0393', '\u039b', '\u03a9', '\u03a0','\u03a8', '\u03a3', '\u0398', '\u039e',
    '€', 'Æ', 'æ', 'ß', 'É', ' ', '!', '"', '#', '¤', '%', '&', '\'', '(', ')','*', '+', ',', '-', '.', '/', 
    '0', '1', '2', '3', '4', '5', '6', '7','8', '9', 
    ':', ';', '<', '=', '>', '?', '¡', 
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
    'Ä',                                                                  'Ö', 
                                                                     'Ñ',                               'Ü', '§', '¿', 
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 
    'ä',                                                                  'ö', 
                                                                     'ñ',                               'ü', 
    'à')


def semi_octet_to_string(input) :
    """ Takes an octet and returns a string
    """
    out = ""
    i=0
    for i in range(0,len(input),2) : # from 0 - length, incrementing by 2
        out = out + input[i+1:i+2] + input[i:i+1]
    return out


def convert_character_to_seven_bit(character) :
    """ Takes a single character.
    Looks it up in the SEVEN_BIT_ALPHABET_ARRAY.
    Returns the position in the array.
    """
    for i in range(0,len(SEVEN_BIT_ALPHABET_ARRAY)) :
        if SEVEN_BIT_ALPHABET_ARRAY[i] == character:
            return i
    return 36 # If the character cannot be found, return a ¤ to indicate the missing character


def send_AT_command(cmd) :
    """ Send a command to the dongle
    """
    dongle.write(AT_COMMAND+cmd+'\r')
    
    
def get_SMSC_from_dongle() :
    """ Interogate the dongle and get the SMSC number
    """
    
    print "Asking the SIM for the SMSC"
    # find the SMSC
    send_AT_command('+CSCA?')

    # read the output, print it to screen. Stop when "OK" is seen
    while True:
        output = dongle.readline()
        print output
    
        # find the response about the SMSC
        if output.startswith("+CSCA:") :
            first_quote = output.find('"') + 1 # zero based index, first quote
            last_quote = output.rfind('"') # last quote
            SMSC_number = output[first_quote:last_quote] # Extract the string between the "
            print "The SMSC number is " + SMSC_number
            return SMSC_number

        if output.startswith("OK"):
            break
        if output.startswith("ERROR"):
            break



# Set the initial variables
FIRST_OCTET = "0100" # MAGIC
PROTO_ID = "00" # MORE MAGIC
data_encoding = "1" # EVEN MORE MAGIC
message_class = "" # Message Class. 0 for FLASH, 1 for normal
SMSC_number = "" # The message centre through which the SMS is sent
SMSC = "" # How the SMSC is represented once encoded
SMSC_info_length = 0
SMSC_length = 0
SMSC_number_format = "81" # by default, assume that it's in national format - e.g. 077...
destination_phone_number = "" # Where the SMS is being sent
destination_phone_number_format = "81" # by default, assume that it's in national format - e.g. 077...
message_text = "" # The message to be sent
encoded_message_binary_string = "" # The message, as encoded into binary
encoded_message_octet = "" # individual octets of the message
AT_COMMAND = "AT" # Commands sent to dongle should start with this
AT_SET_PDU = "+CMGF=0" # Command to set the dongle into PDU mode
SEND_CHARACTER = chr(26)

# Set up the connection to the dongle
dongle = serial.Serial(port="/dev/ttyUSB0",baudrate=115200,timeout=0,rtscts=0,xonxoff=0)

# Get the user inputs. No error checking in this version :-)
get_destination_phone_number = raw_input("Which phone number do you want to send an SMS to? (e.g. +447700900123) : ")
get_message_text = raw_input("What message do you want to send? : ")
get_message_class = raw_input("For FLASH SMS, type 0. For regular SMS, type 1 : ")

# TODO Error check & sanitize input
destination_phone_number = get_destination_phone_number
message_text = get_message_text
message_class = int(get_message_class)
SMSC_number = get_SMSC_from_dongle() #get_SMSC_number

# Set data encoding
data_encoding = data_encoding + str(message_class)

# Get the SMSC number format
if SMSC_number[:1] == '+' : # if the SMSC starts with a + then it is an international number
    SMSC_number_format = "91"; # international
    SMSC_number = SMSC_number[1:len(SMSC_number)] # Strip off the +

# Odd numbers need to be padded with an "F"
if len(SMSC_number)%2 != 0 : 
    SMSC_number = SMSC_number + "F"

# Encode the SMSC number
SMSC = semi_octet_to_string(SMSC_number)

# Calculate the SMSC values
SMSC_info_length = (len(SMSC_number_format + "" + SMSC))/2
SMSC_length = SMSC_info_length;

# Is the number we're sending to in international format?
if destination_phone_number[:1] == '+' : # if it starts with a + then it is an international number
    destination_phone_number_format = "91"; # international
    destination_phone_number = destination_phone_number[1:len(destination_phone_number)] # Strip off the +

# Calculate the destination values in hex (so remove 0x, make upper case, pad with zeros if needed)
destination_phone_number_length = hex(len(destination_phone_number))[2:3].upper().zfill(2)

if len(destination_phone_number)%2 != 0 : # Odd numbers need to be padded
    destination_phone_number = destination_phone_number + "F"

destination = semi_octet_to_string(destination_phone_number)

# Size of the message to be delivered in hex (so remove 0x, make upper case, pad with zeros if needed)
message_data_size = str(hex(len(message_text)))[2:len(message_text)].upper().zfill(2)

# Go through the message text, encoding each character
for i in range(0,len(message_text)) : 
    character = message_text[i:i+1] # get the current character
    current = bin(convert_character_to_seven_bit(character)) # translate into the 7bit alphabet
    character_string = str(current) # Make a string of the binary number. eg "0b1110100
    character_binary_string = character_string[2:len(str(character_string))] # Strip off the 0b
    character_padded_7_bit =  character_binary_string.zfill(7) # all text must contain 7 bits
    # Concatenate the bits
    # Note, they are added to the START of the string
    encoded_message_binary_string = character_padded_7_bit + encoded_message_binary_string 


# Reverse the string to make it easier to count
encoded_message_binary_string_reversed = encoded_message_binary_string[::-1]

# Get each octet into hex
for i in range(0,len(encoded_message_binary_string_reversed),8) : # from 0 - length, incrementing by 8
    # Get the 8 bits, reverse them back to normal, if less than 8, pad them with 0
    encoded_octet = encoded_message_binary_string_reversed[i:i+8][::-1].zfill(8)
    encoded_octet_hex = hex(int(encoded_octet,2)) # Convert to hex
    
    # Strip the 0x at the start, make uppercase, pad with a leading 0 if needed
    encoded_octet_hex_string = str(encoded_octet_hex)[2:len(encoded_octet_hex)].upper().zfill(2)
    
    # Concatenate the octet to the message
    encoded_message_octet = encoded_message_octet + encoded_octet_hex_string

# Generate the PDU
PDU = str(SMSC_info_length).zfill(2) \
        + str(SMSC_number_format) \
        + SMSC \
        + FIRST_OCTET \
        + str(destination_phone_number_length) \
        + destination_phone_number_format \
        + destination \
        + PROTO_ID \
        + data_encoding \
        + str(message_data_size) \
        + encoded_message_octet

# Generate the AT Commands
AT_CMGS = "+CMGS=" + str((len(PDU)/2) - SMSC_length - 1)

# Show the commands
print AT_COMMAND + AT_SET_PDU
print AT_COMMAND + AT_CMGS
print PDU

# Send the commands to the dongle
send_AT_command("") # Send an initial AT
send_AT_command(AT_SET_PDU) # Send the command to place the dongle in PDU mode
send_AT_command(AT_CMGS) # Send the command showing the length of the upcoming PDU, should prompt for input ">"
dongle.write(PDU) # Send the PDU
dongle.write(SEND_CHARACTER) # Submit the PDU
dongle.close() # Close the connection
