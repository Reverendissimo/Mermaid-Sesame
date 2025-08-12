package com.example.mermaidsesame;

import android.Manifest;
import android.app.Activity;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.nfc.NfcAdapter;
import android.nfc.cardemulation.CardEmulation;
import android.nfc.cardemulation.HostApduService;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import java.util.Arrays;

public class MainActivity extends Activity {
    private static final String TAG = "MermaidSesame";
    private static final String PREFS_NAME = "MermaidSesamePrefs";
    private static final String KEY_RESPONSE_DATA = "response_data";
    
    private EditText responseDataEdit;
    private Button saveButton;
    private Button clearLogsButton;
    private Button startServiceButton;
    private Button stopServiceButton;
    private TextView logTextView;
    private ScrollView logScrollView;
    private NfcAdapter nfcAdapter;
    private CardEmulation cardEmulation;
    
    // Debug broadcast receiver
    private BroadcastReceiver debugReceiver;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        // Initialize views
        responseDataEdit = findViewById(R.id.response_data_edit);
        saveButton = findViewById(R.id.save_button);
        clearLogsButton = findViewById(R.id.clear_logs_button);
        startServiceButton = findViewById(R.id.start_service_button);
        stopServiceButton = findViewById(R.id.stop_service_button);
        logTextView = findViewById(R.id.log_text);
        logScrollView = findViewById(R.id.log_scroll);
        
        // Check NFC availability
        nfcAdapter = NfcAdapter.getDefaultAdapter(this);
        if (nfcAdapter == null) {
            logMessage("ERROR: NFC not available on this device");
            return;
        }
        
        // Initialize CardEmulation
        cardEmulation = CardEmulation.getInstance(nfcAdapter);
        if (cardEmulation == null) {
            logMessage("ERROR: CardEmulation not available on this device");
            return;
        }
        
        if (!nfcAdapter.isEnabled()) {
            logMessage("WARNING: NFC is disabled. Please enable NFC in settings.");
        } else {
            logMessage("NFC is enabled and ready");
        }
        
        // Check permissions
        checkPermissions();
        
        // Load saved response data
        loadSavedResponseData();
        
