package ai.uphill.app;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(WebAuthSessionPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
