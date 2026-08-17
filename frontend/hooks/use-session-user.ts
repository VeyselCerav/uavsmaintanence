"use client";

import { useSyncExternalStore } from "react";

import {
  getServerUserSnapshot,
  getStoredUser,
  subscribeSession,
  type AuthUser,
} from "@/lib/auth";

export function useSessionUser(): AuthUser | null {
  return useSyncExternalStore(subscribeSession, getStoredUser, getServerUserSnapshot);
}
