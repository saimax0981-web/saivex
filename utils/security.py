def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(self), microphone=(self), geolocation=()"

    # Do not add a strict CSP yet because SAIVEX currently loads external fonts/scripts
    # and uses browser features like camera/microphone. We can tune CSP after deployment.
    return response
