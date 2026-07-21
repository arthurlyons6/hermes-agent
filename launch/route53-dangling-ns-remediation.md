# Route53 Dangling NS Remediation

Domain: blackgoldrandd.com
Date: 2026-07-21

## Evidence
- `nslookup -type=ns blackgoldrandd.com` -> `Non-existent domain` from `cdns01.comcast.net`
- `dig +nocmd blackgoldrandd.com NS` -> no answer
- Claimed nameservers from registry metadata/claims: `dns.google`, `dns.google-server.net`

## Conclusion
The domain is not present in public DNS. The Route53 NS records are stale/delegated and should be removed.

## Remediation steps
1. Sign in to AWS Route53 console.
2. Open the hosted zone or delegation record set that contains `dns.google`/`dns.google-server.net` for `blackgoldrandd.com`.
3. Delete the NS record set.
4. Confirm with `nslookup -type=ns blackgoldrandd.com` after TTL expiry.
