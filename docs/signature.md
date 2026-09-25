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

With the local development secret from `.env.example`, a shell sender can calculate a signature with:

```bash
SIGNATURE=$(printf '%s' "$PAYLOAD" \
  | openssl dgst -sha256 -hmac 'dev-webhook-secret-9f4c2a7e81b653d0' -hex \
  | awk '{print $2}')
```

The API performs constant-time digest comparison. Missing, malformed, or invalid signatures return `401 Unauthorized`. Secrets and signatures are not echoed in API responses or request logs.

## Testing from Swagger UI

When `APP_ENVIRONMENT=development`, the Swagger UI at `/docs` can execute `POST /webhooks/events` without manually calculating the signature.

For webhook requests started from Swagger UI, development tooling signs the exact outgoing request body on the backend and injects the resulting `X-Webhook-Signature` header before the webhook request is sent. The configured webhook secret is not embedded in or returned to browser JavaScript.

The development signing endpoint is excluded from OpenAPI and is not registered when the application runs with `APP_ENVIRONMENT=production`. It is development tooling only and is not part of the public webhook API contract.

The shared-secret examples in this repository are local demonstration values only. Use secret management appropriate to the deployment environment for real credentials.
