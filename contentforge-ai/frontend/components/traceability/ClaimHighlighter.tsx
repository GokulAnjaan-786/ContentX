import React from "react";
import { UnverifiedClaim } from "@/lib/api";
import { SelectedClaimInfo } from "./TraceabilityPanel";
import { AlertCircle } from "lucide-react";

export interface ClaimHighlighterProps {
  text: string;
  factIdsUsed?: string[];
  unverifiedClaims?: UnverifiedClaim[];
  selectedClaim?: SelectedClaimInfo | null;
  onSelectClaim?: (claim: SelectedClaimInfo) => void;
  className?: string;
}

export const ClaimHighlighter: React.FC<ClaimHighlighterProps> = ({
  text,
  factIdsUsed = [],
  unverifiedClaims = [],
  selectedClaim,
  onSelectClaim,
  className = "",
}) => {
  if (!text) return null;

  // Split text into readable sentences / segments
  // Matches sentence delimiters while keeping the punctuation
  const segments = text.split(/(?<=[.!?])\s+(?=[A-Z0-9"'])/g);

  return (
    <div className={`leading-relaxed ${className}`}>
      {segments.map((segment, index) => {
        const trimmed = segment.trim();
        if (!trimmed) return null;

        // Check if this segment matches or contains any unverified claim
        const matchingUnverified = unverifiedClaims.find((u) => {
          const claimStr = u && typeof u.claim === "string" ? u.claim : (u as any)?.reason || (u as any)?.schema_error || (u as any)?.error;
          if (!claimStr || typeof claimStr !== "string") return false;
          const cleanU = claimStr.trim().toLowerCase();
          const cleanS = trimmed.toLowerCase();
          return (
            cleanS.includes(cleanU) ||
            cleanU.includes(cleanS) ||
            (cleanS.length >= 10 && cleanU.length >= 10 && cleanS.slice(0, 30) === cleanU.slice(0, 30))
          );
        });

        const isUnverified = !!matchingUnverified;

        // Extract any [f1], [f2] citation markers inside the sentence
        const citationMatches = trimmed.match(/\[f\d+\]/gi);
        const sentenceFactIds = citationMatches
          ? citationMatches.map((m) => m.toLowerCase().replace(/\[|\]/g, ""))
          : factIdsUsed;

        const isSelected =
          selectedClaim &&
          (selectedClaim.claimText === trimmed ||
            selectedClaim.claimText.includes(trimmed) ||
            trimmed.includes(selectedClaim.claimText));

        if (isUnverified) {
          return (
            <span
              key={index}
              data-testid="unverified-claim"
              data-unverified="true"
              title="This claim could not be matched to the source document"
              onClick={() =>
                onSelectClaim &&
                onSelectClaim({
                  claimText: trimmed,
                  factIds: [],
                  isUnverified: true,
                  unverifiedReason:
                    matchingUnverified?.reason ||
                    "This claim could not be matched to the source document",
                })
              }
              className={`claim-unverified group relative inline cursor-pointer ${
                isSelected ? "claim-selected" : ""
              }`}
            >
              {segment}{" "}
              <span
                data-testid="unverified-tooltip-indicator"
                className="inline-flex items-center text-amber-600 align-super ml-0.5"
                title="This claim could not be matched to the source document"
              >
                <AlertCircle className="w-3 h-3 inline" />
              </span>
            </span>
          );
        }

        return (
          <span
            key={index}
            data-testid="verified-claim"
            onClick={() =>
              onSelectClaim &&
              onSelectClaim({
                claimText: trimmed,
                factIds: sentenceFactIds,
                isUnverified: false,
              })
            }
            className={`claim-verified inline hover:bg-brand-50/70 hover:text-brand-900 cursor-pointer rounded transition-colors ${
              isSelected ? "claim-selected" : ""
            }`}
            title="Click to view source evidence in Fact Registry"
          >
            {segment}{" "}
          </span>
        );
      })}
    </div>
  );
};
