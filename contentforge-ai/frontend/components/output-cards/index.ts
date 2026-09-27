import React from "react";
import { OutputType } from "@/lib/api";
import { OutputCardProps, LinkedInCard } from "./LinkedInCard";
import { TweetThreadCard } from "./TweetThreadCard";
import { AdvisoryCard } from "./AdvisoryCard";
import { ExecutiveSummaryCard } from "./ExecutiveSummaryCard";
import { InfographicCard } from "./InfographicCard";
import { SlideDeckCard } from "./SlideDeckCard";
import { VideoScriptCard } from "./VideoScriptCard";

export {
  LinkedInCard,
  TweetThreadCard,
  AdvisoryCard,
  ExecutiveSummaryCard,
  InfographicCard,
  SlideDeckCard,
  VideoScriptCard,
};

export interface OutputTypeMeta {
  type: OutputType;
  label: string;
  shortLabel: string;
  description: string;
  iconName: string;
}

export const OUTPUT_TYPE_REGISTRY: Record<OutputType, {
  label: string;
  shortLabel: string;
  description: string;
  component: React.ComponentType<OutputCardProps<any>>;
}> = {
  linkedin: {
    label: "LinkedIn Post",
    shortLabel: "LinkedIn",
    description: "Professional publication-ready LinkedIn content.",
    component: LinkedInCard,
  },
  twitter: {
    label: "Twitter/X Post",
    shortLabel: "Twitter/X",
    description: "Platform-optimized post or thread.",
    component: TweetThreadCard,
  },
  video_package: {
    label: "Video",
    shortLabel: "Video",
    description: "Script, storyboard, narration, subtitles and visual recommendations.",
    component: VideoScriptCard,
  },
  infographic: {
    label: "Infographic",
    shortLabel: "Infographic",
    description: "Infographic content, structure and visual recommendations.",
    component: InfographicCard,
  },
  advisory: {
    label: "Advisory",
    shortLabel: "Advisory",
    description: "Structured advisory document.",
    component: AdvisoryCard,
  },
  executive_summary: {
    label: "Executive Summary",
    shortLabel: "Exec Summary",
    description: "Concise executive briefing.",
    component: ExecutiveSummaryCard,
  },
  presentation: {
    label: "Presentation",
    shortLabel: "Presentation",
    description: "Slides, content, visual recommendations and speaker notes.",
    component: SlideDeckCard,
  },
};

export const ALL_OUTPUT_TYPES: OutputType[] = [
  "linkedin",
  "twitter",
  "video_package",
  "infographic",
  "advisory",
  "executive_summary",
  "presentation",
];
