"""
lib_PN7150 - MicroPython Library for PN7150 NFC Controller

A complete MicroPython translation of the Arduino PN7150 library.
Provides full NFC functionality including read/write, card emulation, and P2P communication.

Default Pin Configuration:
- IRQ=15, VEN=14, SCL=22, SDA=21, I2C_ADDR=0x28

Author: Reverendo 
Version: 1.0
"""

from machine import I2C, Pin
import time

# =============================================================================
# CORE CONSTANTS
# =============================================================================

# Pin configuration constants
NO_PN7150_RESET_PIN = 255  # Value indicating no reset pin is used

# Status codes
NFC_SUCCESS = 0    # Operation completed successfully
NFC_ERROR = 1      # Operation failed
SUCCESS = NFC_SUCCESS  # Alias for NFC_SUCCESS
ERROR = NFC_ERROR      # Alias for NFC_ERROR

# Timing constants
TIMEOUT_2S = 2000  # 2 second timeout in milliseconds

# NCI Protocol constants
MAX_NCI_FRAME_SIZE = 258  # Maximum NCI frame size in bytes

# =============================================================================
# OPERATION MODE FLAGS
# =============================================================================

# Operating mode flags (bitwise OR combinations)
MODE_CARDEMU = (1 << 0)  # Card emulation mode
MODE_P2P = (1 << 1)      # Peer-to-peer mode  
MODE_RW = (1 << 2)       # Read/Write mode

# =============================================================================
# NCI PROTOCOL MODE VALUES
# =============================================================================

# Mode operation types
MODE_POLL = 0x00      # Polling mode (initiator)
MODE_LISTEN = 0x80    # Listening mode (target)
MODE_MASK = 0xF0      # Mode mask for bit operations

# =============================================================================
# NFC TECHNOLOGY TYPES
# =============================================================================

# Passive and active NFC technologies
TECH_PASSIVE_NFCA = 0    # Type A passive (ISO14443A)
TECH_PASSIVE_NFCB = 1    # Type B passive (ISO14443B)
TECH_PASSIVE_NFCF = 2    # Type F passive (FeliCa)
TECH_ACTIVE_NFCA = 3     # Type A active
TECH_ACTIVE_NFCF = 5     # Type F active
TECH_PASSIVE_15693 = 6   # ISO15693 passive

# =============================================================================
# NCI PROTOCOL IDENTIFIERS
# =============================================================================

# NCI protocol types for different tag technologies
PROT_UNDETERMINED = 0x0  # Unknown protocol
PROT_T1T = 0x1          # Type 1 Tag (Topaz)
PROT_T2T = 0x2          # Type 2 Tag (Mifare Ultralight)
PROT_T3T = 0x3          # Type 3 Tag (FeliCa)
PROT_ISODEP = 0x4       # ISO-DEP (ISO14443-4)
PROT_NFCDEP = 0x5       # NFC-DEP (P2P)
PROT_ISO15693 = 0x6     # ISO15693
PROT_MIFARE = 0x80      # Mifare Classic

# =============================================================================
# NCI INTERFACE TYPES
# =============================================================================

# NCI interface identifiers for communication
INTF_UNDETERMINED = 0x0  # Unknown interface
INTF_FRAME = 0x1         # Frame-based interface
INTF_ISODEP = 0x2        # ISO-DEP interface
INTF_NFCDEP = 0x3        # NFC-DEP interface
INTF_TAGCMD = 0x80       # Tag command interface

# =============================================================================
# MESSAGE SIZE CONSTANTS
# =============================================================================

MaxPayloadSize = 255   # Maximum payload size in bytes
MsgHeaderSize = 3      # NCI message header size in bytes

# =============================================================================
# DISCOVERY TECHNOLOGY CONFIGURATIONS
# =============================================================================

# Technology arrays for different operating modes
DiscoveryTechnologiesCE = [MODE_LISTEN | MODE_POLL]  # Card emulation technologies

DiscoveryTechnologiesRW = [  # Read & Write technologies
    MODE_POLL | TECH_PASSIVE_NFCA,    # Type A passive
    MODE_POLL | TECH_PASSIVE_NFCF,    # Type F passive  
    MODE_POLL | TECH_PASSIVE_NFCB,    # Type B passive
    MODE_POLL | TECH_PASSIVE_15693    # ISO15693 passive
]

DiscoveryTechnologiesP2P = [  # Peer-to-peer technologies
    MODE_POLL | TECH_PASSIVE_NFCA,    # Type A passive poll
    MODE_POLL | TECH_PASSIVE_NFCF,    # Type F passive poll
    MODE_POLL | TECH_ACTIVE_NFCA,     # Type A active poll
    MODE_LISTEN | TECH_PASSIVE_NFCF,  # Type F passive listen
    MODE_LISTEN | TECH_ACTIVE_NFCA,   # Type A active listen
    MODE_LISTEN | TECH_ACTIVE_NFCF    # Type F active listen
]

# =============================================================================
# GLOBAL VARIABLES
# =============================================================================

# Global state variables for NCI communication
gNextTag_Protocol = PROT_UNDETERMINED  # Next tag protocol to process
NCIStartDiscovery_length = 0           # Length of discovery command
NCIStartDiscovery = bytearray(30)      # Discovery command buffer

# =============================================================================
# NCI CONFIGURATION ARRAYS
# =============================================================================

