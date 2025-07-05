
#!/usr/bin/env python3
"""
Startet das Web-Interface für die Bot-Konfiguration
"""

import os
import sys
from web_config import app

if __name__ == '__main__':
    print("🌐 Starte Web-Interface für Bot-Konfiguration...")
    print("📍 URL: http://0.0.0.0:5000")
    print("🔑 Standard-Passwort: admin (kann über ADMIN_PASSWORD Umgebungsvariable geändert werden)")
    print("🔐 Flask Secret Key kann über FLASK_SECRET_KEY Umgebungsvariable gesetzt werden")
    print("\n" + "="*50)
    
    # Setze Standard-Umgebungsvariablen falls nicht vorhanden
    if not os.environ.get('ADMIN_PASSWORD'):
        os.environ['ADMIN_PASSWORD'] = 'admin'
        print("⚠️  Verwende Standard-Passwort. Setze ADMIN_PASSWORD für Sicherheit!")
    
    if not os.environ.get('FLASK_SECRET_KEY'):
        os.environ['FLASK_SECRET_KEY'] = 'your-secret-key-change-this-in-production'
        print("⚠️  Verwende Standard Secret Key. Setze FLASK_SECRET_KEY für Sicherheit!")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
