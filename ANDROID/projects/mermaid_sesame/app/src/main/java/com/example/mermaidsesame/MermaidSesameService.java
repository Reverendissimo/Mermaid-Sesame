package com.example.mermaidsesame;

import android.content.SharedPreferences;
import android.nfc.cardemulation.HostApduService;
import android.os.Bundle;
import android.util.Log;
import android.content.Intent;
import android.content.Context;

import java.util.Arrays;

public class MermaidSesameService extends HostApduService {
    private static final String TAG = "MermaidSesameService";
    private static final String PREFS_NAME = "MermaidSesamePrefs";
    private static final String KEY_RESPONSE_DATA = "response_data";
    
    // AID for our service - F1726576406873
    private static final String AID = "F1726576406873";
    private static final byte[] AID_BYTES = hexStringToByteArray(AID);
    
    // APDU commands
    private static final byte[] SELECT_APDU_HEADER = {
        (byte) 0x00, // CLA
        (byte) 0xA4, // INS
        (byte) 0x04, // P1
        (byte) 0x00  // P2
    };
    
    // Success response
    private static final byte[] SUCCESS_SW = {(byte) 0x90, (byte) 0x00};
    
    // Debug counters
    private static int serviceStartCount = 0;
    private static int serviceStopCount = 0;
    private static int apduReceivedCount = 0;
    private static int aidSelectedCount = 0;
    
    @Override
    public void onCreate() {
        super.onCreate();
        serviceStartCount++;
        Log.i(TAG, "=== HCE SERVICE CREATED ===");
        Log.i(TAG, "Service start count: " + serviceStartCount);
        Log.i(TAG, "Service registered AID: " + AID);
        Log.i(TAG, "Service AID bytes: " + bytesToHex(AID_BYTES));
        
        // Send broadcast to update UI
        sendDebugBroadcast("HCE_SERVICE_CREATED", "Service created successfully");
    }
    
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Log.i(TAG, "=== HCE SERVICE STARTED ===");
        Log.i(TAG, "Intent: " + (intent != null ? intent.toString() : "null"));
        Log.i(TAG, "Flags: " + flags);
        Log.i(TAG, "Start ID: " + startId);
        
