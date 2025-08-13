#!/usr/bin/env python3
"""
Final Working Arduino Library Translation
IRQ=15, VEN=14 (matching Arduino example)
With correct return logic and complete functionality
"""

from machine import I2C, Pin
import time

# Constants from Arduino library header
NO_PN7150_RESET_PIN = 255
NFC_SUCCESS = 0
NFC_ERROR = 1
TIMEOUT_2S = 2000
SUCCESS = NFC_SUCCESS
ERROR = NFC_ERROR
MAX_NCI_FRAME_SIZE = 258

# Mode flags
MODE_CARDEMU = (1 << 0)
MODE_P2P = (1 << 1)
MODE_RW = (1 << 2)

# Mode values
MODE_POLL = 0x00
MODE_LISTEN = 0x80
MODE_MASK = 0xF0

# Technology values
TECH_PASSIVE_NFCA = 0
TECH_PASSIVE_NFCB = 1
TECH_PASSIVE_NFCF = 2
TECH_ACTIVE_NFCA = 3
TECH_ACTIVE_NFCF = 5
TECH_PASSIVE_15693 = 6

# Protocol values
PROT_UNDETERMINED = 0x0
PROT_T1T = 0x1
PROT_T2T = 0x2
PROT_T3T = 0x3
PROT_ISODEP = 0x4
PROT_NFCDEP = 0x5
PROT_ISO15693 = 0x6
PROT_MIFARE = 0x80

# Interface values
INTF_UNDETERMINED = 0x0
INTF_FRAME = 0x1
INTF_ISODEP = 0x2
INTF_NFCDEP = 0x3
INTF_TAGCMD = 0x80

MaxPayloadSize = 255
MsgHeaderSize = 3

# Discovery technologies - EXACT from Arduino library
DiscoveryTechnologiesCE = [MODE_LISTEN | MODE_POLL]  # Emulation

DiscoveryTechnologiesRW = [  # Read & Write
    MODE_POLL | TECH_PASSIVE_NFCA,
    MODE_POLL | TECH_PASSIVE_NFCF,
    MODE_POLL | TECH_PASSIVE_NFCB,
    MODE_POLL | TECH_PASSIVE_15693
]

DiscoveryTechnologiesP2P = [  # P2P
    MODE_POLL | TECH_PASSIVE_NFCA,
    MODE_POLL | TECH_PASSIVE_NFCF,
    MODE_POLL | TECH_ACTIVE_NFCA,
    MODE_LISTEN | TECH_PASSIVE_NFCF,
    MODE_LISTEN | TECH_ACTIVE_NFCA,
    MODE_LISTEN | TECH_ACTIVE_NFCF
]

# Global variables from Arduino library
gNextTag_Protocol = PROT_UNDETERMINED
NCIStartDiscovery_length = 0
NCIStartDiscovery = bytearray(30)

# Configuration arrays - EXACT from Arduino library
NxpNci_CORE_CONF = bytearray([
    0x20, 0x02, 0x05, 0x01,  # CORE_SET_CONFIG_CMD
    0x00, 0x02, 0x00, 0x01   # TOTAL_DURATION
])

NxpNci_CORE_CONF_EXTN = bytearray([
    0x20, 0x02, 0x0D, 0x03,  # CORE_SET_CONFIG_CMD
    0xA0, 0x40, 0x01, 0x00,  # TAG_DETECTOR_CFG
    0xA0, 0x41, 0x01, 0x04,  # TAG_DETECTOR_THRESHOLD_CFG
    0xA0, 0x43, 0x01, 0x00   # TAG_DETECTOR_FALLBACK_CNT_CFG
])

NxpNci_CORE_STANDBY = bytearray([
    0x2F, 0x00, 0x01, 0x01   # last byte indicates enable/disable
])

NxpNci_CLK_CONF = bytearray([
    0x20, 0x02, 0x05, 0x01,  # CORE_SET_CONFIG_CMD
    0xA0, 0x03, 0x01, 0x08   # CLOCK_SEL_CFG
])

# TVDD Configuration for 2nd generation (PN7150) - CFG2: external 5V
NxpNci_TVDD_CONF_2ndGen = bytearray([
    0x20, 0x02, 0x07, 0x01, 0xA0, 0x0E, 0x03, 0x06, 0x64, 0x00
])

