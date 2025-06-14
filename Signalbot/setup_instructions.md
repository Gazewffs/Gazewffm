
# Telegram Bot Setup Instructions

## Step 1: Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Login with your phone number
3. Click "Create application"
4. Fill in the required details:
   - App title: Your bot name
   - Short name: A short name for your app
   - Platform: Choose appropriate platform
5. Save the `API_ID` and `API_HASH`

## Step 2: Configure the Bot

1. Open `config.py` and replace the placeholder values:
   - `API_ID`: Your API ID from step 1
   - `API_HASH`: Your API Hash from step 1
   - `PHONE_NUMBER`: Your phone number with country code (e.g., +1234567890)
   - `SOURCE_CHANNEL`: Username of the private channel to monitor
   - `TARGET_CHANNEL`: Username of the channel to forward messages to

## Step 3: Install Dependencies

The bot will automatically install required packages when you run it.

## Step 4: Run the Bot

1. Click the "Run" button in Replit
2. The first time you run it, you'll need to enter the verification code sent to your phone
3. The bot will start monitoring the source channel and forwarding formatted messages

## Features

- **Signal Forwarding**: Converts trading signals to the specified format
- **Result Tracking**: Tracks WIN/LOSS results and calculates accuracy
- **Real-time Processing**: Instantly forwards messages as they arrive
- **Accuracy Calculation**: Maintains running accuracy percentage

## Message Format Changes

**Original Signal** → **Formatted Signal**:
- Changes header to "🔥BILLIONAIRE BOSS🔥"
- Extracts pair and time information
- Formats direction as CALL/PUT
- Adds expiry time calculation

**Original Result** → **Formatted Result**:
- Maintains "🔥BILLIONAIRE BOSS🔥" header
- Shows result (WIN ✅ or LOSS ❌)
- Displays current accuracy percentage
- Adds motivational closing message
