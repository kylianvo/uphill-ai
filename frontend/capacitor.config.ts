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
      resize: KeyboardResize.Body,
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