        sendDebugBroadcast("HCE_SERVICE_STARTED", "Service started with ID: " + startId);
        return START_STICKY; // Keep service running
    }
    
    @Override
    public void onDestroy() {
        super.onDestroy();
        serviceStopCount++;
        Log.i(TAG, "=== HCE SERVICE DESTROYED ===");
        Log.i(TAG, "Service stop count: " + serviceStopCount);
        Log.i(TAG, "Total APDUs received: " + apduReceivedCount);
        Log.i(TAG, "Total AID selections: " + aidSelectedCount);
        
        sendDebugBroadcast("HCE_SERVICE_DESTROYED", "Service destroyed");
    }
    
    @Override
    public byte[] processCommandApdu(byte[] commandApdu, Bundle extras) {
        apduReceivedCount++;
        Log.i(TAG, "=== APDU RECEIVED #" + apduReceivedCount + " ===");
        Log.i(TAG, "APDU length: " + commandApdu.length);
        Log.i(TAG, "APDU data: " + bytesToHex(commandApdu));
        Log.i(TAG, "Extras: " + (extras != null ? extras.toString() : "null"));
        
        // Log APDU structure
        if (commandApdu.length >= 4) {
            Log.i(TAG, "APDU Header: CLA=" + String.format("0x%02X", commandApdu[0]) + 
                      ", INS=" + String.format("0x%02X", commandApdu[1]) + 
                      ", P1=" + String.format("0x%02X", commandApdu[2]) + 
                      ", P2=" + String.format("0x%02X", commandApdu[3]));
        }
        
        if (commandApdu.length >= 5) {
            Log.i(TAG, "APDU Lc: " + String.format("0x%02X", commandApdu[4]));
        }
        
        // Check if this is a SELECT command for our AID
        if (commandApdu.length >= 4 && Arrays.equals(Arrays.copyOf(commandApdu, 4), SELECT_APDU_HEADER)) {
            Log.i(TAG, "SELECT command detected");
            
            if (commandApdu.length >= 5) {
                int aidLength = commandApdu[4] & 0xFF;
                Log.i(TAG, "Expected AID length: " + aidLength);
                
                if (commandApdu.length >= 5 + aidLength) {
                    byte[] receivedAid = Arrays.copyOfRange(commandApdu, 5, 5 + aidLength);
                    Log.i(TAG, "Received AID: " + bytesToHex(receivedAid));
                    Log.i(TAG, "Expected AID: " + bytesToHex(AID_BYTES));
                    Log.i(TAG, "AID match: " + Arrays.equals(receivedAid, AID_BYTES));
                    
                    if (Arrays.equals(receivedAid, AID_BYTES)) {
                        aidSelectedCount++;
                        Log.i(TAG, "=== AID SELECTED SUCCESSFULLY #" + aidSelectedCount + " ===");
                        
                        // Get the configured response data
                        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
                        String responseHex = prefs.getString(KEY_RESPONSE_DATA, "010203040506");
                        byte[] responseData = hexStringToByteArray(responseHex);
                        
                        Log.i(TAG, "Configured response data: " + responseHex);
                        Log.i(TAG, "Response data bytes: " + bytesToHex(responseData));
                        
                        // Return the response data + success status
                        byte[] response = new byte[responseData.length + 2];
                        System.arraycopy(responseData, 0, response, 0, responseData.length);
                        System.arraycopy(SUCCESS_SW, 0, response, responseData.length, 2);
                        
                        Log.i(TAG, "Sending response: " + bytesToHex(response));
                        sendDebugBroadcast("AID_SELECTED", "AID selected successfully, responding with: " + responseHex);
                        
                        return response;
                    } else {
                        Log.w(TAG, "AID mismatch - not our AID");
                        sendDebugBroadcast("AID_MISMATCH", "Received AID: " + bytesToHex(receivedAid));
                    }
                } else {
                    Log.w(TAG, "APDU too short for AID length");
                    sendDebugBroadcast("APDU_ERROR", "APDU too short for AID length");
                }
            } else {
                Log.w(TAG, "APDU too short for Lc field");
                sendDebugBroadcast("APDU_ERROR", "APDU too short for Lc field");
            }
        } else {
            Log.i(TAG, "Not a SELECT command or different header");
            Log.i(TAG, "Expected header: " + bytesToHex(SELECT_APDU_HEADER));
            sendDebugBroadcast("NON_SELECT_CMD", "Non-SELECT command received");
        }
        
        // For any other command, return success with no data
        Log.i(TAG, "Returning generic success response");
        sendDebugBroadcast("GENERIC_RESPONSE", "Returning generic success response");
        return SUCCESS_SW;
    }
    
    @Override
    public void onDeactivated(int reason) {
        Log.i(TAG, "=== HCE SERVICE DEACTIVATED ===");
        Log.i(TAG, "Deactivation reason: " + reason);
        
        String reasonStr;
        switch (reason) {
            case DEACTIVATION_LINK_LOSS:
                reasonStr = "Link Loss";
                break;
            case DEACTIVATION_DESELECTED:
                reasonStr = "Deselected";
                break;
            default:
                reasonStr = "Unknown (" + reason + ")";
                break;
        }
        
        Log.i(TAG, "Deactivation reason: " + reasonStr);
        Log.i(TAG, "Service statistics:");
        Log.i(TAG, "  - Service starts: " + serviceStartCount);
        Log.i(TAG, "  - Service stops: " + serviceStopCount);
        Log.i(TAG, "  - APDUs received: " + apduReceivedCount);
        Log.i(TAG, "  - AID selections: " + aidSelectedCount);
        
        sendDebugBroadcast("HCE_DEACTIVATED", "Service deactivated: " + reasonStr);
    }
    
    private void sendDebugBroadcast(String action, String message) {
        try {
            Intent intent = new Intent("com.example.mermaidsesame.DEBUG_UPDATE");
            intent.putExtra("action", action);
            intent.putExtra("message", message);
            intent.putExtra("timestamp", System.currentTimeMillis());
            intent.putExtra("service_start_count", serviceStartCount);
            intent.putExtra("service_stop_count", serviceStopCount);
            intent.putExtra("apdu_received_count", apduReceivedCount);
            intent.putExtra("aid_selected_count", aidSelectedCount);
            sendBroadcast(intent);
        } catch (Exception e) {
            Log.e(TAG, "Error sending debug broadcast", e);
        }
    }
    
    // Utility methods
    private static byte[] hexStringToByteArray(String s) {
        int len = s.length();
        byte[] data = new byte[len / 2];
        for (int i = 0; i < len; i += 2) {
            data[i / 2] = (byte) ((Character.digit(s.charAt(i), 16) << 4)
                                 + Character.digit(s.charAt(i+1), 16));
        }
        return data;
    }
    
    private static String bytesToHex(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02X ", b));
        }
        return sb.toString().trim();
    }
    

} 