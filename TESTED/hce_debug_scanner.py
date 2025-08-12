#!/usr/bin/env python3
"""
HCE Debug Scanner
Detailed debugging for Android HCE communication
"""

from machine import I2C, Pin
import time

# Import the working Arduino library
exec(open('PN7150_working_library.py').read())

def print_hex_array(data, length):
    """Print hex array with proper formatting"""
    result = ""
    for i in range(min(length, len(data))):
        result += f"0x{data[i]:02X} "
    return result.strip()

def debug_nci_messages(nfc):
    """Debug all NCI messages"""
    print("  === NCI Message Debug ===")
    print(f"  Buffer length: {nfc.rxMessageLength}")
    if nfc.rxMessageLength > 0:
        print(f"  Raw buffer: {print_hex_array(nfc.rxBuffer, nfc.rxMessageLength)}")
        
        # Parse NCI message type
        if nfc.rxMessageLength >= 2:
            msg_type = nfc.rxBuffer[0]
            msg_id = nfc.rxBuffer[1]
            
            print(f"  Message Type: 0x{msg_type:02X}")
            print(f"  Message ID: 0x{msg_id:02X}")
            
            # Check for specific NCI messages
            if msg_type == 0x40:  # Response
                if msg_id == 0x00:  # RF_TRANSCEIVE_RSP
                    print("  -> RF_TRANSCEIVE_RSP")
                    if nfc.rxMessageLength >= 3:
                        payload_len = nfc.rxBuffer[2]
                        print(f"  Payload length: {payload_len}")
                        if payload_len > 0 and nfc.rxMessageLength >= 3 + payload_len:
                            payload = nfc.rxBuffer[3:3+payload_len]
                            print(f"  Payload: {print_hex_array(payload, len(payload))}")
                elif msg_id == 0x06:  # RF_DISCOVER_RSP
                    print("  -> RF_DISCOVER_RSP")
                elif msg_id == 0x08:  # RF_DEACTIVATE_RSP
                    print("  -> RF_DEACTIVATE_RSP")
            elif msg_type == 0x60:  # Notification
                if msg_id == 0x05:  # RF_INTF_ACTIVATED_NTF
                    print("  -> RF_INTF_ACTIVATED_NTF")
                    if nfc.rxMessageLength >= 3:
                        payload_len = nfc.rxBuffer[2]
                        print(f"  Payload length: {payload_len}")
                        if payload_len > 0 and nfc.rxMessageLength >= 3 + payload_len:
                            payload = nfc.rxBuffer[3:3+payload_len]
                            print(f"  Payload: {print_hex_array(payload, len(payload))}")
                            
                            # Parse RF_INTF_ACTIVATED_NTF
                            if len(payload) >= 4:
                                rf_disc_id = payload[0]
                                rf_interface = payload[1]
                                rf_protocol = payload[2]
                                rf_tech_param_len = payload[3]
                                print(f"  RF Discovery ID: 0x{rf_disc_id:02X}")
                                print(f"  RF Interface: 0x{rf_interface:02X}")
                                print(f"  RF Protocol: 0x{rf_protocol:02X}")
                                print(f"  RF Tech Param Length: {rf_tech_param_len}")
                                
                                # Check if it's ISO-DEP (Android HCE)
                                if rf_protocol == 0x04:  # ISO-DEP
                                    print("  *** ISO-DEP (Android HCE) detected! ***")
                elif msg_id == 0x06:  # RF_DISCOVER_NTF
                    print("  -> RF_DISCOVER_NTF")
                elif msg_id == 0x08:  # RF_DEACTIVATE_NTF
                    print("  -> RF_DEACTIVATE_NTF")
            elif msg_type == 0x20:  # Command
                if msg_id == 0x00:  # CORE_RESET_CMD
                    print("  -> CORE_RESET_CMD")
                elif msg_id == 0x01:  # CORE_INIT_CMD
                    print("  -> CORE_INIT_CMD")
                elif msg_id == 0x06:  # RF_DISCOVER_CMD
                    print("  -> RF_DISCOVER_CMD")
                elif msg_id == 0x00:  # RF_TRANSCEIVE_CMD
                    print("  -> RF_TRANSCEIVE_CMD")

