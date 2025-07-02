import os
from dotenv import load_dotenv

# Charger le .env
load_dotenv()

# Tester la variable
google_key = os.getenv('GOOGLE_GEOCODE_KEY')
print(f"Google API Key: {google_key}")

if google_key:
    print("✅ Configuration OK!")
else:
    print("❌ Clé non trouvée")