        // Set up button listeners
        saveButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                saveResponseData();
            }
        });
        
        clearLogsButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                clearLogs();
            }
        });
        
        startServiceButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startHceService();
            }
        });
        
        stopServiceButton.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                stopHceService();
            }
        });
        
        // Set up debug broadcast receiver
        setupDebugReceiver();
        
        logMessage("=== MERMAID SESAME HCE DEBUG APP ===");
        logMessage("AID: F1726576406873");
        logMessage("Category: OTHER (non-payment)");
        logMessage("Ready to monitor HCE routing and APDU processing");
        logMessage("Place this phone near the ESP32 reader to test");
        
        // Automatically start HCE service when app launches
        logMessage("Auto-starting HCE service...");
        startHceService();
    }
    
    private void setupDebugReceiver() {
        debugReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                String action = intent.getStringExtra("action");
                String message = intent.getStringExtra("message");
                long timestamp = intent.getLongExtra("timestamp", 0);
                int serviceStartCount = intent.getIntExtra("service_start_count", 0);
                int serviceStopCount = intent.getIntExtra("service_stop_count", 0);
                int apduReceivedCount = intent.getIntExtra("apdu_received_count", 0);
                int aidSelectedCount = intent.getIntExtra("aid_selected_count", 0);
                
                logMessage("=== HCE SERVICE EVENT ===");
                logMessage("Action: " + action);
                logMessage("Message: " + message);
                logMessage("Timestamp: " + timestamp);
                logMessage("Service Stats:");
                logMessage("  - Starts: " + serviceStartCount);
                logMessage("  - Stops: " + serviceStopCount);
                logMessage("  - APDUs: " + apduReceivedCount);
                logMessage("  - AID Selections: " + aidSelectedCount);
                
                // Highlight important events
                if ("AID_SELECTED".equals(action)) {
                    logMessage("*** SUCCESS: ESP32 SELECTED OUR AID! ***");
                    logMessage("*** HCE ROUTING IS WORKING! ***");
                } else if ("HCE_SERVICE_CREATED".equals(action)) {
                    logMessage("*** HCE SERVICE CREATED SUCCESSFULLY ***");
                } else if ("HCE_SERVICE_STARTED".equals(action)) {
                    logMessage("*** HCE SERVICE STARTED SUCCESSFULLY ***");
                } else if ("APDU_RECEIVED".equals(action)) {
                    logMessage("*** APDU RECEIVED FROM READER ***");
                }
            }
        };
        
        IntentFilter filter = new IntentFilter("com.example.mermaidsesame.DEBUG_UPDATE");
        registerReceiver(debugReceiver, filter);
        
        logMessage("Debug broadcast receiver registered");
    }
    
    private void startHceService() {
        try {
            Intent serviceIntent = new Intent(this, MermaidSesameService.class);
            startService(serviceIntent);
            logMessage("Manually started HCE service");
        } catch (Exception e) {
            logMessage("ERROR starting HCE service: " + e.getMessage());
        }
    }
    
    private void stopHceService() {
        try {
            Intent serviceIntent = new Intent(this, MermaidSesameService.class);
            stopService(serviceIntent);
            logMessage("Manually stopped HCE service");
        } catch (Exception e) {
            logMessage("ERROR stopping HCE service: " + e.getMessage());
        }
    }
    
    private void checkPermissions() {
        String[] permissions = {
            Manifest.permission.NFC,
            Manifest.permission.INTERNET,
            Manifest.permission.ACCESS_NETWORK_STATE,
            Manifest.permission.ACCESS_WIFI_STATE,
            Manifest.permission.WAKE_LOCK,
            Manifest.permission.FOREGROUND_SERVICE
        };
        
        // Check which permissions are not granted
        java.util.List<String> permissionsToRequest = new java.util.ArrayList<>();
        for (String permission : permissions) {
            if (ContextCompat.checkSelfPermission(this, permission) 
                != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(permission);
                logMessage("Permission needed: " + permission);
            } else {
                logMessage("Permission granted: " + permission);
            }
        }
        
        // Request permissions if needed
        if (!permissionsToRequest.isEmpty()) {
            ActivityCompat.requestPermissions(this, 
                permissionsToRequest.toArray(new String[0]), 1);
            logMessage("Requesting " + permissionsToRequest.size() + " permissions");
        }
    }
    
    private void loadSavedResponseData() {
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        String savedData = prefs.getString(KEY_RESPONSE_DATA, "010203040506");
        responseDataEdit.setText(savedData);
        logMessage("Loaded saved response data: " + savedData);
    }
    
    private void saveResponseData() {
        String data = responseDataEdit.getText().toString().trim();
        
        // Validate hex format
        if (!data.matches("[0-9A-Fa-f]+")) {
            Toast.makeText(this, "Please enter valid hex data (0-9, A-F)", Toast.LENGTH_SHORT).show();
            logMessage("ERROR: Invalid hex format in response data");
            return;
        }
        
        // Ensure exactly 6 bytes (12 hex characters)
        if (data.length() != 12) {
            Toast.makeText(this, "Please enter exactly 6 bytes (12 hex characters)", Toast.LENGTH_SHORT).show();
            logMessage("ERROR: Response data must be exactly 6 bytes (12 hex chars)");
            return;
        }
        
        // Save to preferences
        SharedPreferences prefs = getSharedPreferences(PREFS_NAME, MODE_PRIVATE);
        SharedPreferences.Editor editor = prefs.edit();
        editor.putString(KEY_RESPONSE_DATA, data);
        editor.apply();
        
        Toast.makeText(this, "Response data saved: " + data, Toast.LENGTH_SHORT).show();
        logMessage("Response data saved: " + data);
    }
    
    private void clearLogs() {
        logTextView.setText("");
        logMessage("Logs cleared");
    }
    
    public void logMessage(String message) {
        String timestamp = java.time.LocalTime.now().toString();
        String logEntry = "[" + timestamp + "] " + message + "\n";
        
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                logTextView.append(logEntry);
                // Auto-scroll to bottom
                logScrollView.post(new Runnable() {
                    @Override
                    public void run() {
                        logScrollView.fullScroll(ScrollView.FOCUS_DOWN);
                    }
                });
            }
        });
        
        Log.d(TAG, message);
    }
    
    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        
        if (requestCode == 1) {
            boolean allGranted = true;
            for (int i = 0; i < permissions.length; i++) {
                if (grantResults[i] == PackageManager.PERMISSION_GRANTED) {
                    logMessage("Permission granted: " + permissions[i]);
                } else {
                    logMessage("Permission denied: " + permissions[i]);
                    allGranted = false;
                }
            }
            
            if (allGranted) {
                logMessage("All permissions granted! Starting HCE service...");
                startHceService();
            } else {
                logMessage("Some permissions were denied. HCE service may not work properly.");
            }
        }
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        logMessage("Activity resumed - app is in foreground");
        
        // Enable foreground dispatch for NFC priority
        if (nfcAdapter != null && nfcAdapter.isEnabled()) {
            logMessage("Enabling foreground dispatch for NFC priority...");
            enableForegroundDispatch();
            logMessage("Ensuring HCE service is active...");
            startHceService();
        }
    }
    
    @Override
    protected void onPause() {
        super.onPause();
        logMessage("Activity paused");
        
        // Disable foreground dispatch
        if (nfcAdapter != null && nfcAdapter.isEnabled()) {
            logMessage("Disabling foreground dispatch...");
            disableForegroundDispatch();
        }
    }
    
    private void enableForegroundDispatch() {
        try {
            Intent intent = new Intent(this, getClass());
            intent.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP);
            PendingIntent pendingIntent = PendingIntent.getActivity(this, 0, intent, 
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_MUTABLE);
            
            nfcAdapter.enableForegroundDispatch(this, pendingIntent, null, null);
            logMessage("Foreground dispatch enabled successfully");
            
            // Set our HCE service as the preferred service
            ComponentName serviceComponent = new ComponentName(this, MermaidSesameService.class);
            boolean success = cardEmulation.setPreferredService(this, serviceComponent);
            if (success) {
                logMessage("HCE service set as preferred service successfully");
            } else {
                logMessage("WARNING: Failed to set HCE service as preferred service");
            }
        } catch (Exception e) {
            logMessage("ERROR enabling foreground dispatch: " + e.getMessage());
        }
    }
    
    private void disableForegroundDispatch() {
        try {
            nfcAdapter.disableForegroundDispatch(this);
            logMessage("Foreground dispatch disabled");
            
            // Disable preferred service
            cardEmulation.unsetPreferredService(this);
            logMessage("HCE service unset as preferred service");
        } catch (Exception e) {
            logMessage("ERROR disabling foreground dispatch: " + e.getMessage());
        }
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (debugReceiver != null) {
            unregisterReceiver(debugReceiver);
            logMessage("Debug broadcast receiver unregistered");
        }
    }
} 