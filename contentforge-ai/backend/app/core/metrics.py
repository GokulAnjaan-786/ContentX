import logging
from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger("contentforge.metrics")

# 1. AI Generation Metrics
AI_GENERATION_DURATION = Histogram(
    "contentforge_ai_generation_duration_seconds",
    "Time spent in seconds executing AI output generation",
    ["output_type", "status"],
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0, 60.0, 120.0],
)

AI_GENERATION_FAILURES = Counter(
    "contentforge_ai_generation_failures_total",
    "Total number of failed AI generation calls",
    ["output_type", "reason"],
)

AI_GENERATION_TOKENS = Counter(
    "contentforge_ai_generation_tokens_total",
    "Total token consumption across AI model invocations",
    ["output_type", "token_type"],  # token_type: prompt, completion
)

# 2. Document Extraction & Processing Metrics
DOCUMENT_PROCESSING_DURATION = Histogram(
    "contentforge_document_processing_duration_seconds",
    "Time spent extracting, cleaning, and chunking documents",
    ["source_type", "status"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

# 3. Content Understanding & Fact Registry Metrics
UNDERSTANDING_PASS_DURATION = Histogram(
    "contentforge_understanding_pass_duration_seconds",
    "Time spent in Content Understanding Pass building Fact Registry",
    buckets=[0.5, 1.0, 3.0, 5.0, 10.0, 20.0, 45.0, 90.0],
)

FACTS_EXTRACTED_TOTAL = Counter(
    "contentforge_facts_extracted_total",
    "Total number of atomic facts extracted and stored in Fact Registry",
)

# 4. Security & Compliance Metrics
SECURITY_DETECTIONS = Counter(
    "contentforge_security_detections_total",
    "Total occurrences of flagged security violations",
    ["category"],  # prompt_injection, pii, malware
)

ACTIVE_CELERY_JOBS = Gauge(
    "contentforge_active_generation_jobs",
    "Number of generation jobs currently actively executing",
)