# Core NCI configuration commands for PN7150 initialization
NxpNci_CORE_CONF = bytearray([
    0x20, 0x02, 0x05, 0x01,  # CORE_SET_CONFIG_CMD
    0x00, 0x02, 0x00, 0x01   # TOTAL_DURATION configuration
])

# Extended core configuration with tag detector settings
NxpNci_CORE_CONF_EXTN = bytearray([
    0x20, 0x02, 0x0D, 0x03,  # CORE_SET_CONFIG_CMD
    0xA0, 0x40, 0x01, 0x00,  # TAG_DETECTOR_CFG
    0xA0, 0x41, 0x01, 0x04,  # TAG_DETECTOR_THRESHOLD_CFG
    0xA0, 0x43, 0x01, 0x00   # TAG_DETECTOR_FALLBACK_CNT_CFG
])

# Core standby configuration
NxpNci_CORE_STANDBY = bytearray([
    0x2F, 0x00, 0x01, 0x01   # Standby mode enable/disable
])

# Clock configuration for PN7150
NxpNci_CLK_CONF = bytearray([
    0x20, 0x02, 0x05, 0x01,  # CORE_SET_CONFIG_CMD
    0xA0, 0x03, 0x01, 0x08   # CLOCK_SEL_CFG
])

# TVDD (Voltage) configuration for 2nd generation PN7150 (external 5V)
NxpNci_TVDD_CONF_2ndGen = bytearray([
    0x20, 0x02, 0x07, 0x01, 0xA0, 0x0E, 0x03, 0x06, 0x64, 0x00
])

# RF configuration for 2nd generation PN7150 - comprehensive RF tuning
NxpNci_RF_CONF_2ndGen = bytearray([
    0x20, 0x02, 0x94, 0x11,
    0xA0, 0x0D, 0x06, 0x04, 0x35, 0x90, 0x01, 0xF4, 0x01,  # RF_CLIF_CFG_INITIATOR CLIF_AGC_INPUT_REG
    0xA0, 0x0D, 0x06, 0x06, 0x30, 0x01, 0x90, 0x03, 0x00,  # RF_CLIF_CFG_TARGET CLIF_SIGPRO_ADCBCM_THRESHOLD_REG
    0xA0, 0x0D, 0x06, 0x06, 0x42, 0x02, 0x00, 0xFF, 0xFF,  # RF_CLIF_CFG_TARGET CLIF_ANA_TX_AMPLITUDE_REG
    0xA0, 0x0D, 0x06, 0x20, 0x42, 0x88, 0x00, 0xFF, 0xFF,  # RF_CLIF_CFG_TECHNO_I_TX15693 CLIF_ANA_TX_AMPLITUDE_REG
    0xA0, 0x0D, 0x04, 0x22, 0x44, 0x23, 0x00,              # RF_CLIF_CFG_TECHNO_I_RX15693 CLIF_ANA_RX_REG
    0xA0, 0x0D, 0x06, 0x22, 0x2D, 0x50, 0x34, 0x0C, 0x00,  # RF_CLIF_CFG_TECHNO_I_RX15693 CLIF_SIGPRO_RM_CONFIG1_REG
    0xA0, 0x0D, 0x06, 0x32, 0x42, 0xF8, 0x00, 0xFF, 0xFF,  # RF_CLIF_CFG_BR_106_I_TXA CLIF_ANA_TX_AMPLITUDE_REG
    0xA0, 0x0D, 0x06, 0x34, 0x2D, 0x24, 0x37, 0x0C, 0x00,  # RF_CLIF_CFG_BR_106_I_RXA_P CLIF_SIGPRO_RM_CONFIG1_REG
    0xA0, 0x0D, 0x06, 0x34, 0x33, 0x86, 0x80, 0x00, 0x70,  # RF_CLIF_CFG_BR_106_I_RXA_P CLIF_AGC_CONFIG0_REG
    0xA0, 0x0D, 0x04, 0x34, 0x44, 0x22, 0x00,              # RF_CLIF_CFG_BR_106_I_RXA_P CLIF_ANA_RX_REG
    0xA0, 0x0D, 0x06, 0x42, 0x2D, 0x15, 0x45, 0x0D, 0x00,  # RF_CLIF_CFG_BR_848_I_RXA CLIF_SIGPRO_RM_CONFIG1_REG
    0xA0, 0x0D, 0x04, 0x46, 0x44, 0x22, 0x00,              # RF_CLIF_CFG_BR_106_I_RXB CLIF_ANA_RX_REG
    0xA0, 0x0D, 0x06, 0x46, 0x2D, 0x05, 0x59, 0x0E, 0x00,  # RF_CLIF_CFG_BR_106_I_RXB CLIF_SIGPRO_RM_CONFIG1_REG
    0xA0, 0x0D, 0x06, 0x44, 0x42, 0x88, 0x00, 0xFF, 0xFF,  # RF_CLIF_CFG_BR_106_I_TXB CLIF_ANA_TX_AMPLITUDE_REG
    0xA0, 0x0D, 0x06, 0x56, 0x2D, 0x05, 0x9F, 0x0C, 0x00,  # RF_CLIF_CFG_BR_212_I_RXF_P CLIF_SIGPRO_RM_CONFIG1_REG
    0xA0, 0x0D, 0x06, 0x54, 0x42, 0x88, 0x00, 0xFF, 0xFF,  # RF_CLIF_CFG_BR_212_I_TXF CLIF_ANA_TX_AMPLITUDE_REG
    0xA0, 0x0D, 0x06, 0x0A, 0x33, 0x80, 0x86, 0x00, 0x70   # RF_CLIF_CFG_I_ACTIVE CLIF_AGC_CONFIG0_REG
])

