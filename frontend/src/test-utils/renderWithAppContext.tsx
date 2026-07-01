import { ReactNode } from "react";
import { renderHook, RenderHookOptions } from "@testing-library/react";
import { AppProvider } from "../contexts/AppContext";

// Every hook in src/hooks/ calls useAppContext() internally, so any hook
// unit test needs an AppProvider wrapper -- a bare renderHook throws.
export function renderHookWithApp<TResult, TProps>(
  callback: (props: TProps) => TResult,
  options?: Omit<RenderHookOptions<TProps>, "wrapper">
) {
  return renderHook(callback, {
    wrapper: ({ children }: { children: ReactNode }) => <AppProvider>{children}</AppProvider>,
    ...options,
  });
}
