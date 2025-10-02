#!/usr/bin/env python3
"""
Professional NFC Reader for Mermaid Sesame HCE Detection
ESP32 with PN7150 NFC Controller using lib_PN7150 library
"""

from machine import I2C, Pin
import time

# Import the MicroPython PN7150 library
exec(open('lib_PN7150.py').read())

def print_hex_array(data, length):
    """Convert byte array to hex string"""
    return ' '.join([f'0x{byte:02X}' for byte in data[:length]])

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
    # SELECT APDU: CLA=00, INS=A4, P1=04, P2=00, Lc=length, AID=variable
    aid_length = len(aid)
    select_cmd = bytearray([0x00, 0xA4, 0x04, 0x00, aid_length]) + aid
    print(f"  Sending SELECT AID: {print_hex_array(select_cmd, len(select_cmd))}")
    print(f"  APDU length: {len(select_cmd)} bytes")
    
    # Use SendApduCommand to send APDU
    response = nfc.SendApduCommand(select_cmd)
    
    if response:
        print(f"  HCE Response Data: {print_hex_array(response, len(response))}")
        
        # Check for success status (last 2 bytes should be 0x90 0x00)
        if len(response) >= 2:
            status = response[-2:]
            if status == bytearray([0x90, 0x00]):
                print(f"  Status: SUCCESS (0x90 0x00)")
                return response[:-2]  # Return data without status bytes
            else:
                print(f"  Status: FAILED ({print_hex_array(status, 2)})")
                return None
        else:
            print("  Status: INVALID RESPONSE")
            return None
    else:
        print("  No response received")
        return None

def main():
    print("=== Professional NFC Reader for Mermaid Sesame HCE ===")
    print("Using lib_PN7150 library - IRQ=15, VEN=14, SCL=22, SDA=21")
    print("Place Android phone with Mermaid Sesame app near the reader...")
    print()
    
    try:
        # Initialize I2C
        i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
        
        # Create PN7150 instance using the new lib_PN7150 library
        # The library automatically initializes the chip
        nfc = lib_PN7150(IRQpin=15, VENpin=14, SCLpin=22, SDApin=21, I2Caddress=0x28, wire=i2c)
        
        print("PN7150 initialized successfully!")
        
        # Configure for Reader/Writer mode (mode 1)
        mode = 1
        
        print("Configuring for Reader/Writer mode...")
        if nfc.ConfigMode(mode) != SUCCESS:
            print("ERROR: Failed to configure mode")
            return
        
        print("Starting discovery...")
        if nfc.StartDiscovery(mode) != SUCCESS:
            print("ERROR: Failed to start discovery")
            return
        
        print("Ready! Place a card near the reader...")
        print()
        
        card_count = 0
        
        while True:
            card_count += 1
            print(f"=== CARD #{card_count} ===")
            print("Waiting for card...")
            
            RfInterface = RfIntf_t()
            
            # Wait for card detection
            if nfc.WaitForDiscoveryNotification(RfInterface):  # Card detected
                print(f"Found card! Protocol: 0x{RfInterface.Protocol:02X}, ModeTech: 0x{RfInterface.ModeTech:02X}")
                
                # Check if it's NFC-A technology (MIFARE, NTAG, etc.)
                if RfInterface.ModeTech == (MODE_POLL | TECH_PASSIVE_NFCA):
                    # Extract UID from raw response
                    uid = extract_correct_uid(nfc.rxBuffer, nfc.rxMessageLength)
                    if uid:
                        uid_str = ":".join([f"{b:02X}" for b in uid])
                        print(f"Card UID: {uid_str}")
                        
                        # Identify card type based on protocol
                        if RfInterface.Protocol == PROT_MIFARE:
                            print("Card type: MIFARE")
                        elif RfInterface.Protocol == PROT_T2T:
                            print("Card type: Type 2 Tag (NTAG)")
                        elif RfInterface.Protocol == PROT_ISODEP:
                            print("Card type: ISO-DEP (Android HCE)")
                        else:
                            print(f"Card type: Unknown (Protocol: 0x{RfInterface.Protocol:02X})")
                        
                        print("Card read successfully!")
                        
                        # Check for Mermaid Sesame HCE app
                        print("  Checking for Mermaid Sesame HCE app...")
                        mermaid_aid = bytearray([0xF1, 0x72, 0x65, 0x76, 0x40, 0x68, 0x73])  # F1726576406873
                        hce_response = send_select_aid(nfc, mermaid_aid)
                        
                        if hce_response:
                            print("  MERMAID SESAME HCE DETECTED!")
                            print(f"  Response: {print_hex_array(hce_response, len(hce_response))}")
                            
                            # Convert response to readable format
                            try:
                                response_text = hce_response.decode('utf-8', errors='ignore')
                                print(f"  Response as text: '{response_text}'")
                            except:
                                print("  Response cannot be decoded as text")
                        else:
                            print("  No Mermaid Sesame HCE app found")
                    else:
                        print("UID extraction failed")
                else:
                    print(f"Unknown card technology: 0x{RfInterface.ModeTech:02X}")
            else:
                print("No card detected")
                continue
            
            print("Remove card...")
            time.sleep_ms(1000)
            
            # Stop and restart discovery
            print("Stopping discovery...")
            nfc.StopDiscovery()
            
            print("Starting discovery...")
            nfc.StartDiscovery(mode)
            time.sleep_ms(500)
            
            print("Ready for next card!")
            print("-" * 50)
            print()
            
    except Exception as e:
        print(f"Initialization error: {e}")
        return

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nReader stopped by user")
    except Exception as e:
        print(f"ERROR: {e}")
