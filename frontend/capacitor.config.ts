import type { CapacitorConfig } from '@capacitor/cli';
import { KeyboardResize } from '@capacitor/keyboard';

const config: CapacitorConfig = {
  appId: 'ai.uphill.app',
  appName: 'Uphill AI',
  webDir: 'out',
  server: {
    androidScheme: 'https',
    iosScheme: 'capacitor',
  },
  plugins: {
    StatusBar: {
      // Capacitor's naming is inverted from intuition: style 'DARK' means
      // "dark theme" -> light/white status bar content, meant for a DARK
      // app background. This app is light-themed, so 'LIGHT' (-> dark
      // content) is correct -- 'DARK' was rendering white time/battery
      // icons against this app's light background, making them invisible.
      style: 'LIGHT',
      backgroundColor: '#ffffff',
    },
    Keyboard: {
      // 'Body' only sets document.body's CSS height via injected JS -- it
      // never touches the WKWebView's actual native frame, so it's a no-op
      // for position:fixed elements (every modal in this app uses fixed
      // positioning), which stayed pinned to the full, un-shrunk viewport
      // and kept the keyboard covering whatever was focused. 'Native'
      // actually resizes the WKWebView's frame, which correctly shrinks
      // the effective viewport for fixed layouts too.
      resize: KeyboardResize.Native,
      resizeOnFullScreen: true,
    },
    SocialLogin: {
      // Only Google is wired up on native so far -- keeping the others
      // disabled avoids bundling their SDKs (Facebook/Apple/Twitter) into
      // the app for no reason. Flip to true if/when those get implemented.
      providers: {
        google: true,
        facebook: false,
        apple: false,
        twitter: false,
      },
    },
  },
};

export default config;
