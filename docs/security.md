---
title: Security
description: Supported security reporting and the package's provider boundary.
---

# Security

Please report suspected vulnerabilities privately through the repository's
[security advisory form](https://github.com/jbcom/meshy-content-generator/security/advisories/new),
not through a public issue. Include affected versions, a minimal reproduction,
impact, and any mitigation already known.

Do not include API keys, access tokens, customer data, or paid-generation
artifacts in a report.

## Scope

This package does not own Meshy credentials or HTTP transport. Provider-auth,
network, retry, polling, download, and vendor-error issues belong in
`vendor-fabric`; pipeline parsing and ImageMagick transformation issues belong
here. We will coordinate across the boundary when an issue affects both.
