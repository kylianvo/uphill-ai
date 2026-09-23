package ai.uphill.app;

import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.net.Uri;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

// Opens a third-party OAuth consent page in the browser and resolves with the
// URL it redirects to on `callbackScheme`, which reaches MainActivity through
// the matching intent-filter in AndroidManifest.xml.
@CapacitorPlugin(name = "WebAuthSession")
public class WebAuthSessionPlugin extends Plugin {

    private String pendingCallId;
    private String callbackScheme;
    private boolean leftApp;

    @PluginMethod
    public void start(PluginCall call) {
        String url = call.getString("url");
        String scheme = call.getString("callbackScheme");
        if (url == null || scheme == null) {
            call.reject("url and callbackScheme are required");
            return;
        }
        PluginCall previous = takePendingCall();
        if (previous != null) {
            previous.reject("Cancelled", "CANCELLED");
        }
        try {
            getActivity().startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
        } catch (ActivityNotFoundException e) {
            call.reject("No browser available");
            return;
        }
        callbackScheme = scheme;
        leftApp = false;
        getBridge().saveCall(call);
        pendingCallId = call.getCallbackId();
    }

    @Override
    protected void handleOnNewIntent(Intent intent) {
        super.handleOnNewIntent(intent);
        Uri data = intent.getData();
        if (data == null || callbackScheme == null || !callbackScheme.equals(data.getScheme())) {
            return;
        }
        PluginCall call = takePendingCall();
        if (call == null) {
            return;
        }
        JSObject result = new JSObject();
        result.put("url", data.toString());
        call.resolve(result);
    }

    @Override
    protected void handleOnPause() {
        super.handleOnPause();
        if (pendingCallId != null) {
            leftApp = true;
        }
    }

    // Android delivers the redirect intent before onResume, so reaching here
    // with the call still pending means the user came back without finishing.
    @Override
    protected void handleOnResume() {
        super.handleOnResume();
        if (pendingCallId != null && leftApp) {
            PluginCall call = takePendingCall();
            if (call != null) {
                call.reject("Cancelled", "CANCELLED");
            }
        }
    }

    private PluginCall takePendingCall() {
        if (pendingCallId == null) {
            return null;
        }
        PluginCall call = getBridge().getSavedCall(pendingCallId);
        if (call != null) {
            getBridge().releaseCall(call);
        }
        pendingCallId = null;
        leftApp = false;
        return call;
    }
}
