"use client";
/* eslint-disable @typescript-eslint/no-explicit-any */

import React, { useState } from "react";
import BottomSheet from "./BottomSheet";
import ConfirmActionModal from "./ConfirmActionModal";

export interface ManagePlanSheetProps {
  isOpen: boolean;
  onClose: () => void;
  onSync: () => void;
  syncing: boolean;
  syncNotice: { kind: string; text: string } | null;
  showExportOptions: boolean;
  onExport: () => void;
  /** Inline export options UI, rendered in place of the Export row when showExportOptions. */
  exportOptions?: React.ReactNode;
  /** Extra rows such as the COROS push button. */
  extraRows?: React.ReactNode;
  recentPlans: any[];
  activePlanId?: number | null;
  formatPlanName: (p: any) => string;
  onSelectPlan: (id: number) => void;
  onPlanSettings: () => void;
  onNewPlan: () => void;
}

export default function ManagePlanSheet(p: ManagePlanSheetProps) {
  const [recentOpen, setRecentOpen] = useState(false);
  const [confirmNew, setConfirmNew] = useState(false);

  return (
    <>
      <BottomSheet isOpen={p.isOpen} onClose={p.onClose} title="Manage plan">
        <button type="button" className="manage-row" onClick={p.onSync} disabled={p.syncing}>
          {p.syncing ? "Syncing..." : "Sync watch"}
        </button>
        {p.syncNotice && (
          <div
            role={p.syncNotice.kind === "error" ? "alert" : "status"}
            style={{ fontSize: 12, padding: "6px 8px", color: p.syncNotice.kind === "error" ? "var(--accent-alert)" : "var(--text-secondary)" }}
          >
            {p.syncNotice.text}
          </div>
        )}
        {p.extraRows}
        {p.showExportOptions ? (
          p.exportOptions
        ) : (
          <button type="button" className="manage-row" onClick={p.onExport}>Export calendar</button>
        )}
        <button
          type="button"
          className="manage-row"
          aria-expanded={recentOpen}
          onClick={() => setRecentOpen((v) => !v)}
        >
          Load a recent plan
        </button>
        {recentOpen && (
          <div>
            {p.recentPlans.length === 0 ? (
              <div style={{ padding: 8, fontSize: 13, color: "var(--text-muted)" }}>No plans available</div>
            ) : (
              p.recentPlans.map((pl) => (
                <button
                  key={pl.id}
                  type="button"
                  className="manage-row"
                  style={{ paddingLeft: 24, fontWeight: pl.id === p.activePlanId ? 700 : 500 }}
                  onClick={() => {
                    p.onSelectPlan(pl.id);
                    p.onClose();
                  }}
                >
                  {p.formatPlanName(pl)}
                </button>
              ))
            )}
          </div>
        )}
        <button type="button" className="manage-row" onClick={p.onPlanSettings}>Plan settings</button>
        <button type="button" className="manage-row manage-row-destructive" onClick={() => setConfirmNew(true)}>
          Start a new plan
        </button>
      </BottomSheet>
      <ConfirmActionModal
        isOpen={confirmNew}
        onClose={() => setConfirmNew(false)}
        onConfirm={() => {
          setConfirmNew(false);
          p.onClose();
          p.onNewPlan();
        }}
        title="Start a new plan?"
        message="Start a new plan? Your current plan stays in Recent plans."
        confirmLabel="Confirm"
        cancelLabel="Cancel"
        isDestructive
      />
    </>
  );
}
