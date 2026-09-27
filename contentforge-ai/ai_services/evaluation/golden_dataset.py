"""
ContentForge AI Golden Dataset for AI Evaluation Pipeline.
Contains 16 curated documents across multiple domains (incident reports,
technical articles, security advisories, and executive summaries) with
manually verified ground truth facts.
"""

from typing import Any, Dict, List

GOLDEN_DOCUMENTS: List[Dict[str, Any]] = [
    # 1. Incident Report: Cloud Database Outage
    {
        "id": "doc_01",
        "title": "Post-Mortem: US-East Multi-AZ Aurora DB Failover Incident",
        "category": "incident_report",
        "text": (
            "On August 12, 2026, at 04:12 UTC, CloudForge Aurora PostgreSQL cluster experienced a network split in availability zone us-east-1a. "
            "The cluster primary replica became unresponsive, triggering an automated failover to us-east-1b. "
            "Due to DNS replication latency in the internal service mesh, application connection pools remained pinned to the dead instance for 18 minutes. "
            "Total service degradation lasted 24 minutes. No persistent customer transactions were lost. "
            "Remediation action items: reduce DNS TTL to 5 seconds and implement circuit breakers in the API gateway connection pool."
        ),
        "ground_truth_facts": [
            "Network split occurred in us-east-1a on August 12, 2026 at 04:12 UTC.",
            "Primary database failed over to us-east-1b.",
            "DNS replication latency caused connection pools to pin to dead instance for 18 minutes.",
            "Total service degradation lasted 24 minutes.",
            "Zero persistent customer transactions were lost.",
        ],
        "target_outputs": ["linkedin", "twitter", "advisory", "executive_summary"],
    },
    # 2. Security Advisory: Critical Zero-Day Patch
    {
        "id": "doc_02",
        "title": "Security Advisory SEC-2026-104: Critical RPC Auth Bypass",
        "category": "security_advisory",
        "text": (
            "Cybersecurity emergency bulletin SEC-2026-104 published on September 3, 2026. "
            "A critical flaw in RPC authentication broker allows unauthenticated remote attackers to execute arbitrary code with root privileges. "
            "Assigned CVSS v3 score is 9.8 (Critical). "
            "Affected versions: brokerd v2.0 through v2.4.1. "
            "All operators must immediately upgrade to v2.4.2 or block external ingress on port 8443. "
            "Proof-of-concept exploits were detected in the wild targeting European enterprise customers."
        ),
        "ground_truth_facts": [
            "Security bulletin SEC-2026-104 published on September 3, 2026.",
            "Critical unauthenticated RPC remote code execution vulnerability with CVSS 9.8.",
            "Affects brokerd versions v2.0 through v2.4.1.",
            "Mitigation requires upgrading to v2.4.2 or blocking ingress on port 8443.",
            "Active exploitation observed targeting European enterprises.",
        ],
        "target_outputs": ["advisory", "twitter", "executive_summary"],
    },
    # 3. Technical Article: Zero-Trust Microsegmentation
    {
        "id": "doc_03",
        "title": "Architectural Patterns: Zero-Trust Service Mesh in Production",
        "category": "technical_article",
        "text": (
            "Transitioning from perimeter firewalls to microsegmentation reduces breach blast radius by up to 85%. "
            "By enforcing mutual TLS (mTLS) with SPIFFE identities, services verify caller identity cryptographically on every packet. "
            "Benchmarking shows Envoy proxy sidecar adds 1.2 milliseconds of p99 latency overhead while processing 12,000 requests per second. "
            "Access policies should follow least-privilege principles, rotating cryptographic certificates every 24 hours. "
            "Key architectural components include identity provider, service control plane, and distributed policy enforcement points."
        ),
        "ground_truth_facts": [
            "Zero-trust microsegmentation reduces breach blast radius by up to 85%.",
            "Mutual TLS with SPIFFE identities provides cryptographic caller verification.",
            "Sidecar latency overhead is 1.2ms p99 at 12,000 requests per second.",
            "Cryptographic certificates must be rotated every 24 hours.",
        ],
        "target_outputs": ["linkedin", "twitter", "executive_summary"],
    },
    # 4. Executive Brief: AI Infrastructure Efficiency
    {
        "id": "doc_04",
        "title": "Executive Strategy: Scaling AI Compute Efficiency in FY27",
        "category": "executive_brief",
        "text": (
            "CloudForge AI's FY27 capital plan allocates $4.8M towards high-efficiency GPU cluster upgrades. "
            "Adopting FP8 precision quantization lowered inference electrical consumption by 38% across production inference workloads. "
            "Throughput improved from 140 tokens per second to 230 tokens per second on 70B parameter models. "
            "Total operating expense per million generated tokens decreased from $1.20 to $0.45. "
            "The executive board targets 100% renewable power certification for all owned datacenters by Q3 2027."
        ),
        "ground_truth_facts": [
            "FY27 capital plan allocates $4.8M to GPU compute upgrades.",
            "FP8 precision quantization reduced inference energy use by 38%.",
            "Inference throughput increased to 230 tokens/sec on 70B models.",
            "Operating cost dropped from $1.20 to $0.45 per million tokens.",
            "Targeting 100% renewable energy certification by Q3 2027.",
        ],
        "target_outputs": ["executive_summary", "linkedin"],
    },
    # 5. Incident Report: BGP Route Hijacking
    {
        "id": "doc_05",
        "title": "Incident Retrospective: Edge Ingress BGP Route Leak",
        "category": "incident_report",
        "text": (
            "On May 19, 2026, autonomous system AS-9110 leaked 42 IP prefixes to an upstream Tier-2 transit provider. "
            "Inbound traffic intended for CloudForge European endpoints was routed through misconfigured transit nodes in Frankfurt. "
            "Packet loss surged to 62% for 31 minutes until RPKI route origin validation filtering dropped the invalid announcements. "
            "No data modification or man-in-the-middle decryption took place as all traffic was end-to-end TLS 1.3 encrypted. "
            "Corrective action: enforce strict RPKI ROV reject rules across all transit peering agreements."
        ),
        "ground_truth_facts": [
            "BGP route leak by AS-9110 occurred on May 19, 2026.",
            "42 IP prefixes were leaked to Frankfurt transit nodes.",
            "Packet loss reached 62% for 31 minutes.",
            "RPKI filtering resolved the leak.",
            "Zero data exfiltration due to mandatory TLS 1.3 encryption.",
        ],
        "target_outputs": ["advisory", "executive_summary", "twitter"],
    },
    # 6. Technical Article: Event-Driven Architecture with Kafka
    {
        "id": "doc_06",
        "title": "Scaling Event Streams: Kafka Tiered Storage Architecture",
        "category": "technical_article",
        "text": (
            "Apache Kafka tiered storage offloads closed topic segments to object storage like S3 or MinIO. "
            "This pattern reduces local NVMe SSD storage requirements by 70% while keeping data queryable via existing consumer APIs. "
            "In benchmarks with 5 TB daily ingestion, broker memory consumption remained stable at 18 GB. "
            "Rebalance recovery times dropped from 45 minutes to under 3 minutes because broker state is stateless. "
            "Segment compaction should be scheduled during low-traffic maintenance windows."
        ),
        "ground_truth_facts": [
            "Kafka tiered storage offloads historical segments to object storage.",
            "Reduces broker NVMe storage requirements by 70%.",
            "Broker memory stays stable at 18 GB with 5 TB daily ingestion.",
            "Partition rebalancing time dropped from 45 minutes to under 3 minutes.",
        ],
        "target_outputs": ["linkedin", "twitter"],
    },
    # 7. Security Advisory: OpenSSL Cipher Deprecation
    {
        "id": "doc_07",
        "title": "Compliance Bulletin: Mandatory Deprecation of TLS 1.0/1.1 and CBC Ciphers",
        "category": "security_advisory",
        "text": (
            "In compliance with PCI-DSS v4.0 regulations, all legacy TLS 1.0 and 1.1 ciphers will be permanently disabled on October 31, 2026. "
            "All client connections must negotiate TLS 1.2 or TLS 1.3 using ECDHE key exchange. "
            "Legacy clients using CBC ciphers or RSA key exchange will receive connection termination handshake errors. "
            "Internal telemetry indicates that 99.4% of existing client requests already negotiate modern TLS suites. "
            "Legacy client deprecation grace period ends October 15, 2026."
        ),
        "ground_truth_facts": [
            "TLS 1.0 and 1.1 permanent cutoff date is October 31, 2026.",
            "Complies with PCI-DSS v4.0 security mandate.",
            "Clients must support TLS 1.2/1.3 with ECDHE key exchange.",
            "99.4% of current clients already use modern TLS suites.",
            "Grace period expires October 15, 2026.",
        ],
        "target_outputs": ["advisory", "executive_summary"],
    },
    # 8. Executive Brief: Q3 Cybersecurity Posture Report
    {
        "id": "doc_08",
        "title": "Board Briefing: Q3 Enterprise Security Posture & SOC Metrics",
        "category": "executive_brief",
        "text": (
            "During Q3 2026, the Security Operations Center triaged 1.4 million telemetry events and thwarted 312 targeted phishing campaigns. "
            "Mean Time to Detect (MTTD) decreased from 14 minutes in Q2 to 6 minutes in Q3. "
            "Mean Time to Remediate (MTTR) reached an all-time low of 19 minutes. "
            "Employee security awareness simulations achieved a 98.7% reporting rate with zero credential submissions on simulated lures. "
            "Independent penetration testing by NCC Group produced zero critical or high severity findings across external perimeter IPs."
        ),
        "ground_truth_facts": [
            "SOC triaged 1.4 million events and stopped 312 phishing campaigns in Q3 2026.",
            "MTTD improved from 14 minutes to 6 minutes.",
            "MTTR reached 19 minutes.",
            "Employee phishing simulation reporting rate was 98.7%.",
            "Zero critical/high vulnerabilities discovered during NCC Group audit.",
        ],
        "target_outputs": ["executive_summary", "linkedin"],
    },
    # 9. Incident Report: Redis Cache Eviction Cascades
    {
        "id": "doc_09",
        "title": "Post-Mortem: Redis OOM Cache Eviction Cascade",
        "category": "incident_report",
        "text": (
            "On June 28, 2026, a misconfigured session serialization key TTL caused Redis cache memory usage to hit the 64 GB maxmemory limit. "
            "The eviction policy 'allkeys-lru' evicted critical API permission cache entries, causing 25,000 backend database queries per second. "
            "The PostgreSQL connection pool was exhausted for 11 minutes, returning HTTP 500 errors to 8% of mobile clients. "
            "Engineer on-call increased maxmemory to 96 GB and applied an emergency key expiration patch. "
            "Preventative fix: isolate authentication cache from transient session storage into dedicated Redis clusters."
        ),
        "ground_truth_facts": [
            "Redis hit 64 GB maxmemory limit on June 28, 2026 due to missing key TTL.",
            "Allkeys-lru eviction dumped auth permissions, causing 25,000 queries/sec spike on database.",
            "Database connection pool exhausted for 11 minutes affecting 8% of mobile requests.",
            "Mitigated by resizing to 96 GB and enforcing key TTL.",
            "Architectural fix: partition auth cache from session storage.",
        ],
        "target_outputs": ["advisory", "twitter", "executive_summary"],
    },
    # 10. Technical Article: Retrieval Augmented Generation (RAG) Best Practices
    {
        "id": "doc_10",
        "title": "Engineering Guide: High-Precision RAG with Sliding-Window Chunking",
        "category": "technical_article",
        "text": (
            "Naive fixed-character chunking introduces boundary truncation that degrades semantic retrieval accuracy by 22%. "
            "Adopting sliding-window token chunking with a 600-word target and 50-word overlap preserves cross-sentence context. "
            "Combining dense vector embeddings (BAAI/bge-m3) with BM25 keyword reranking improves Top-3 retrieval recall to 94.6%. "
            "Storing chunk provenance metadata (page number and section header) enables immutable fact citation tracking. "
            "Deduplicating retrieved chunks prior to LLM synthesis reduces input context costs by 31%."
        ),
        "ground_truth_facts": [
            "Fixed chunking degrades retrieval accuracy by 22%.",
            "Sliding-window chunking uses 600-word target with 50-word overlap.",
            "Dense embeddings + BM25 reranking achieves 94.6% Top-3 retrieval recall.",
            "Provenance metadata allows strict fact citation grounding.",
            "Deduplication reduces prompt token costs by 31%.",
        ],
        "target_outputs": ["linkedin", "twitter"],
    },
    # 11. Security Advisory: DNS Cache Poisoning Vulnerability
    {
        "id": "doc_11",
        "title": "Vulnerability Bulletin: CVE-2026-4402 Internal DNS Resolver Poisoning",
        "category": "security_advisory",
        "text": (
            "Security vulnerability CVE-2026-4402 identified in CoreDNS forward plugin version 1.11.0. "
            "Insufficient entropy in UDP transaction IDs enables local network adversaries to spoof DNS responses for internal microservices. "
            "Severity level is rated High (CVSS 7.9). "
            "Exploitation could redirect internal gRPC traffic to unauthorized endpoints. "
            "All Kubernetes cluster administrators must apply patch v1.11.2 or enable DNS-over-HTTPS upstream resolvers immediately."
        ),
        "ground_truth_facts": [
            "CVE-2026-4402 affects CoreDNS forward plugin version 1.11.0.",
            "Low UDP transaction ID entropy permits internal DNS spoofing.",
            "Assigned CVSS score is 7.9 (High).",
            "Patch v1.11.2 or DoH upstream configuration required immediately.",
        ],
        "target_outputs": ["advisory", "twitter"],
    },
    # 12. Executive Brief: Global SOC2 Type II Certification
    {
        "id": "doc_12",
        "title": "Compliance Milestone: Successful SOC2 Type II and ISO 27001 Re-Certification",
        "category": "executive_brief",
        "text": (
            "CloudForge completed its annual SOC2 Type II examination covering Security, Availability, and Confidentiality trust principles. "
            "Independent accounting firm Ernst & Young audited operational controls over a 12-month evaluation period with zero exceptions noted. "
            "Simultaneously, the organization achieved ISO 27001:2022 re-certification across all 4 global engineering hubs. "
            "The clean audit report unlocks enterprise contracts valued at $14.2M across regulated healthcare and finance sectors. "
            "Audit reports are available to verified enterprise partners under mutual NDA via the trust center portal."
        ),
        "ground_truth_facts": [
            "Completed SOC2 Type II audit with zero exceptions noted by Ernst & Young.",
            "12-month audit period covered Security, Availability, and Confidentiality.",
            "Achieved ISO 27001:2022 re-certification across 4 global engineering offices.",
            "Audit compliance directly unlocks $14.2M in enterprise sales pipeline.",
        ],
        "target_outputs": ["executive_summary", "linkedin"],
    },
    # 13. Technical Article: eBPF-Based Kernel Observability
    {
        "id": "doc_13",
        "title": "Deep Dive: eBPF Non-Intrusive Continuous Profiling",
        "category": "technical_article",
        "text": (
            "Traditional application performance monitoring (APM) agents introduce 3-7% CPU overhead through runtime bytecode rewriting. "
            "eBPF runs sandboxed bytecode programs directly inside the Linux kernel, capturing system calls and network metrics with less than 0.8% CPU overhead. "
            "Deploying Cilium and Pixie enabled automatic distributed tracing across 400 microservices without changing a single line of application source code. "
            "Kernel tracepoints provide packet-level visibility into TCP socket retransmissions and dropped connections. "
            "Requires Linux kernel version 5.15 or newer with BPF CO-RE enabled."
        ),
        "ground_truth_facts": [
            "Traditional APM agents consume 3-7% CPU overhead.",
            "eBPF continuous profiling consumes less than 0.8% CPU overhead.",
            "Cilium and Pixie provide distributed tracing across 400 microservices without code modifications.",
            "Requires Linux kernel 5.15+ with BPF CO-RE support.",
        ],
        "target_outputs": ["linkedin", "twitter"],
    },
    # 14. Incident Report: CI/CD Pipeline Artifact Tampering Attempt
    {
        "id": "doc_14",
        "title": "Security Incident: Thwarted Supply Chain Tampering in Build Runner",
        "category": "incident_report",
        "text": (
            "On July 2, 2026, automated cryptographic verification detected a hash mismatch in a third-party npm dependency during container image build. "
            "The malicious package version attempted to exfiltrate build environment variables to an external pastebin server. "
            "The build container's default-deny egress network policy blocked outbound socket connections immediately. "
            "Zero secrets or production keys were leaked. The compromised dependency was quarantined across internal npm mirrors within 12 minutes. "
            "Software Bill of Materials (SBOM) generation with Cosign signature validation has been made mandatory for all build artifacts."
        ),
        "ground_truth_facts": [
            "Cryptographic hash mismatch detected compromised npm dependency on July 2, 2026.",
            "Malicious package attempted environment variable exfiltration.",
            "Default-deny network egress policy blocked all outbound connections.",
            "Zero credentials or secrets were compromised.",
            "Mandated Cosign signed SBOM verification for all container builds.",
        ],
        "target_outputs": ["advisory", "executive_summary"],
    },
    # 15. Security Advisory: Deprecation of SHA-1 Signatures in Certificates
    {
        "id": "doc_15",
        "title": "Security Advisory: Total Deprecation of Legacy SHA-1 and RSA-1024 Certificates",
        "category": "security_advisory",
        "text": (
            "Effective August 1, 2026, CloudForge edge API endpoints will completely reject client certificates signed with SHA-1 hashes or RSA keys under 2048 bits. "
            "This policy aligns with NIST SP 800-131A cryptographic guidelines. "
            "Clients using non-compliant certificates will fail mutual TLS handshakes with code ERR_SSL_UNSUPPORTED_CERTIFICATE. "
            "Automated notifications have been sent to 19 enterprise partners whose client certificates expire or require re-issuance. "
            "Recommended migration: issue ECDSA P-256 or RSA-4096 certificates via our automated ACME server."
        ),
        "ground_truth_facts": [
            "Rejection of SHA-1 and sub-2048 bit RSA certificates takes effect August 1, 2026.",
            "Complies with NIST SP 800-131A cryptographic guidelines.",
            "Non-compliant clients will receive mutual TLS handshake failures.",
            "19 enterprise clients notified to re-issue certificates.",
            "Recommended standard is ECDSA P-256 or RSA-4096.",
        ],
        "target_outputs": ["advisory", "executive_summary"],
    },
    # 16. Technical Article: Database Connection Pooling with PgBouncer
    {
        "id": "doc_16",
        "title": "Database Optimization: Scaling PostgreSQL to 50,000 Concurrent Connections",
        "category": "technical_article",
        "text": (
            "Each native PostgreSQL backend process consumes approximately 10 MB of RAM, limiting max connections on a 64 GB host to around 2,000. "
            "Deploying PgBouncer in transaction pooling mode allows 50,000 client applications to share a pool of 200 persistent database connections. "
            "Connection acquisition latency dropped from 45ms to under 1.1ms per transaction. "
            "Care must be taken to avoid session-level prepared statements or advisory locks when using transaction-level pooling. "
            "PgBouncer health checks should be probed every 5 seconds with automated failover managed via Keepalived."
        ),
        "ground_truth_facts": [
            "Native PostgreSQL processes use ~10 MB RAM each, capping direct connections.",
            "PgBouncer transaction pooling enables 50,000 clients across 200 backend connections.",
            "Connection establishment latency decreased from 45ms to 1.1ms.",
            "Transaction mode requires avoiding session-level prepared statements and locks.",
            "Probing health every 5 seconds ensures high availability failover.",
        ],
        "target_outputs": ["linkedin", "twitter", "executive_summary"],
    },
]
