#!/usr/bin/env python3
"""
Enhanced Continuous Reader with HCE Detection
- Corrected logic for WaitForDiscoveryNotification
- Added Mermaid Sesame HCE app detection
- Sends SELECT AID F1726576406873 after reading any card
"""

from machine import I2C, Pin
import time

# Import the working Arduino library
exec(open('PN7150_working_library.py').read())

def print_hex_array(data, length):
    """Print hex array with proper formatting"""
    result = ""
    for i in range(length):
        result += f"0x{data[i]:02X} "
    return result.strip()

def extract_correct_uid(response, length):
    """Extract UID from correct position in RF_INTF_ACTIVATED_NTF response"""
    if length < 17:  # Need at least 17 bytes for UID
        return None
    
    print(f"  Full response: {print_hex_array(response, length)}")
    
    # Analyze response structure to find UID position
    # For MIFARE: UID is at positions 13-16 (4 bytes)
    # For NTAG: UID might be at different position due to longer response
    
    # Analyze the response structure
    if length >= 20:
        # Look for the UID length pattern
        if response[11] == 0x04 and response[12] == 0x00 and response[13] == 0x04:
            # MIFARE pattern: 0x04 0x00 0x04 [UID]
            uid_start = 14
            uid_length = 4
        elif response[12] == 0x07 and response[13] == 0x04:
            # NTAG pattern: 0x07 0x04 [UID]
            uid_start = 13
            uid_length = 7
        else:
            # Fallback to position 13
            uid_start = 13
            uid_length = 4
    
    if length >= uid_start + uid_length:
        uid = response[uid_start:uid_start + uid_length]
        return uid
    
    return None

def send_select_aid(nfc, aid):
    """Send SELECT APDU command to check for HCE app"""
    # SELECT APDU: CLA=00, INS=A4, P1=04, P2=00, Lc=07, AID=F1726576406873
    # FIXED: No trailing 0x00 - exact format: 5 header + 1 Lc + 7 AID = 13 bytes total
    select_cmd = bytearray([0x00, 0xA4, 0x04, 0x00, 0x07]) + aid
    print(f"  Sending SELECT AID: {print_hex_array(select_cmd, len(select_cmd))}")
    print(f"  APDU length: {len(select_cmd)} bytes (should be 12)")
    
    # Use SendApduCommand to send APDU
    response = nfc.SendApduCommand(select_cmd)
    
    if response and len(response) >= 2:  # At least 2 bytes SW
        if len(response) >= 8:  # 6 bytes data + 2 bytes SW
            response_data = response[:6]
            status_words = response[6:8]
        else:
            response_data = None
            status_words = response[-2:]
        
        if status_words[0] == 0x90 and status_words[1] == 0x00:
            if response_data:
                print(f"  HCE Response Data: {print_hex_array(response_data, 6)}")
                return response_data
            else:
                print("  HCE Response: Success (no data)")
                return bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x06])  # Default response
        else:
            print(f"  SELECT AID failed: SW={status_words[0]:02X}{status_words[1]:02X}")
    elif response:
        print(f"  SELECT AID failed: Invalid response length {len(response)}")
    else:
        print("  No response received")
    
    return None

def stop_discovery(nfc):
    """Stop discovery process - EXACT from Arduino library"""
    NCIStopDiscovery = bytearray([0x21, 0x06, 0x01, 0x00])
    nfc.writeData(NCIStopDiscovery, len(NCIStopDiscovery))
    nfc.getMessage()
    nfc.getMessage(1000)
    return True

def reset_mode(nfc, mode):
    """Reset mode - EXACT from Arduino example"""
    print("Re-initializing...")
    nfc.ConfigMode(mode)
    nfc.StartDiscovery(mode)