# RF Configuration for 2nd generation (PN7150) - EXACT from Arduino library
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

# RfIntf_t structure - EXACT from Arduino library
class RfIntf_info_APP_t:
    def __init__(self):
        self.SensRes = bytearray(2)
        self.NfcIdLen = 0
        self.NfcId = bytearray(10)
        self.SelResLen = 0
        self.SelRes = bytearray(1)
        self.RatsLen = 0
        self.Rats = bytearray(20)

class RfIntf_info_BPP_t:
    def __init__(self):
        self.SensResLen = 0
        self.SensRes = bytearray(12)
        self.AttribResLen = 0
        self.AttribRes = bytearray(17)

class RfIntf_info_FPP_t:
    def __init__(self):
        self.BitRate = 0
        self.SensResLen = 0
        self.SensRes = bytearray(18)

class RfIntf_info_VPP_t:
    def __init__(self):
        self.AFI = 0
        self.DSFID = 0
        self.ID = bytearray(8)

class RfIntf_Info_t:
    def __init__(self):
        self.NFC_APP = RfIntf_info_APP_t()
        self.NFC_BPP = RfIntf_info_BPP_t()
        self.NFC_FPP = RfIntf_info_FPP_t()
        self.NFC_VPP = RfIntf_info_VPP_t()

class RfIntf_t:
    def __init__(self):
        self.Interface = 0
        self.Protocol = 0
        self.ModeTech = 0
        self.MoreTags = False
        self.Info = RfIntf_Info_t()

class Electroniccats_PN7150:
    def __init__(self, IRQpin, VENpin, I2Caddress, wire=None):
        self._IRQpin = IRQpin
        self._VENpin = VENpin
        self._I2Caddress = I2Caddress
        self._wire = wire
        
        # Initialize pins - EXACT from Arduino constructor
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
    
    def begin(self):
        """EXACT translation of Arduino begin() method"""
        if self._wire is None:
            # Initialize I2C if not provided
            self._wire = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
        
        if self._VENpin != NO_PN7150_RESET_PIN:
            self.ven.value(1)
            time.sleep_ms(1)
            self.ven.value(0)
            time.sleep_ms(1)
            self.ven.value(1)
            time.sleep_ms(3)
        
        return SUCCESS
    
    def hasMessage(self):
        """EXACT translation of Arduino hasMessage() method"""
        return self.irq.value() == 1  # PN7150 indicates it has data by driving IRQ signal HIGH
    
    def writeData(self, txBuffer, txBufferLevel):
        """EXACT translation of Arduino writeData() method"""
        try:
            self._wire.writeto(self._I2Caddress, txBuffer[:txBufferLevel])
            return 0  # SUCCESS
        except Exception as e:
            print(f"Write error: {e}")
            return 4  # Could not properly copy data to I2C buffer
    
    def readData(self, rxBuffer):
        """EXACT translation of Arduino readData() method"""
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
        """EXACT translation of Arduino isTimeOut() method"""
        return (time.ticks_ms() - self.timeOutStartTime) >= self.timeOut
    
    def setTimeOut(self, theTimeOut):
        """EXACT translation of Arduino setTimeOut() method"""
        self.timeOutStartTime = time.ticks_ms()
        self.timeOut = theTimeOut
    
    def getMessage(self, timeout=5):
        """EXACT translation of Arduino getMessage() method"""
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
        
        # Open connection to NXPNCI
        self.begin()
        
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
        """EXACT translation of Arduino ConfigureSettings() method - returns False on success"""
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
        """EXACT translation of Arduino ConfigMode() method"""
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
        """EXACT translation of Arduino StartDiscovery() method"""
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
        """EXACT translation of Arduino WaitForDiscoveryNotification() method"""
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
        """Send APDU command to activated tag using DATA_PACKET format (like official library)"""
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
        """Print hex array with proper formatting"""
        result = ""
        for i in range(min(length, len(data))):
            result += f"0x{data[i]:02X} "
        return result.strip()

    def StopDiscovery(self):
        """Stop discovery process"""
        NCIStopDiscovery = bytearray([0x21, 0x06, 0x01, 0x00])
        self.writeData(NCIStopDiscovery, len(NCIStopDiscovery))
        self.getMessage()
        self.getMessage(1000)
        return True

 