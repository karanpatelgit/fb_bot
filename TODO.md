Build a full-featured Facebook Messenger chatbot for a content creator 
with Hindi-speaking followers using the Groq API (free tier).

## TECH STACK
- Python 3.11+
- Flask (webhook server)
- Groq API (model: llama-3.3-70b-versatile) ← best free model for Hindi
- Facebook Messenger Platform API
- SQLite for memory/analytics
- Railway deployment

## FACEBOOK APP SETUP NEEDED
- PAGE_ACCESS_TOKEN (from Meta Developer Console)
- VERIFY_TOKEN (any secret string you choose)
- GROQ_API_KEY
- Store all in .env file

## BOT PERSONALITY
You are {creator_name}'s AI assistant. You speak naturally in 
Hinglish (Hindi + English mix) just like Indian creators do.
You are friendly, funny, and engaging like a real person.
You represent the creator's brand and values.
Never say you are an AI unless directly asked.

## CORE FEATURES TO BUILD

### 1. SMART AI CHAT (main feature)
- Full conversation with memory (last 10 messages per user)
- Responds in Hinglish by default
- Detects if user writes in English → replies in English
- Detects if user writes in pure Hindi → replies in pure Hindi
- Maintains personality across conversations
- Each user gets their own conversation history

### 2. AUTO WELCOME MESSAGE
- When someone sends first message ever → send warm welcome
- Introduce the creator and what the bot can do
- Show quick reply buttons for main features

### 3. QUICK REPLY MENU
When user sends "menu" or "help" show buttons:
- 🎬 Latest Content
- 💡 Ask Me Anything  
- 🎁 Exclusive Tips
- 📞 Contact Creator
- 🌟 About Me

### 4. CONTENT FEATURES
- /tips → send 5 random valuable tips related to creator's niche
- /quote → motivational quote in Hindi
- /joke → clean Hindi/Hinglish joke
- /fact → interesting fact

### 5. ENGAGEMENT FEATURES  
- Ask follow-up questions to keep conversation going
- Send reaction-worthy responses (use emojis naturally)
- Remember user's name if they share it
- Birthday wishes if user shares birthday

### 6. BROADCAST SYSTEM
- Admin can send message to ALL subscribers at once
- Endpoint: POST /broadcast {"message": "...", "admin_key": "..."}
- Track who is subscribed vs unsubscribed

### 7. USER MEMORY
- Remember each user's name, preferences, past topics
- Personalize responses based on history
- Store in SQLite: users table, messages table, memory table

### 8. ANALYTICS
- Track: total users, messages today, popular topics
- Admin endpoint: GET /stats

### 9. SMART RESPONSES FOR COMMON QUESTIONS
Detect these intents and respond accordingly:
- "price/cost/fees" → redirect to DM or link
- "collab/collaboration" → send collab inquiry form
- "buy/purchase" → send product/service info  
- "support/help" → send support info
- Abusive message → politely decline and redirect

### 10. HANDOFF TO HUMAN
- If user types "real person" or "human" or "creator se baat"
  → Send message: "Main {creator} ko notify kar raha hoon, 
    wo jald hi reply karenge! 🙏"
  → Send notification to creator's own Messenger

## FILE STRUCTURE
messenger_bot/
├── app.py          (main Flask app + webhook)
├── ai.py           (Groq chat logic)  
├── database.py     (SQLite operations)
├── messenger.py    (Facebook API calls)
├── handlers.py     (message routing logic)
├── config.py       (all constants)
├── requirements.txt
├── .env
└── Procfile        (for Railway)

## WEBHOOK ROUTES
- GET  /webhook  → Facebook verification
- POST /webhook  → incoming messages
- POST /broadcast → admin broadcast
- GET  /stats    → analytics dashboard

## AI SYSTEM PROMPT FOR GROQ
"You are a friendly AI assistant for [Creator Name], 
an Indian content creator. Speak in Hinglish (mix of Hindi and English) 
naturally like young Indians do. Be warm, funny, and helpful.
Keep responses SHORT (2-4 lines max) for Messenger.
Use emojis naturally. Never be formal or robotic.
If asked about creator's personal life, politely redirect.
Current conversation context: {history}"

## GROQ MODEL SELECTION
Primary: llama-3.3-70b-versatile
- Best for Hindi/Hinglish understanding
- Free on Groq
- Fast enough for real-time chat
- 32k context window

Fallback: llama-3.1-8b-instant  
- Use if 70B hits rate limit
- Faster but slightly less Hindi-capable

## RATE LIMIT HANDLING
- Add retry logic with 3 attempts
- If Groq fails → send: "Ek second... 😅 dobara try karo!"
- Cache common responses to reduce API calls

## DEPLOYMENT (Railway)
Environment variables needed:
PAGE_ACCESS_TOKEN=
VERIFY_TOKEN=
GROQ_API_KEY=
ADMIN_KEY=
CREATOR_NAME=
CREATOR_NICHE=
PORT=5000

Procfile content:
web: python app.py

## IMPORTANT NOTES
- Facebook requires HTTPS → Railway provides this automatically
- Webhook must respond within 20 seconds or Facebook retries
- Handle duplicate message_id to avoid double replies
- Log all errors but never crash the webhook
- Message length limit: 2000 chars → split long messages

Build all files completely with working code. 
Use this exact structure and make it production-ready.
