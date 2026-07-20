import os
# These will be empty if not set in environment variables. 
# Railway will provide the real values via environment variables.
API_ID = os.environ.get("32848098")
API_HASH = os.environ.get("25aed111e2313d498327da54a4f63f55")
BOT_TOKEN = os.environ.get("8951489248:AAH3h6MPTlLBK4Zd-xvqDMZINTc-RNRcXLw")
CHANNEL_ID = os.environ.get("-1003869963264")

# Optional: Check if running locally and warn if missing
if not API_ID or not API_HASH or not BOT_TOKEN or not CHANNEL_ID:
    print("WARNING: Missing environment variables. If running locally, set them in your terminal or .env file.")
    # For local testing, you can uncomment and fill these in, BUT NEVER COMMIT THIS FILE WITH REAL KELS!
    # API_ID = 123456
    # API_HASH = "your_hash"
    # BOT_TOKEN = "your_bot_token"
    # CHANNEL_ID = "-1001234567890"