def test_hce_communication(nfc):
    """Test HCE communication with detailed logging"""
    print("  === Testing HCE Communication ===")
    
    # Test 1: Send SELECT AID for Mermaid Sesame
    print("  Test 1: SELECT AID F1726576406873")
    mermaid_aid = bytearray([0xF1, 0x72, 0x65, 0x76, 0x40, 0x68, 0x73])
    select_cmd = bytearray([0x00, 0xA4, 0x04, 0x00, 0x07]) + mermaid_aid
    print(f"  APDU: {print_hex_array(select_cmd, len(select_cmd))}")
    
    response = nfc.SendApduCommand(select_cmd)
    if response:
        print(f"  Response: {print_hex_array(response, len(response))}")
        if len(response) >= 8:
            data = response[:6]
            sw = response[6:8]
            print(f"  Data: {print_hex_array(data, 6)}")
            print(f"  Status Words: {print_hex_array(sw, 2)}")
            if sw[0] == 0x90 and sw[1] == 0x00:
                print("  *** SUCCESS: Mermaid Sesame HCE detected! ***")
                return True
            else:
                print(f"  FAILED: SW={sw[0]:02X}{sw[1]:02X}")
        else:
            print(f"  FAILED: Invalid response length {len(response)}")
    else:
        print("  FAILED: No response")
    
    # Test 2: Send SELECT AID for Google Pay (for comparison)
    print("  Test 2: SELECT AID for Google Pay")
    google_aid = bytearray([0xA0, 0x00, 0x00, 0x03, 0x33, 0x01, 0x01, 0x01])
    select_cmd = bytearray([0x00, 0xA4, 0x04, 0x00, 0x08]) + google_aid
    print(f"  APDU: {print_hex_array(select_cmd, len(select_cmd))}")
    
    response = nfc.SendApduCommand(select_cmd)
    if response:
        print(f"  Response: {print_hex_array(response, len(response))}")
    else:
        print("  No response")
    
    return False

def hce_debug_scanner():
    print("=== HCE Debug Scanner ===")
    print("IRQ=15, VEN=14")
    print("Place Android phone with Mermaid Sesame app near the reader...")
    print()
    
    # Initialize I2C
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
    
    # Create PN7150 instance
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
    print("Ready! Place Android phone near the reader...")
    print()
    
    card_count = 0
    
    while True:
        card_count += 1
        print(f"\n=== CARD #{card_count} ===")
        print("Waiting for card...")
        
        RfInterface = RfIntf_t()
        
        if nfc.WaitForDiscoveryNotification(RfInterface):
            print(f"Found card! Protocol: 0x{RfInterface.Protocol:02X}, ModeTech: 0x{RfInterface.ModeTech:02X}")
            
            # Debug all NCI messages
            debug_nci_messages(nfc)
            
            # Check if it's NFC-A technology
            if RfInterface.ModeTech == (MODE_POLL | TECH_PASSIVE_NFCA):
                # Extract UID
                uid = extract_correct_uid(nfc.rxBuffer, nfc.rxMessageLength)
                if uid:
                    uid_str = ":".join([f"{b:02X}" for b in uid])
                    print(f"CARD UID: {uid_str}")
                    
                    # Identify card type
                    if RfInterface.Protocol == PROT_MIFARE:
                        print("Card type: MIFARE")
                    elif RfInterface.Protocol == 0x02:
                        print("Card type: NTAG/ISO-DEP")
                    elif RfInterface.Protocol == 0x04:
                        print("Card type: Android HCE (ISO-DEP)")
                    else:
                        print(f"Card type: Unknown (Protocol: 0x{RfInterface.Protocol:02X})")
                    
                    print("Card read successfully!")
                    
                    # Test HCE communication
                    if RfInterface.Protocol == 0x04:  # ISO-DEP
                        print("  Testing HCE communication...")
                        hce_detected = test_hce_communication(nfc)
                        if hce_detected:
                            print("  *** MERMAID SESAME HCE WORKING! ***")
                        else:
                            print("  *** HCE communication failed ***")
                            print("  Possible issues:")
                            print("  1. Mermaid Sesame app not running")
                            print("  2. HCE routing not working")
                            print("  3. App not in foreground")
                            print("  4. NFC permissions not granted")
                    
                else:
                    print("UID extraction failed")
            else:
                print(f"Unknown card technology: 0x{RfInterface.ModeTech:02X}")
            
            # Wait for card removal
            print("Remove card...")
            time.sleep_ms(2000)
            
            # Reset for next card
            print("Resetting...")
            nfc.StopDiscovery()
            nfc.StartDiscovery(mode)
            
        else:
            print("No card detected")
        
        print("-" * 50)
        time.sleep_ms(1000)

def extract_correct_uid(response, length):
    """Extract UID from correct position in RF_INTF_ACTIVATED_NTF response"""
    if length < 17:
        return None
    
    # Analyze the response structure
    if length >= 20:
        if response[11] == 0x04 and response[12] == 0x00 and response[13] == 0x04:
            uid_start = 14
            uid_length = 4
        elif response[12] == 0x07 and response[13] == 0x04:
            uid_start = 13
            uid_length = 7
        else:
            uid_start = 13
            uid_length = 4
    
    if length >= uid_start + uid_length:
        uid = response[uid_start:uid_start + uid_length]
        return uid
    
    return None

if __name__ == "__main__":
    hce_debug_scanner() 