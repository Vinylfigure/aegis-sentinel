"use client";

/* Engagement UI state — selection only, never data. Not persisted:
 * selections are per-visit focus, not program state. */

import { create } from "zustand";

export interface EngagementUiState {
  /** Focused reconciliation delta (drives the WhyCompletePanel story). */
  selectedDeltaId: string | null;
  selectDelta: (id: string | null) => void;
  /** Focused proof-graph node (drives the NodeInspector). */
  selectedProofNodeId: string | null;
  selectProofNode: (id: string | null) => void;
}

export const useEngagementStore = create<EngagementUiState>()((set) => ({
  selectedDeltaId: null,
  selectDelta: (id) => set({ selectedDeltaId: id }),
  selectedProofNodeId: null,
  selectProofNode: (id) => set({ selectedProofNodeId: id }),
}));
