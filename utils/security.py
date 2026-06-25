def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(self), microphone=(self), geolocation=()"

    # Do not add strict CSP yet because SAIVEX loads some external scripts/fonts.
    # We can add a carefully tuned CSP during deployment.
    return response