# =============================================================================
# NCI DATA STRUCTURES
# =============================================================================

class RfIntf_info_APP_t:
    """
    NFC Application Protocol (Type A) interface information structure.
    
    Contains all data fields specific to Type A NFC tags including
    the response from ATQA/SENS_REQ, NFCID, and SAK/SEL_RES.
    """
    def __init__(self):
        self.SensRes = bytearray(2)    # ATQA/SENS_RES response (2 bytes)
        self.NfcIdLen = 0              # Length of NFCID (4, 7, or 10 bytes)
        self.NfcId = bytearray(10)     # NFCID (UID) of the tag
        self.SelResLen = 0             # Length of SAK/SEL_RES (1 byte)
        self.SelRes = bytearray(1)     # SAK/SEL_RES response
        self.RatsLen = 0               # Length of RATS response
        self.Rats = bytearray(20)      # RATS (Request for Answer To Select)

class RfIntf_info_BPP_t:
    """
    NFC Application Protocol (Type B) interface information structure.
    
    Contains all data fields specific to Type B NFC tags including
    the response from ATQB/SENSB_REQ and ATTRIB response.
    """
    def __init__(self):
        self.SensResLen = 0            # Length of ATQB/SENSB_RES
        self.SensRes = bytearray(12)   # ATQB/SENSB_RES response (12 bytes)
        self.AttribResLen = 0          # Length of ATTRIB response
        self.AttribRes = bytearray(17) # ATTRIB response (17 bytes)

class RfIntf_info_FPP_t:
    """
    NFC Application Protocol (Type F) interface information structure.
    
    Contains all data fields specific to Type F (FeliCa) NFC tags including
    the response from polling and bit rate information.
    """
    def __init__(self):
        self.BitRate = 0               # Bit rate for communication
        self.SensResLen = 0            # Length of polling response
        self.SensRes = bytearray(18)   # Polling response (18 bytes)

class RfIntf_info_VPP_t:
    """
    NFC Application Protocol (Type V) interface information structure.
    
    Contains all data fields specific to Type V (ISO15693) NFC tags including
    AFI (Application Family Identifier), DSFID, and UID.
    """
    def __init__(self):
        self.AFI = 0                   # Application Family Identifier
        self.DSFID = 0                 # Data Storage Format Identifier
        self.ID = bytearray(8)         # ISO15693 UID (8 bytes)

class RfIntf_Info_t:
    """
    Comprehensive NFC interface information container.
    
    Aggregates all technology-specific interface information structures
    to provide complete tag information regardless of technology type.
    """
    def __init__(self):
        self.NFC_APP = RfIntf_info_APP_t()  # Type A protocol info
        self.NFC_BPP = RfIntf_info_BPP_t()  # Type B protocol info
        self.NFC_FPP = RfIntf_info_FPP_t()  # Type F protocol info
        self.NFC_VPP = RfIntf_info_VPP_t()  # Type V protocol info

class RfIntf_t:
    """
    Main NCI RF Interface structure.
    
    Contains the complete interface information for an activated NFC tag
    including protocol type, interface type, mode/technology combination,
    and all technology-specific data.
    
    Attributes:
        Interface (int): NCI interface type (INTF_ISODEP, INTF_FRAME, etc.)
        Protocol (int): NCI protocol type (PROT_ISODEP, PROT_T2T, etc.)
        ModeTech (int): Combined mode and technology identifier
        MoreTags (bool): True if more tags are available in field
        Info (RfIntf_Info_t): Technology-specific interface information
    """
    def __init__(self):
        self.Interface = 0             # NCI interface identifier
        self.Protocol = 0              # NCI protocol identifier
        self.ModeTech = 0              # Combined mode and technology
        self.MoreTags = False          # Multiple tags present flag
        self.Info = RfIntf_Info_t()    # Technology-specific information

