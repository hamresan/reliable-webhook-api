# Webhook signature

Webhook requests use a provider-neutral HMAC-SHA256 signature.

## Format

The sender computes the lowercase hexadecimal HMAC-SHA256 digest of the **exact HTTP request body bytes** using the shared secret and sends the 64-character digest in the configured signature header.

Default local header:

```text
X-Webhook-Signature
```

Conceptually:

```text
signature = hex(HMAC-SHA256(secret, exact_request_body_bytes))
```

Do not parse and re-serialize JSON before signing. Whitespace and byte-level differences change the digest.

## Example

With `APP_WEBHOOK_SECRET=replace-with-local-secret`, a shell sender can calculate a signature with:

```bash
SIGNATURE=$(printf '%s' "$PAYLOAD" \
  | openssl dgst -sha256 -hmac 'replace-with-local-secret' -hex \
  | awk '{print $2}')
```

The API performs constant-time digest comparison. Missing, malformed, or invalid signatures return `401 Unauthorized`. Secrets and signatures are not echoed in API responses or request logs.

The shared-secret examples in this repository are local demonstration values only. Use secret management appropriate to the deployment environment for real credentials.
