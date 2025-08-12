package com.example.mermaidsesame;

import android.content.Context;
import android.content.ComponentName;
import android.nfc.NfcAdapter;
import android.nfc.cardemulation.CardEmulation;
import android.util.Log;

public class HceAidRegistrar {

    private static final String TAG = "HceAidRegistrar";

    // Your AID, uppercase, no spaces
    private static final String AID = "F1726576406873";

    // Your AID category: "other" for private use
    private static final String AID_CATEGORY = "other";

    public static boolean registerDynamicAid(Context context) {
        NfcAdapter nfcAdapter = NfcAdapter.getDefaultAdapter(context);
        if (nfcAdapter == null) {
            Log.e(TAG, "NFC not supported on this device");
            return false;
        }

        CardEmulation cardEmulation = CardEmulation.getInstance(nfcAdapter);

        ComponentName serviceComponent = new ComponentName(context, MermaidSesameService.class);
        boolean result = cardEmulation.registerAidsForService(
            serviceComponent,
            AID_CATEGORY,
            java.util.Collections.singletonList(AID)
        );

        if (result) {
            Log.i(TAG, "Successfully registered dynamic AID: " + AID);
        } else {
            Log.e(TAG, "Failed to register dynamic AID: " + AID);
        }

        return result;
    }

    public static boolean unregisterDynamicAid(Context context) {
        NfcAdapter nfcAdapter = NfcAdapter.getDefaultAdapter(context);
        if (nfcAdapter == null) {
            Log.e(TAG, "NFC not supported on this device");
            return false;
        }

        CardEmulation cardEmulation = CardEmulation.getInstance(nfcAdapter);

        ComponentName serviceComponent = new ComponentName(context, MermaidSesameService.class);
        boolean result = cardEmulation.removeAidsForService(
            serviceComponent,
            AID_CATEGORY
        );

        if (result) {
            Log.i(TAG, "Successfully unregistered dynamic AIDs");
        } else {
            Log.e(TAG, "Failed to unregister dynamic AIDs");
        }

        return result;
    }
} 