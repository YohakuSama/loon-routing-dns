# Evidence privacy / minimization

Keep private node subscriptions, authentication URLs, access tokens, passwords, account identifiers, direct screenshots revealing personal data and raw public/private IPv4/IPv6 addresses **out** of GitHub. Do not paste full request logs into public issues.

Use aliases for device, Wi-Fi/network, node, resolver, exit and addresses. Where repeated identity matters, derive a salted local hash and keep the salt private; never publish the mapping. Avoid direct DNS resolver IPs; use resolver-a/b and annotate IPv4 vs IPv6 separately.

Trim logs to the smallest matching-rule evidence. Strip query parameters, cookies, headers, IPs, hostnames with personal account identifiers, MACs and GPS. Redact again before sharing.

`validate_device_results.py` rejects many common raw IP and secret formats but **cannot guarantee** detection of every credential, personal identifier or provider-sensitive value. Human review is mandatory.
