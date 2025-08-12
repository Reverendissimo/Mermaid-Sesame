#!/usr/bin/env python3
"""
Simple HCE Test
Focus on Android HCE routing and AID selection
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

def simple_hce_test():
    print("=== Simple HCE Test ===")
    print("Testing Android HCE routing and AID selection")
    print("Make sure Mermaid Sesame app is running and in foreground!")
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
    print("Ready! Place Android phone with Mermaid Sesame app near the reader...")
    print()
    
    while True:
        print("\n=== Waiting for Android HCE ===")
        
        RfInterface = RfIntf_t()
        
        if nfc.WaitForDiscoveryNotification(RfInterface):
            print(f"Found device! Protocol: 0x{RfInterface.Protocol:02X}")
            
            # Check if it's ISO-DEP (Android HCE)
            if RfInterface.Protocol == 0x04:  # ISO-DEP
                print("*** Android HCE (ISO-DEP) detected! ***")
                
                # Extract UID
                if nfc.rxMessageLength >= 20:
                    uid_start = 14
                    uid = nfc.rxBuffer[uid_start:uid_start+4]
                    uid_str = ":".join([f"{b:02X}" for b in uid])
                    print(f"Device UID: {uid_str}")
                
                print("Testing AID selection...")
                
                # Test 1: Mermaid Sesame AID
                print("1. Testing Mermaid Sesame AID: F1726576406873")
                mermaid_aid = bytearray([0xF1, 0x72, 0x65, 0x76, 0x40, 0x68, 0x73])
                select_cmd = bytearray([0x00, 0xA4, 0x04, 0x00, 0x07]) + mermaid_aid
                
                print(f"   APDU: {print_hex_array(select_cmd, len(select_cmd))}")
                response = nfc.SendApduCommand(select_cmd)
                
                if response:
                    print(f"   Response: {print_hex_array(response, len(response))}")
                    if len(response) >= 8:
                        data = response[:6]
                        sw = response[6:8]
                        print(f"   Data: {print_hex_array(data, 6)}")
                        print(f"   Status: {print_hex_array(sw, 2)}")
                        
                        if sw[0] == 0x90 and sw[1] == 0x00:
                            print("   *** SUCCESS: Mermaid Sesame HCE working! ***")
                            print(f"   Response data: {print_hex_array(data, 6)}")
                        else:
                            print(f"   FAILED: Status words {sw[0]:02X}{sw[1]:02X}")
                    else:
                        print(f"   FAILED: Invalid response length {len(response)}")
                else:
                    print("   FAILED: No response")
                
                # Test 2: Generic AID for comparison
                print("2. Testing generic AID: A0000002471001")
                generic_aid = bytearray([0xA0, 0x00, 0x00, 0x02, 0x47, 0x10, 0x01])
                select_cmd = bytearray([0x00, 0xA4, 0x04, 0x00, 0x07]) + generic_aid
                
                print(f"   APDU: {print_hex_array(select_cmd, len(select_cmd))}")
                response = nfc.SendApduCommand(select_cmd)
                
                if response:
                    print(f"   Response: {print_hex_array(response, len(response))}")
                else:
                    print("   No response")
                
                print("\n=== HCE Routing Analysis ===")
                print("If Mermaid Sesame AID fails but generic AID works:")
                print("  -> HCE routing is working, but app not responding")
                print("If both fail:")
                print("  -> HCE routing issue or app not properly configured")
                print("If Mermaid Sesame AID works:")
                print("  -> Everything is working perfectly!")
                
            else:
                print(f"Not Android HCE (Protocol: 0x{RfInterface.Protocol:02X})")
            
            print("\nRemove device and try again...")
            time.sleep_ms(3000)
            
            # Reset for next test
            nfc.StopDiscovery()
            nfc.StartDiscovery(mode)
            
        else:
            print("No device detected")
        
        time.sleep_ms(1000)

if __name__ == "__main__":
    simple_hce_test() 