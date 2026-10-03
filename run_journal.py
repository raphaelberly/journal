from app import app

if __name__ == '__main__':

    # The dev server is plain HTTP, where browsers may not send Secure cookies back
    app.config.update(SESSION_COOKIE_SECURE=False, REMEMBER_COOKIE_SECURE=False)
    app.run('localhost', 8088, debug=True)