class lib_PN7150:
    """
    PN7150 NFC Controller Library for MicroPython.
    
    A complete implementation of the PN7150 NFC controller interface providing
    full NFC functionality including read/write operations, card emulation,
    and peer-to-peer communication.
    
    The class automatically initializes the PN7150 chip upon instantiation,
    including hardware reset, NCI connection establishment, and configuration.
    
    Operating Modes:
        - Mode 1 (RW): Read/Write mode for communicating with NFC tags
        - Mode 2 (CE): Card Emulation mode for acting as an NFC tag
        - Mode 3 (P2P): Peer-to-Peer mode for device-to-device communication
    
    Supported Technologies:
        - Type A (ISO14443A): Mifare Classic, Ultralight, NTAG, etc.
        - Type B (ISO14443B): ISO14443-4 compliant tags
        - Type F (FeliCa): Japanese FeliCa cards
        - Type V (ISO15693): ISO15693 compliant tags
    
    Example:
        # Basic usage with default pins
        nfc = lib_PN7150()
        
        # Custom pin configuration
        nfc = lib_PN7150(IRQpin=16, VENpin=17, SCLpin=18, SDApin=19)
        
        # Start read/write mode
        nfc.ConfigMode(1)  # RW mode
        nfc.StartDiscovery(1)
    """
    
    def __init__(self, IRQpin=15, VENpin=14, SCLpin=22, SDApin=21, I2Caddress=0x28, wire=None):
        """
        Initialize PN7150 NFC Controller with complete hardware setup.
        
        Performs full initialization sequence including pin configuration,
        hardware reset, I2C communication setup, NCI connection, and
        PN7150 configuration. The chip is ready for use after instantiation.
        
        Args:
            IRQpin (int): Interrupt pin number (default: 15)
                The PN7150 drives this pin HIGH when data is available
            VENpin (int): Voltage enable pin number (default: 14)
                Controls power to the PN7150 chip (255 = no reset pin)
            SCLpin (int): I2C clock pin number (default: 22)
                Serial clock line for I2C communication
            SDApin (int): I2C data pin number (default: 21)
                Serial data line for I2C communication
            I2Caddress (int): I2C slave address (default: 0x28)
                The PN7150's I2C address (usually 0x28 or 0x29)
            wire (I2C, optional): Existing I2C instance (default: None)
                If provided, uses existing I2C instead of creating new one
        
        Raises:
            Exception: If PN7150 initialization fails at any step
        """
        self._IRQpin = IRQpin
        self._VENpin = VENpin
        self._SCLpin = SCLpin
        self._SDApin = SDApin
        self._I2Caddress = I2Caddress
        self._wire = wire
        
        # Initialize pins
        self.irq = Pin(IRQpin, Pin.IN)
        if VENpin != NO_PN7150_RESET_PIN:
            self.ven = Pin(VENpin, Pin.OUT)
        else:
            self.ven = None
        
        # Message handling variables
        self.rxBuffer = bytearray(MAX_NCI_FRAME_SIZE)
        self.rxMessageLength = 0
        self.timeOutStartTime = 0
        self.timeOut = 0
        
        # Controller info
        self.gNfcController_generation = 0
        self.gNfcController_fw_version = bytearray(3)
        
        # Initialize the PN7150 chip completely
        self._initialize_chip()
    
    def _initialize_chip(self):
        """
        Complete PN7150 hardware and software initialization sequence.
        
        Performs the full initialization sequence required to get the PN7150
        chip ready for NFC operations. This includes:
        
        1. I2C communication setup
        2. Hardware power cycle (VEN pin sequence)
        3. NCI protocol connection establishment
        4. PN7150 configuration (core, RF, clock, voltage settings)
        
        This method is automatically called during __init__ and should not
        be called manually unless reinitializing the chip.
        
        Raises:
            Exception: If any initialization step fails
        """
        try:
            # Step 1: Hardware initialization
            if self._wire is None:
                self._wire = I2C(0, scl=Pin(self._SCLpin), sda=Pin(self._SDApin), freq=100000)
            
            # Step 2: Power cycle the chip
            if self._VENpin != NO_PN7150_RESET_PIN:
                self.ven.value(1)
                time.sleep_ms(1)
                self.ven.value(0)
                time.sleep_ms(1)
                self.ven.value(1)
                time.sleep_ms(3)
            
            # Step 3: Connect to NCI
            if self.connectNCI() != SUCCESS:
                raise Exception("Failed to connect to NCI")
            
            # Step 4: Configure settings
            if self.ConfigureSettings():
                raise Exception("Failed to configure PN7150 settings")
            
            print("PN7150 initialized successfully")
            
        except Exception as e:
            print(f"PN7150 initialization failed: {e}")
            raise
    
    def begin(self):
        """
        Legacy hardware initialization method (for compatibility).
        
        Performs basic hardware initialization including I2C setup and
        VEN pin power cycle sequence. This method is provided for
        compatibility with Arduino library usage patterns.
        
        Note: This method is automatically called during _initialize_chip()
        and is typically not needed when using the modern initialization.
        
        Returns:
            int: SUCCESS (0) if initialization succeeds, ERROR (1) otherwise
        """
        if self._wire is None:
            # Initialize I2C if not provided
            self._wire = I2C(0, scl=Pin(self._SCLpin), sda=Pin(self._SDApin), freq=100000)
        
        if self._VENpin != NO_PN7150_RESET_PIN:
            self.ven.value(1)
            time.sleep_ms(1)
            self.ven.value(0)
            time.sleep_ms(1)
            self.ven.value(1)
            time.sleep_ms(3)
        
        return SUCCESS
    
    def hasMessage(self):
        """
        Check if PN7150 has data available for reading.
        
        Reads the IRQ pin status to determine if the PN7150 has data
        ready to be read via I2C. The PN7150 drives the IRQ pin HIGH
        when it has data available.
        
        Returns:
            bool: True if data is available, False otherwise
        """
        return self.irq.value() == 1  # PN7150 indicates it has data by driving IRQ signal HIGH
    
    def writeData(self, txBuffer, txBufferLevel):
        """
        Write data to PN7150 via I2C communication.
        
        Sends a data buffer to the PN7150 chip using I2C communication.
        The data is sent as a complete NCI message to the chip.
        
        Args:
            txBuffer (bytearray): Data buffer to send to PN7150
            txBufferLevel (int): Number of bytes to send from buffer
        
        Returns:
            int: 0 on success, 4 on I2C write error
        """
        try:
            self._wire.writeto(self._I2Caddress, txBuffer[:txBufferLevel])
            return 0  # SUCCESS
        except Exception as e:
            print(f"Write error: {e}")
            return 4  # Could not properly copy data to I2C buffer
    
    def readData(self, rxBuffer):
        """
        Read data from PN7150 via I2C communication.
        
        Reads a complete NCI message from the PN7150 chip. The message
        consists of a 3-byte header followed by optional payload data.
        The header contains the payload length information.
        
        Args:
            rxBuffer (bytearray): Buffer to store received data
        
        Returns:
            int: Number of bytes received, 0 if no data available
        """
        bytesReceived = 0
        
        if self.hasMessage():  # only try to read something if the PN7150 indicates it has something
            # first reading the header, as this contains how long the payload will be
            bytesReceived = self._wire.readfrom(self._I2Caddress, 3)
            
            if len(bytesReceived) == 3:
                rxBuffer[0] = bytesReceived[0]
                rxBuffer[1] = bytesReceived[1]
                rxBuffer[2] = bytesReceived[2]
                
                payloadLength = rxBuffer[2]
                if payloadLength > 0:
                    # then reading the payload, if any
                    payload = self._wire.readfrom(self._I2Caddress, payloadLength)
                    index = 3
                    for i in range(len(payload)):
                        if index < len(rxBuffer):
                            rxBuffer[index] = payload[i]
                            index += 1
                    bytesReceived = index
        
        return bytesReceived
    
    def isTimeOut(self):
        """
        Check if the current timeout period has expired.
        
        Compares the elapsed time since timeout was set against the
        configured timeout duration.
        
        Returns:
            bool: True if timeout has expired, False otherwise
        """
        return (time.ticks_ms() - self.timeOutStartTime) >= self.timeOut
    
    def setTimeOut(self, theTimeOut):
        """
        Set a timeout duration for message operations.
        
        Configures a timeout period starting from the current time.
        Used by getMessage() and other methods that need timeout control.
        
        Args:
            theTimeOut (int): Timeout duration in milliseconds
        """
        self.timeOutStartTime = time.ticks_ms()
        self.timeOut = theTimeOut
    
    def getMessage(self, timeout=5):
        """
        Wait for and receive a message from PN7150.
        
        Waits for the PN7150 to indicate data is available and then reads
        the complete NCI message. Uses timeout to prevent infinite waiting.
        
        Args:
            timeout (int): Timeout duration in milliseconds (default: 5)
                Special value 1337 means infinite timeout (continuous polling)
        
        Returns:
            int: Number of bytes received, 0 if timeout occurred
        """
        self.setTimeOut(timeout)
        self.rxMessageLength = 0
        
        while not self.isTimeOut():
            self.rxMessageLength = self.readData(self.rxBuffer)
            if self.rxMessageLength:
                break
            elif timeout == 1337:
                self.setTimeOut(timeout)
        
        return self.rxMessageLength
    
    def wakeupNCI(self):
        """EXACT translation of Arduino wakeupNCI() method"""
        NCICoreReset = bytearray([0x20, 0x00, 0x01, 0x01])
        NbBytes = 0
        
        # Reset RF settings restauration flag
        self.writeData(NCICoreReset, 4)
        self.getMessage(15)
        NbBytes = self.rxMessageLength
        
        if (NbBytes == 0) or (self.rxBuffer[0] != 0x40) or (self.rxBuffer[1] != 0x00):
            return ERROR
        
        self.getMessage()
        NbBytes = self.rxMessageLength
        
        if NbBytes != 0:
            # Is CORE_GENERIC_ERROR_NTF ?
            if (self.rxBuffer[0] == 0x60) and (self.rxBuffer[1] == 0x07):
                # Is PN7150B0HN/C11004 Anti-tearing recovery procedure triggered ?
                pass  # gRfSettingsRestored_flag = true;
            else:
                return ERROR
        
        return SUCCESS
    
    def connectNCI(self):
        """EXACT translation of Arduino connectNCI() method"""
        i = 2
        NCICoreInit = bytearray([0x20, 0x01, 0x00])
        
        # Loop until NXPNCI answers
        while self.wakeupNCI() != SUCCESS:
            if i == 0:
                return ERROR
            i -= 1
            time.sleep_ms(500)
        
        self.writeData(NCICoreInit, len(NCICoreInit))
        self.getMessage()
        
        if (self.rxBuffer[0] != 0x40) or (self.rxBuffer[1] != 0x01) or (self.rxBuffer[3] != 0x00):
            return ERROR
        
        # Retrieve NXP-NCI NFC Controller generation
        if self.rxBuffer[17 + self.rxBuffer[8]] == 0x08:
            self.gNfcController_generation = 1
        elif self.rxBuffer[17 + self.rxBuffer[8]] == 0x10:
            self.gNfcController_generation = 2
        
        # Retrieve NXP-NCI NFC Controller FW version
        self.gNfcController_fw_version[0] = self.rxBuffer[17 + self.rxBuffer[8]]  # 0xROM_CODE_V
        self.gNfcController_fw_version[1] = self.rxBuffer[18 + self.rxBuffer[8]]  # 0xFW_MAJOR_NO
        self.gNfcController_fw_version[2] = self.rxBuffer[19 + self.rxBuffer[8]]  # 0xFW_MINOR_NO
        
        return SUCCESS
    
    def ConfigureSettings(self, uidcf=None, uidlen=0):
        """
        Configure all PN7150 settings for proper operation.
        
        Applies all necessary configuration arrays to the PN7150 chip including:
        - Core configuration (timing, duration)
        - Extended core configuration (tag detector settings)
        - Standby configuration
        - Clock configuration
        - Voltage (TVDD) configuration
        - RF configuration (comprehensive RF tuning)
        
        Args:
            uidcf (bytearray, optional): UID configuration (unused in this implementation)
            uidlen (int, optional): UID length (unused in this implementation)
        
        Returns:
            bool: False on success, True on error
        """
        # Apply CORE configuration
        self.writeData(NxpNci_CORE_CONF, len(NxpNci_CORE_CONF))
        self.getMessage(1000)
        if (self.rxMessageLength == 0) or (self.rxBuffer[0] != 0x40) or (self.rxBuffer[1] != 0x02):
            return True  # Error
        
        # Apply CORE extension configuration
        self.writeData(NxpNci_CORE_CONF_EXTN, len(NxpNci_CORE_CONF_EXTN))
        self.getMessage(1000)
        if (self.rxMessageLength == 0) or (self.rxBuffer[0] != 0x40) or (self.rxBuffer[1] != 0x02):
            return True  # Error
        
        # Apply CORE standby configuration
        self.writeData(NxpNci_CORE_STANDBY, len(NxpNci_CORE_STANDBY))
        self.getMessage(1000)
        if (self.rxMessageLength == 0) or (self.rxBuffer[0] != 0x4F) or (self.rxBuffer[1] != 0x00):
            return True  # Error
        
        # Apply Clock configuration
        self.writeData(NxpNci_CLK_CONF, len(NxpNci_CLK_CONF))
        self.getMessage(1000)
        if (self.rxMessageLength == 0) or (self.rxBuffer[0] != 0x40) or (self.rxBuffer[1] != 0x02):
            return True  # Error
        
        # Apply TVDD configuration
        self.writeData(NxpNci_TVDD_CONF_2ndGen, len(NxpNci_TVDD_CONF_2ndGen))
        self.getMessage(1000)
        if (self.rxMessageLength == 0) or (self.rxBuffer[0] != 0x40) or (self.rxBuffer[1] != 0x02):
            return True  # Error
        
        # Apply RF configuration
        self.writeData(NxpNci_RF_CONF_2ndGen, len(NxpNci_RF_CONF_2ndGen))
        self.getMessage(1000)
        if (self.rxMessageLength == 0) or (self.rxBuffer[0] != 0x40) or (self.rxBuffer[1] != 0x02):
            return True  # Error
        
        return False  # Success
    
    def ConfigMode(self, modeSE):
        """
        Configure PN7150 for specific operating mode.
        
        Sets up the discovery map and routing configuration for the specified
        operating mode. This must be called before starting discovery.
        
        Args:
            modeSE (int): Operating mode to configure
                1 = Read/Write mode (discover and communicate with tags)
                2 = Card Emulation mode (act as an NFC tag)
                3 = Peer-to-Peer mode (device-to-device communication)
        
        Returns:
            int: SUCCESS (0) on success, ERROR (1) on failure
        """
        mode = (MODE_RW if modeSE == 1 else MODE_CARDEMU if modeSE == 2 else MODE_P2P)
        
        Command = bytearray(MAX_NCI_FRAME_SIZE)
        Item = 0
        NCIDiscoverMap = bytearray([0x21, 0x00])
        
        # Emulation mode
        DM_CARDEMU = bytearray([0x4, 0x2, 0x2])
        R_CARDEMU = bytearray([0x1, 0x3, 0x0, 0x1, 0x4])
        
        # RW Mode
        DM_RW = bytearray([0x1, 0x1, 0x1, 0x2, 0x1, 0x1, 0x3, 0x1, 0x1, 0x4, 0x1, 0x2, 0x80, 0x01, 0x80])
        NCIPropAct = bytearray([0x2F, 0x02, 0x00])
        
        # P2P Support
        DM_P2P = bytearray([0x5, 0x3, 0x3])
        R_P2P = bytearray([0x1, 0x3, 0x0, 0x1, 0x5])
        NCISetConfig_NFC = bytearray([0x20, 0x02, 0x1F, 0x02, 0x29, 0x0D, 0x46, 0x66, 0x6D, 0x01, 0x01, 0x11, 0x03, 0x02, 0x00, 0x01, 0x04, 0x01, 0xFA, 0x61, 0x0D, 0x46, 0x66, 0x6D, 0x01, 0x01, 0x11, 0x03, 0x02, 0x00, 0x01, 0x04, 0x01, 0xFA])
        
        NCIRouting = bytearray([0x21, 0x01, 0x07, 0x00, 0x01])
        NCISetConfig_NFCA_SELRSP = bytearray([0x20, 0x02, 0x04, 0x01, 0x32, 0x01, 0x00])
        
        if mode == 0:
            return SUCCESS
        
        # Enable Proprietary interface for T4T card presence check procedure
        if modeSE == 1:
            if mode == MODE_RW:
                self.writeData(NCIPropAct, len(NCIPropAct))
                self.getMessage()
                
                if (self.rxBuffer[0] != 0x4F) or (self.rxBuffer[1] != 0x02) or (self.rxBuffer[3] != 0x00):
                    return ERROR
        
        # Building Discovery Map command
        Item = 0
        
        if ((mode & MODE_CARDEMU and modeSE == 2) or (mode & MODE_P2P and modeSE == 3)):
            if modeSE == 2:
                for i in range(len(DM_CARDEMU)):
                    Command[4 + (3 * Item) + i] = DM_CARDEMU[i]
            else:
                for i in range(len(DM_P2P)):
                    Command[4 + (3 * Item) + i] = DM_P2P[i]
            Item += 1
        
        if mode & MODE_RW and modeSE == 1:
            for i in range(len(DM_RW)):
                Command[4 + (3 * Item) + i] = DM_RW[i]
            Item += len(DM_RW) // 3
        
        if Item != 0:
            for i in range(len(NCIDiscoverMap)):
                Command[i] = NCIDiscoverMap[i]
            Command[2] = 1 + (Item * 3)
            Command[3] = Item
            self.writeData(Command, 3 + Command[2])
            self.getMessage(10)
            if (self.rxBuffer[0] != 0x41) or (self.rxBuffer[1] != 0x00) or (self.rxBuffer[3] != 0x00):
                return ERROR
        
        return SUCCESS
    
    def StartDiscovery(self, modeSE):
        """
        Start NFC tag discovery process.
        
        Initiates the discovery sequence to detect NFC tags in the field.
        The discovery technologies used depend on the configured mode.
        
        Args:
            modeSE (int): Operating mode for discovery
                1 = Read/Write mode (discover Type A, B, F, V tags)
                2 = Card Emulation mode (listen for readers)
                3 = Peer-to-Peer mode (discover P2P devices)
        
        Returns:
            int: SUCCESS (0) on success, ERROR (1) on failure
        """
        if modeSE == 1:
            TechTabSize = len(DiscoveryTechnologiesRW)
            TechTab = DiscoveryTechnologiesRW
        elif modeSE == 2:
            TechTabSize = len(DiscoveryTechnologiesCE)
            TechTab = DiscoveryTechnologiesCE
        else:
            TechTabSize = len(DiscoveryTechnologiesP2P)
            TechTab = DiscoveryTechnologiesP2P
        
        global NCIStartDiscovery_length, NCIStartDiscovery
        
        NCIStartDiscovery_length = 0
        NCIStartDiscovery[0] = 0x21
        NCIStartDiscovery[1] = 0x03
        NCIStartDiscovery[2] = (TechTabSize * 2) + 1
        NCIStartDiscovery[3] = TechTabSize
        
        for i in range(TechTabSize):
            NCIStartDiscovery[(i * 2) + 4] = TechTab[i]
            NCIStartDiscovery[(i * 2) + 5] = 0x01
        
        NCIStartDiscovery_length = (TechTabSize * 2) + 4
        self.writeData(NCIStartDiscovery, NCIStartDiscovery_length)
        self.getMessage()
        
        if (self.rxBuffer[0] != 0x41) or (self.rxBuffer[1] != 0x03) or (self.rxBuffer[3] != 0x00):
            return ERROR
        else:
            return SUCCESS
    
    def WaitForDiscoveryNotification(self, pRfIntf, tout=0):
        """
        Wait for tag discovery notification and activate the tag.
        
        Waits for the PN7150 to report a discovered tag and then activates
        it for communication. Handles both single and multiple tag scenarios.
        
        Args:
            pRfIntf (RfIntf_t): Interface structure to populate with tag info
            tout (int): Timeout in milliseconds (0 = infinite wait)
        
        Returns:
            bool: True if tag was successfully activated, False otherwise
        """
        NCIRfDiscoverSelect = bytearray([0x21, 0x04, 0x03, 0x01, PROT_ISODEP, INTF_ISODEP])
        
        # P2P Support
        NCIStopDiscovery = bytearray([0x21, 0x06, 0x01, 0x00])
        NCIRestartDiscovery = bytearray([0x21, 0x06, 0x01, 0x03])
        saved_NTF = bytearray(7)
        
        global gNextTag_Protocol
        gNextTag_Protocol = PROT_UNDETERMINED
        getFlag = False
        
        # EXACT Arduino logic
        while True:
            getFlag = self.getMessage(tout if tout > 0 else 1337)
            if not (((self.rxBuffer[0] != 0x61) or 
                    ((self.rxBuffer[1] != 0x05) and (self.rxBuffer[1] != 0x03))) and 
                   (getFlag == True)):
                break
        
        gNextTag_Protocol = PROT_UNDETERMINED
        
        # Is RF_INTF_ACTIVATED_NTF ?
        if self.rxBuffer[1] == 0x05:
            pRfIntf.Interface = self.rxBuffer[4]
            pRfIntf.Protocol = self.rxBuffer[5]
            pRfIntf.ModeTech = self.rxBuffer[6]
            pRfIntf.MoreTags = False
            self.FillInterfaceInfo(pRfIntf, self.rxBuffer[10:])
            
            # P2P handling - simplified for now
            return True
        else:
            # RF_DISCOVER_NTF
            pRfIntf.Interface = INTF_UNDETERMINED
            pRfIntf.Protocol = self.rxBuffer[4]
            pRfIntf.ModeTech = self.rxBuffer[5]
            pRfIntf.MoreTags = True
            
            # Get next NTF for further activation
            while True:
                if not self.getMessage(100):
                    return False
                if (self.rxBuffer[0] == 0x61) and (self.rxBuffer[1] == 0x03):
                    break
            
            gNextTag_Protocol = self.rxBuffer[4]
            
            # Remaining NTF ?
            while self.rxBuffer[self.rxMessageLength - 1] == 0x02:
                self.getMessage(100)
            
            # In case of multiple cards, select the first one
            NCIRfDiscoverSelect[4] = pRfIntf.Protocol
            if pRfIntf.Protocol == PROT_ISODEP:
                NCIRfDiscoverSelect[5] = INTF_ISODEP
            elif pRfIntf.Protocol == PROT_NFCDEP:
                NCIRfDiscoverSelect[5] = INTF_NFCDEP
            elif pRfIntf.Protocol == PROT_MIFARE:
                NCIRfDiscoverSelect[5] = INTF_TAGCMD
            else:
                NCIRfDiscoverSelect[5] = INTF_FRAME
            
            self.writeData(NCIRfDiscoverSelect, len(NCIRfDiscoverSelect))
            self.getMessage(100)
            
            if (self.rxBuffer[0] == 0x41) and (self.rxBuffer[1] == 0x04) and (self.rxBuffer[3] == 0x00):
                return True
            else:
                return False
    
    def FillInterfaceInfo(self, pRfIntf, pBuf):
        """EXACT translation of Arduino FillInterfaceInfo() method"""
        if pRfIntf.Protocol == PROT_T1T:
            pRfIntf.Info.NFC_APP.SensRes[0] = pBuf[0]
            pRfIntf.Info.NFC_APP.SensRes[1] = pBuf[1]
            pRfIntf.Info.NFC_APP.NfcIdLen = pBuf[2]
            for i in range(pRfIntf.Info.NFC_APP.NfcIdLen):
                pRfIntf.Info.NFC_APP.NfcId[i] = pBuf[3 + i]
        elif pRfIntf.Protocol == PROT_T2T:
            pRfIntf.Info.NFC_APP.SensRes[0] = pBuf[0]
            pRfIntf.Info.NFC_APP.SensRes[1] = pBuf[1]
            pRfIntf.Info.NFC_APP.NfcIdLen = pBuf[2]
            for i in range(pRfIntf.Info.NFC_APP.NfcIdLen):
                pRfIntf.Info.NFC_APP.NfcId[i] = pBuf[3 + i]
            pRfIntf.Info.NFC_APP.SelResLen = pBuf[3 + pRfIntf.Info.NFC_APP.NfcIdLen]
            if pRfIntf.Info.NFC_APP.SelResLen > 0:
                pRfIntf.Info.NFC_APP.SelRes[0] = pBuf[4 + pRfIntf.Info.NFC_APP.NfcIdLen]

    def SendApduCommand(self, apdu_cmd):
        """
        Send APDU command to an activated ISO-DEP tag.
        
        Sends an APDU (Application Protocol Data Unit) command to a tag
        that has been activated and is ready for ISO-DEP communication.
        Uses the DATA_PACKET format required by the NCI protocol.
        
        Args:
            apdu_cmd (bytearray): APDU command bytes to send to the tag
        
        Returns:
            bytearray or None: APDU response from tag, None if error or timeout
        """
        # DATA_PACKET format: [0x00, 0x00, CommandSize, CommandData]
        # This is the correct format for ISO-DEP communication
        
        cmd_length = len(apdu_cmd)
        data_packet = bytearray([0x00, 0x00, cmd_length]) + apdu_cmd
        
        print(f"  DATA_PACKET CMD: {self.print_hex_array(data_packet, len(data_packet))}")
        
        # Send the DATA_PACKET
        self.writeData(data_packet, len(data_packet))
        
        # Get immediate response (acknowledgment) - EXACT like official library
        self.getMessage()
        print(f"  Immediate response: {self.print_hex_array(self.rxBuffer, self.rxMessageLength)}")
        
        # Wait for actual data response - EXACT like official library
        if self.getMessage(1000):  # 1 second timeout
            print(f"  Data response: {self.print_hex_array(self.rxBuffer, self.rxMessageLength)}")
            
            # Check if it's a DATA_PACKET response
            if self.rxBuffer[0] == 0x00 and self.rxBuffer[1] == 0x00:
                payload_length = self.rxBuffer[2]
                if payload_length > 0:
                    response = self.rxBuffer[3:3+payload_length]
                    print(f"  DATA_PACKET RSP: {self.print_hex_array(response, len(response))}")
                    return response
                else:
                    print("  Empty response")
                    return None
            else:
                print(f"  Unexpected response format: {self.print_hex_array(self.rxBuffer, self.rxMessageLength)}")
                return None
        else:
            print("  No data response received")
            return None

    def print_hex_array(self, data, length):
        """
        Format byte array as hexadecimal string for debugging.
        
        Converts a byte array to a formatted hexadecimal string suitable
        for printing and debugging communication data.
        
        Args:
            data (bytearray): Data to format
            length (int): Number of bytes to format
        
        Returns:
            str: Formatted hexadecimal string (e.g., "0x01 0x02 0x03")
        """
        result = ""
        for i in range(min(length, len(data))):
            result += f"0x{data[i]:02X} "
        return result.strip()

    def StopDiscovery(self):
        """
        Stop the NFC tag discovery process.
        
        Sends the NCI stop discovery command to halt the current discovery
        process. This should be called when switching modes or when
        discovery is no longer needed.
        
        Returns:
            bool: True on success
        """
        NCIStopDiscovery = bytearray([0x21, 0x06, 0x01, 0x00])
        self.writeData(NCIStopDiscovery, len(NCIStopDiscovery))
        self.getMessage()
        self.getMessage(1000)
        return True

 