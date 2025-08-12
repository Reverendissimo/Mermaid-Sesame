#!/usr/bin/env python3
"""
Android HCE Test
Test communication with Android's built-in HCE services
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

def test_android_hce():
    print("=== Android HCE Communication Test ===")
    print("Testing communication with Android's built-in HCE services")
    print("This will help verify if HCE routing is working")
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
                
                print("Testing various AIDs...")
                
                # Test 1: ISO 14443-4 SELECT
                print("1. Testing ISO 14443-4 SELECT")
                select_cmd = bytearray([0x00, 0xA4, 0x04, 0x00, 0x00])
                print(f"   APDU: {print_hex_array(select_cmd, len(select_cmd))}")
                response = nfc.SendApduCommand(select_cmd)
                if response:
                    print(f"   Response: {print_hex_array(response, len(response))}")
                else:
                    print("   No response")
                
                # Test 2: GET VERSION command
                print("2. Testing GET VERSION")
                get_version_cmd = bytearray([0x00, 0xCA, 0x9F, 0x36, 0x00])
                print(f"   APDU: {print_hex_array(get_version_cmd, len(get_version_cmd))}")
                response = nfc.SendApduCommand(get_version_cmd)
                if response:
                    print(f"   Response: {print_hex_array(response, len(response))}")
                else:
                    print("   No response")
                
                # Test 3: SELECT PPSE (Payment)
                print("3. Testing SELECT PPSE (Payment)")
                ppse_aid = bytearray([0x32, 0x50, 0x41, 0x59, 0x2E, 0x53, 0x59, 0x53, 0x2E, 0x44, 0x44, 0x46, 0x30, 0x31])
                select_cmd = bytearray([0x00, 0xA4, 0x04, 0x00, 0x0E]) + ppse_aid
                print(f"   APDU: {print_hex_array(select_cmd, len(select_cmd))}")
                response = nfc.SendApduCommand(select_cmd)
                if response:
                    print(f"   Response: {print_hex_array(response, len(response))}")
                else:
                    print("   No response")
                
                # Test 4: Mermaid Sesame AID
                print("4. Testing Mermaid Sesame AID: F1726576406873")
                mermaid_aid = bytearray([0xF1, 0x72, 0x65, 0x76, 0x40, 0x68, 0x73])
                select_cmd = bytearray([0x00, 0xA4, 0x04, 0x00, 0x07]) + mermaid_aid
                print(f"   APDU: {print_hex_array(select_cmd, len(select_cmd))}")
                response = nfc.SendApduCommand(select_cmd)
                if response:
                    print(f"   Response: {print_hex_array(response, len(response))}")
                    if len(response) >= 8:
                        data = response[:6]
                        sw = response[6:8]
                        if sw[0] == 0x90 and sw[1] == 0x00:
                            print("   *** SUCCESS: Mermaid Sesame HCE working! ***")
                            print(f"   Response data: {print_hex_array(data, 6)}")
                        else:
                            print(f"   Status: {print_hex_array(sw, 2)}")
                else:
                    print("   No response")
                
                print("\n=== Analysis ===")
                print("If any command works:")
                print("  -> HCE routing is functional")
                print("  -> Issue is with Mermaid Sesame app configuration")
                print("If all commands fail:")
                print("  -> HCE routing issue or phone not properly configured")
                print("  -> Check Android NFC settings and permissions")
                
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
    test_android_hce() 