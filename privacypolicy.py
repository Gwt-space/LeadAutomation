@app.route('/privacy')
def privacy():
    return """
    <html>
        <head><title>Privacy Policy</title></head>
        <body>
            <h1>Privacy Policy</h1>
            <p>This app collects lead data (name, email, phone) from Meta Lead Ads and sends WhatsApp notifications.</p>
            <p>Data is not shared or stored beyond the immediate usage for communication.</p>
            <p>Contact us for concerns: example@example.com</p>
        </body>
    </html>
    """
