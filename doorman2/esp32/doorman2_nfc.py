#!/usr/bin/env python3
"""
Doorman2 NFC Reader Module for ESP32
Supports both PN532 and PN7150 NFC readers with unified interface
"""

import asyncio

# Static configuration - set to "pn7150" or "pn532"
NFC_READER_TYPE = "pn7150"  # Change this to "pn532" if using PN532 instead

# Import PN7150 constants at module level
try:
    from lib_PN7150 import lib_PN7150, RfIntf_t, SUCCESS, MODE_POLL, TECH_PASSIVE_NFCA, PROT_ISODEP
    PN7150_AVAILABLE = True
except ImportError:
    PN7150_AVAILABLE = False

class Nfc:
    """
    Unified NFC reader class supporting both PN532 and PN7150.
    
    Provides a consistent interface for NFC card detection regardless of
    the underlying hardware implementation. Auto-detects available reader
    and falls back gracefully between PN7150 and PN532.
    
    UID Format:
        Both readers return variable length UIDs (4, 7, or 10 bytes).
        The main application uses only the first 4 bytes for hash generation.
        This ensures compatibility across different card types.
    
    Hardware Configurations:
        PN7150: IRQ=15, VEN=14, SCL=22, SDA=21, I2C_ADDR=0x28
        PN532:  UART_ID=2, RX=19, TX=22
    """
    
    def __init__(self):
        """
        Initialize NFC reader with static configuration.
        
        Uses the NFC_READER_TYPE constant to determine which reader to use.
        Set NFC_READER_TYPE to "pn7150" or "pn532" at the top of this file.
        """
        self._uids = []
        self._flag = asyncio.Event()
        self._reader_type = NFC_READER_TYPE
        self._reader = None
        
        print(f"NFC Reader configured: {self._reader_type}")

    async def wait_uid(self):
        """
        Wait for and return the next detected NFC card UID.
        
        Discards any previously queued UIDs and waits for a new card detection.
        This method maintains the same interface as the original implementation.
        
        Returns:
            bytearray: Card UID bytes, or None if timeout/error
        """
        # discard queued uids
        for _ in range(len(self._uids)):
            self._uids.pop()

        while not self._uids:
            await self._flag.wait()
            self._flag.clear()

        uid = None
        while self._uids:
            uid = self._uids.pop()
        return uid

    async def loop(self):
        """
        Main NFC detection loop using the detected reader type.
        
        Uses the reader type detected at initialization.
        Maintains the same interface regardless of which reader is used.
        """
        if self._reader_type == "pn7150":
            await self._loop_pn7150()
        elif self._reader_type == "pn532":
            await self._loop_pn532()
        else:
            raise RuntimeError("No NFC reader detected or available")

    async def _loop_pn7150(self):
        """
        PN7150 NFC reader implementation.
        
        Uses lib_PN7150 for advanced NFC functionality including
        better protocol support and HCE detection capabilities.
        """
        if not PN7150_AVAILABLE:
            raise ImportError("PN7150 library not available")
        
        # Initialize PN7150 with default configuration
        self._reader = lib_PN7150(IRQpin=15, VENpin=14, SCLpin=22, SDApin=21, I2Caddress=0x28)
        self._reader_type = "pn7150"
        
        # Configure for Read/Write mode
        if self._reader.ConfigMode(1) != SUCCESS:
            raise Exception("Failed to configure PN7150 mode")
        
        # Start discovery
        if self._reader.StartDiscovery(1) != SUCCESS:
            raise Exception("Failed to start PN7150 discovery")
        
        print("Using PN7150 NFC reader")
        
        rf_intf = RfIntf_t()
        
        while True:
            # Wait for card detection with 250ms timeout
            if self._reader.WaitForDiscoveryNotification(rf_intf, 250):
                # Check if it's HCE (Android phone) or physical card
                if rf_intf.Protocol == PROT_ISODEP:
                    # It's an HCE device - get HCE response data
                    hce_data = await self._get_hce_response()
                    if hce_data:
                        self._uids.append(hce_data)
                        self._flag.set()
                else:
                    # It's a physical card - extract UID
                    uid = self._extract_uid_pn7150(rf_intf)
                    if uid:
                        self._uids.append(uid)
                        self._flag.set()
                
                # Restart discovery for next card
                self._reader.StopDiscovery()
                self._reader.StartDiscovery(1)
            
            await asyncio.sleep(0.25)

    async def _loop_pn532(self):
        """
        PN532 NFC reader implementation (fallback).
        
        Uses the original PN532 implementation for backward compatibility.
        """
        from pn532 import PN532Uart, PN532Error
        
        self._reader = PN532Uart(2, rx=19, tx=22)
        self._reader_type = "pn532"

        try:
            self._reader.SAM_configuration()
            ic, ver, rev, support = self._reader.get_firmware_version()
            print(f'Found PN532 with firmware version: {ver}.{rev}')
        except Exception as e:
            print('PN532 initialization failed:', e)
            raise

        while True:
            uid = None
            try:
                uid = self._reader.read_passive_target()
            except PN532Error as e:
                print('PN532:', e)

            self._reader.power_down()

            if uid is not None:
                self._uids.append(uid)
                self._flag.set()

            await asyncio.sleep(0.25)

    def _extract_uid_pn7150(self, rf_intf):
        """
        Extract UID from PN7150 RF interface response.
        
        This method parses the PN7150 response to extract the card UID,
        similar to the logic used in the continuous scanner.
        
        IMPORTANT: Returns variable length UIDs (4, 7, or 10 bytes) just like PN532.
        The main application handles this by using only the first 4 bytes for hash generation.
        
        Args:
            rf_intf: RfIntf_t object containing tag information
            
        Returns:
            bytearray: Card UID bytes (variable length), or None if extraction fails
        """
        # Check if it's NFC-A technology
        if not PN7150_AVAILABLE:
            return None
        if rf_intf.ModeTech != (MODE_POLL | TECH_PASSIVE_NFCA):
            return None
        
        # Extract UID from the raw response buffer
        response = self._reader.rxBuffer
        length = self._reader.rxMessageLength
        
        if length < 17:  # Need at least 17 bytes for UID
            return None
        
        # Analyze response structure to find UID position
        # For MIFARE: UID is at positions 13-16 (4 bytes)
        # For NTAG: UID might be at different position due to longer response
        
        uid_start = 13
        uid_length = 4
        
        # Look for specific patterns in longer responses
        if length >= 20:
            if response[11] == 0x04 and response[12] == 0x00 and response[13] == 0x04:
                # MIFARE pattern: 0x04 0x00 0x04 [UID]
                uid_start = 14
                uid_length = 4
            elif response[12] == 0x07 and response[13] == 0x04:
                # NTAG pattern: 0x07 0x04 [UID]
                uid_start = 13
                uid_length = 7
            elif length >= 25:  # Check for longer UIDs (10 bytes)
                # Some cards might have longer UIDs
                if response[11] == 0x0A and response[12] == 0x04:
                    uid_start = 13
                    uid_length = 10
        
        # Extract UID if we have enough data
        if length >= uid_start + uid_length:
            uid = response[uid_start:uid_start + uid_length]
            # Ensure we return the full UID length (main app will take [:4] as needed)
            return uid
        
        return None

    async def _get_hce_response(self):
        """
        Get HCE response data from Android phone.
        
        Sends SELECT AID command to check for HCE apps and returns
        the response data which will be used as the authentication ID.
        
        Returns:
            bytearray: HCE response data, or None if no response
        """
        # Mermaid Sesame HCE AID (as used in the continuous scanner)
        mermaid_aid = bytearray([0xF1, 0x72, 0x65, 0x76, 0x40, 0x68, 0x73])  # F1726576406873
        
        try:
            # Send SELECT APDU command
            aid_length = len(mermaid_aid)
            select_cmd = bytearray([0x00, 0xA4, 0x04, 0x00, aid_length]) + mermaid_aid
            
            # Use SendApduCommand to send APDU
            response = self._reader.SendApduCommand(select_cmd)
            
            if response:
                # Check for success status (last 2 bytes should be 0x90 0x00)
                if len(response) >= 2:
                    status = response[-2:]
                    if status == bytearray([0x90, 0x00]):
                        # Return the response data without status bytes
                        hce_data = response[:-2]
                        print(f"HCE Response received: {len(hce_data)} bytes")
                        return hce_data
                    else:
                        print(f"HCE Status failed: {status.hex()}")
                        return None
                else:
                    print("HCE Invalid response")
                    return None
            else:
                print("No HCE response received")
                return None
                
        except Exception as e:
            print(f"HCE communication error: {e}")
            return None

    def get_reader_type(self):
        """
        Get the currently active reader type.
        
        Returns:
            str: "pn7150", "pn532", or None if not initialized
        """
        return self._reader_type