def final_continuous_reader():
    print("=== Enhanced Continuous Reader with HCE Detection ===")
    print("IRQ=15, VEN=14 (matching Arduino example)")
    print("Place any MIFARE card or Android phone with Mermaid Sesame app near the reader...")
    print()
    
    # Initialize I2C
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
    
    # Create PN7150 instance with Arduino example pins
    nfc = Electroniccats_PN7150(IRQpin=15, VENpin=14, I2Caddress=0x28, wire=i2c)
    
    print("Initializing...")
    if nfc.connectNCI():
        print("Error while setting up the mode, check connections!")
        return
    
    print("Configuring settings...")
    if nfc.ConfigureSettings():
        print("The Configure Settings is failed!")
        return
    
    mode = 1  # Reader/Writer mode
    
    print("Configuring mode...")
    if nfc.ConfigMode(mode):
        print("The Configure Mode is failed!!")
        return
    
    nfc.StartDiscovery(mode)
    print("Ready! Place a MIFARE card near the reader...")
    print()
    
    card_count = 0
    
    # Continuous detection loop - EXACT like Arduino example
    while True:
        card_count += 1
        print(f"\n=== CARD #{card_count} ===")
        print("Waiting for card...")
        
        RfInterface = RfIntf_t()
        
        # CORRECTED: WaitForDiscoveryNotification returns True when card is detected
        if nfc.WaitForDiscoveryNotification(RfInterface):  # Card detected
            print(f"Found card! Protocol: 0x{RfInterface.Protocol:02X}, ModeTech: 0x{RfInterface.ModeTech:02X}")
            
            # Check if it's NFC-A technology (MIFARE, NTAG, etc.)
            if RfInterface.ModeTech == (MODE_POLL | TECH_PASSIVE_NFCA):
                # Extract UID from raw response
                uid = extract_correct_uid(nfc.rxBuffer, nfc.rxMessageLength)
                if uid:
                    uid_str = ":".join([f"{b:02X}" for b in uid])
                    print(f"CARD UID: {uid_str}")
                    
                    # Identify card type based on protocol
                    if RfInterface.Protocol == PROT_MIFARE:
                        print("Card type: MIFARE")
                    elif RfInterface.Protocol == 0x02:  # ISO-DEP
                        print("Card type: NTAG/ISO-DEP")
                    elif RfInterface.Protocol == 0x04:  # Android HCE
                        print("Card type: Android HCE (Google Pay)")
                    else:
                        print(f"Card type: Unknown (Protocol: 0x{RfInterface.Protocol:02X})")
                    
                    print("Card read successfully!")
                    
                    # Try to detect Mermaid Sesame HCE app
                    print("  Checking for Mermaid Sesame HCE app...")
                    mermaid_aid = bytearray([0xF1, 0x72, 0x65, 0x76, 0x40, 0x68, 0x73])  # F1726576406873
                    hce_response = send_select_aid(nfc, mermaid_aid)
                    
                    if hce_response:
                        print("  *** MERMAID SESAME HCE DETECTED! ***")
                        print(f"  Response: {print_hex_array(hce_response, 6)}")
                    else:
                        print("  No Mermaid Sesame HCE app found")
                    
                    # Also try reference app AID for testing
                    print("  Checking for reference HCE app...")
                    reference_aid = bytearray([0xF2, 0x23, 0x34, 0x45, 0x56, 0x67])  # F22334455667
                    ref_response = send_select_aid(nfc, reference_aid)
                    
                    if ref_response:
                        print("  *** REFERENCE HCE APP DETECTED! ***")
                        print(f"  Response: {print_hex_array(ref_response, len(ref_response))}")
                    else:
                        print("  No reference HCE app found")
                    
                else:
                    print("UID extraction failed")
            else:
                print(f"Unknown card technology: 0x{RfInterface.ModeTech:02X}")
            
            # Handle multiple cards if present
            if RfInterface.MoreTags:
                print("Multiple cards detected!")
                # nfc.ReaderActivateNext(&RfInterface)  # Not implemented yet
            
            # Wait for card removal (simplified)
            print("Remove card...")
            time.sleep_ms(1000)
            
            # EXACT Arduino pattern: StopDiscovery, StartDiscovery, ResetMode
            print("Stopping discovery...")
            stop_discovery(nfc)
            
            print("Starting discovery...")
            nfc.StartDiscovery(mode)
            
            print("Resetting mode...")
            reset_mode(nfc, mode)
            
            print("Ready for next card!")
        else:
            print("No card detected")
        
        print("-" * 50)
        time.sleep_ms(500)

if __name__ == "__main__":
    final_continuous_reader() 