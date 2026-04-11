# Sentinel's Journal

## 2025-05-22 - Broken Security Utility: JWT Critical Header Validator
**Vulnerability:** The security utility `src/backend/security/jwt_crit.py` was broken due to a `NameError` (`RESERVED_HEADERS` was used but not defined). This would cause the entire application to crash if it attempted to validate a JWT with a `crit` header, potentially leading to a Denial of Service (DoS) or bypassing security checks if exceptions were swallowed incorrectly elsewhere.
**Learning:** Security-critical utilities must be thoroughly tested. While the tests existed, they were failing, indicating that this utility might not have been integrated into a CI pipeline yet, or the failure was ignored.
**Prevention:** Ensure all security-related tests are part of the core test suite and enforced in CI/CD. Don't assume utility code is functional just because it's present.
