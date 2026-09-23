import { registerPlugin } from '@capacitor/core';

// Local native plugin (ios/App/App/WebAuthSessionPlugin.swift,
// android/.../WebAuthSessionPlugin.java). Rejects with code "CANCELLED" when
// the user closes the consent page.
export interface WebAuthSessionPlugin {
  start(options: { url: string; callbackScheme: string }): Promise<{ url: string }>;
}

export const WebAuthSession = registerPlugin<WebAuthSessionPlugin>('WebAuthSession');
