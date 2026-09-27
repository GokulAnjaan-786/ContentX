import React from "react";
import { render, screen } from "@testing-library/react";
import {
  LinkedInCard,
  TweetThreadCard,
  AdvisoryCard,
  ExecutiveSummaryCard,
  InfographicCard,
  SlideDeckCard,
  VideoScriptCard,
} from "@/components/output-cards";
import { GeneratedOutput } from "@/lib/api";

describe("Results Screen: 7 Output Cards Rendering", () => {
  test("renders LinkedInCard with authentic post structure and confidence score", () => {
    const mockOutput: GeneratedOutput = {
      id: "out-1",
      job_id: "job-1",
      output_type: "linkedin",
      validation_score: 0.95,
      status: "completed",
      fact_ids_used: ["f1", "f2"],
      unverified_claims: [],
      created_at: "2026-09-26T00:00:00Z",
      content: {
        hook: "Critical insight for CISOs in 2026.",
        body: "Our threat intelligence team detected 340% increase in API attacks.",
        hashtags: ["CyberSecurity", "API", "ThreatIntel"],
        call_to_action: "Download the complete incident report below.",
        fact_ids_used: ["f1", "f2"],
      },
    };

    render(<LinkedInCard output={mockOutput} />);

    expect(screen.getByTestId("linkedin-card")).toBeInTheDocument();
    expect(screen.getByText(/Critical insight for CISOs in 2026/i)).toBeInTheDocument();
    expect(screen.getByText(/340% increase in API attacks/i)).toBeInTheDocument();
    expect(screen.getByText(/#CyberSecurity/i)).toBeInTheDocument();
    expect(screen.getByText(/95% source-grounded/i)).toBeInTheDocument();
  });

  test("renders TweetThreadCard with numbered tweet bubbles", () => {
    const mockOutput: GeneratedOutput = {
      id: "out-2",
      job_id: "job-1",
      output_type: "twitter",
      validation_score: 0.92,
      status: "completed",
      fact_ids_used: ["f1"],
      unverified_claims: [],
      created_at: "2026-09-26T00:00:00Z",
      content: {
        tweets: [
          { order: 1, text: "1/ Threat actors breached 42 financial nodes last month." },
          { order: 2, text: "2/ Immediate multi-factor rotation mitigated 98% of lateral movement." },
        ],
        fact_ids_used: ["f1"],
      },
    };

    render(<TweetThreadCard output={mockOutput} />);

    expect(screen.getByTestId("twitter-card")).toBeInTheDocument();
    expect(screen.getByText(/Threat actors breached 42 financial nodes/i)).toBeInTheDocument();
    expect(screen.getByText(/Immediate multi-factor rotation mitigated/i)).toBeInTheDocument();
    expect(screen.getByText(/92% source-grounded/i)).toBeInTheDocument();
  });

  test("renders AdvisoryCard with severity, scope, details, and actions", () => {
    const mockOutput: GeneratedOutput = {
      id: "out-3",
      job_id: "job-1",
      output_type: "advisory",
      validation_score: 0.98,
      status: "completed",
      fact_ids_used: ["f1", "f2", "f3"],
      unverified_claims: [],
      created_at: "2026-09-26T00:00:00Z",
      content: {
        title: "CVE-2026-9901 Zero-Day Vulnerability in Auth Microservice",
        severity: "CRITICAL",
        summary: "Remote code execution possible without prior authentication.",
        scope: "Kubernetes ingress auth proxy running v2.4.1",
        details: "Buffer overflow during JWT public key parsing leads to shell drop.",
        recommended_actions: [
          "Deploy hotfix patch v2.4.2 immediately.",
          "Restrict ingress API traffic to trusted IPs.",
        ],
        references: ["https://nvd.nist.gov/vuln/detail/CVE-2026-9901"],
        fact_ids_used: ["f1", "f2", "f3"],
      },
    };

    render(<AdvisoryCard output={mockOutput} />);

    expect(screen.getByTestId("advisory-card")).toBeInTheDocument();
    expect(screen.getByText(/CVE-2026-9901 Zero-Day Vulnerability/i)).toBeInTheDocument();
    expect(screen.getByText(/CRITICAL/i)).toBeInTheDocument();
    expect(screen.getByText(/Kubernetes ingress auth proxy/i)).toBeInTheDocument();
    expect(screen.getByText(/Deploy hotfix patch v2.4.2 immediately/i)).toBeInTheDocument();
    expect(screen.getByText(/98% source-grounded/i)).toBeInTheDocument();
  });

  test("renders ExecutiveSummaryCard with narrative and key takeaways", () => {
    const mockOutput: GeneratedOutput = {
      id: "out-4",
      job_id: "job-1",
      output_type: "executive_summary",
      validation_score: 0.91,
      status: "completed",
      fact_ids_used: ["f1"],
      unverified_claims: [],
      created_at: "2026-09-26T00:00:00Z",
      content: {
        title: "Q3 AI Infrastructure Scaling & Resilience Audit",
        summary_text: "Our enterprise data footprint doubled while latency dropped 45%.",
        key_takeaways: [
          "Autonomous agent workloads reduced processing costs by $1.2M.",
          "Data privacy compliance achieved 100% adherence across all EU regions.",
        ],
        fact_ids_used: ["f1"],
      },
    };

    render(<ExecutiveSummaryCard output={mockOutput} />);

    expect(screen.getByTestId("executive-summary-card")).toBeInTheDocument();
    expect(screen.getByText(/Q3 AI Infrastructure Scaling/i)).toBeInTheDocument();
    expect(screen.getByText(/Autonomous agent workloads reduced processing costs/i)).toBeInTheDocument();
    expect(screen.getByText(/91% source-grounded/i)).toBeInTheDocument();
  });

  test("renders InfographicCard with headline, modular sections, and styling suggestions", () => {
    const mockOutput: GeneratedOutput = {
      id: "out-5",
      job_id: "job-1",
      output_type: "infographic",
      validation_score: 0.89,
      status: "completed",
      fact_ids_used: ["f1", "f2"],
      unverified_claims: [],
      created_at: "2026-09-26T00:00:00Z",
      content: {
        headline: "The State of Cloud Security 2026",
        sections: [
          { order: 1, stat_or_point: "87% of companies adopt zero-trust models", icon_suggestion: "shield" },
          { order: 2, stat_or_point: "3.2x faster incident recovery time", icon_suggestion: "zap" },
        ],
        layout_style: "Vertical Split Grid",
        colour_theme: "Cyber Navy & Emerald",
        fact_ids_used: ["f1", "f2"],
      },
    };

    render(<InfographicCard output={mockOutput} />);

    expect(screen.getByTestId("infographic-card")).toBeInTheDocument();
    expect(screen.getByText(/The State of Cloud Security 2026/i)).toBeInTheDocument();
    expect(screen.getByText(/Vertical Split Grid/i)).toBeInTheDocument();
    expect(screen.getByText(/Cyber Navy & Emerald/i)).toBeInTheDocument();
    expect(screen.getByText(/87% of companies adopt zero-trust models/i)).toBeInTheDocument();
  });

  test("renders SlideDeckCard with slide viewer, bullets, and speaker notes", () => {
    const mockOutput: GeneratedOutput = {
      id: "out-6",
      job_id: "job-1",
      output_type: "presentation",
      validation_score: 0.94,
      status: "completed",
      fact_ids_used: ["f1"],
      unverified_claims: [],
      created_at: "2026-09-26T00:00:00Z",
      content: {
        slides: [
          {
            slide_no: 1,
            title: "Strategic Overview: Fact-Grounded AI",
            bullets: ["Eliminating generative hallucination", "Single understanding pass architecture"],
            speaker_notes: "Welcome board members and introduce the core pipeline.",
            visual_suggestion: "Split architecture diagram showing single understanding pass",
          },
        ],
        fact_ids_used: ["f1"],
      },
    };

    render(<SlideDeckCard output={mockOutput} />);

    expect(screen.getByTestId("presentation-card")).toBeInTheDocument();
    expect(screen.getByText(/Strategic Overview: Fact-Grounded AI/i)).toBeInTheDocument();
    expect(screen.getByText(/Eliminating generative hallucination/i)).toBeInTheDocument();
    expect(screen.getByText(/Welcome board members/i)).toBeInTheDocument();
    expect(screen.getByText(/94% source-grounded/i)).toBeInTheDocument();
  });

  test("renders VideoScriptCard with scenes, narration, and time estimate", () => {
    const mockOutput: GeneratedOutput = {
      id: "out-7",
      job_id: "job-1",
      output_type: "video_package",
      validation_score: 0.93,
      status: "completed",
      fact_ids_used: ["f1"],
      unverified_claims: [],
      created_at: "2026-09-26T00:00:00Z",
      content: {
        title: "Product Launch Video: ContentForge AI",
        total_duration_estimate: "1m 30s",
        scenes: [
          {
            scene_no: 1,
            narration: "Every week, organizations produce dozens of high-value reports.",
            visual_description: "Montage of PDF reports and busy office terminals",
            subtitle_text: "High-value reports trapped in PDF silos.",
            duration_estimate_sec: 15,
          },
        ],
        fact_ids_used: ["f1"],
      },
    };

    render(<VideoScriptCard output={mockOutput} />);

    expect(screen.getByTestId("video-package-card")).toBeInTheDocument();
    expect(screen.getByText(/Product Launch Video: ContentForge AI/i)).toBeInTheDocument();
    expect(screen.getByText(/Runtime: 1m 30s/i)).toBeInTheDocument();
    expect(screen.getByText(/Every week, organizations produce dozens of high-value reports/i)).toBeInTheDocument();
    expect(screen.getByText(/93% source-grounded/i)).toBeInTheDocument();
  });
});
