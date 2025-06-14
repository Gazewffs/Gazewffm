
import asyncio
import re
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityBold, MessageEntityItalic
import logging
from config import API_ID, API_HASH, PHONE_NUMBER, SOURCE_CHANNEL, TARGET_CHANNEL, SESSION_NAME

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Accuracy tracking
accuracy_stats = {
    'total_signals': 0,
    'wins': 0,
    'accuracy': 0.0
}

def calculate_accuracy():
    """Calculate accuracy percentage"""
    if accuracy_stats['total_signals'] == 0:
        return 0.0
    accuracy = round((accuracy_stats['wins'] / accuracy_stats['total_signals']) * 100, 1)
    logger.info(f"Accuracy calculation: {accuracy_stats['wins']} wins / {accuracy_stats['total_signals']} total = {accuracy}%")
    return accuracy

def extract_signal_info(message_text):
    """Extract signal information from the original message"""
    # Extract pair - handle various formats
    pair_patterns = [
        r'🀄\s*([A-Z]+[-]?[A-Z]*)',  # Original format
        r'🔥\s*([A-Z]+[-]?[A-Z]*)',  # Alternative format
        r'([A-Z]{3,6}[-][A-Z]{3})',   # Direct pair format like NZDJPY-OTC
    ]
    
    pair = "UNKNOWN"
    for pattern in pair_patterns:
        pair_match = re.search(pattern, message_text)
        if pair_match:
            pair = pair_match.group(1)
            break
    
    # Extract time - handle various formats
    time_patterns = [
        r'(\d{2}:\d{2}:\d{2})\s*ENTRY TIME',
        r'🕐\s*(\d{2}:\d{2}:\d{2})\s*ENTRY TIME',
        r'(\d{2}:\d{2}:\d{2})\s*ENTRY',
        r'ENTRY TIME\s*(\d{2}:\d{2}:\d{2})',
    ]
    
    entry_time = "00:00:00"
    for pattern in time_patterns:
        time_match = re.search(pattern, message_text)
        if time_match:
            entry_time = time_match.group(1)
            break
    
    # Extract direction - handle UP/DOWN with emojis
    direction = "CALL"
    if any(indicator in message_text for indicator in ["🔴 DOWN 🔴", "DOWN 🔴", "🔴DOWN🔴", "DOWN"]):
        direction = "PUT"   # DOWN means PUT
    elif any(indicator in message_text for indicator in ["🟢 UP 🟢", "UP 🟢", "🟢UP🟢", "UP"]):
        direction = "CALL"  # UP means CALL
    
    # Calculate expiry time (1 minute later)
    if entry_time != "00:00:00":
        try:
            entry_hour, entry_min, entry_sec = map(int, entry_time.split(':'))
            expiry_min = entry_min + 1
            expiry_hour = entry_hour
            
            if expiry_min >= 60:
                expiry_min = 0
                expiry_hour += 1
                if expiry_hour >= 24:
                    expiry_hour = 0
            
            expiry_time = f"{expiry_hour:02d}:{expiry_min:02d}"
        except:
            expiry_time = "00:01"
    else:
        expiry_time = "00:01"
    
    return {
        'pair': pair,
        'entry_time': entry_time,
        'expiry_time': expiry_time,
        'direction': direction
    }

def format_signal_message(signal_info):
    """Format the signal message in the required format"""
    direction_emoji = "📈" if signal_info['direction'] == "CALL" else "📉"
    
    return f"""**🔥BILLIONAIRE BOSS🔥**

**🚀 PAIR  : {signal_info['pair']}**
**🧭 TIME : 1 M [+ 5:30 ]**

**⏳ EXPIRY : {signal_info['entry_time'][:5]} TO {signal_info['expiry_time']}** 

**⚙️DIRECTION⚙️ GO FOR {signal_info['direction']} {direction_emoji}**
              
           **🔔AUTO MTG 1🔔**"""

def format_result_message(result_text):
    """Format the result message"""
    accuracy = calculate_accuracy()
    
    return f"""**🔥BILLIONAIRE BOSS🔥**

**🚀RESULT  : - {result_text}**

**📈 ACCURACY - {accuracy}%**

**🚀 Stay tuned for the next signal!**"""

def is_signal_message(message_text):
    """Check if message is a trading signal"""
    signal_indicators = [
        "One Minute Trade",
        "1 MINT",
        "ENTRY TIME",
        "Premium Signal",
        "DOWN 🔴",
        "UP 🟢",
        "🔴 DOWN 🔴",
        "🟢 UP 🟢",
        "TIME ZONE UTC"
    ]
    
    # Check for pair indicators
    pair_indicators = [
        re.search(r'[A-Z]{3,6}[-][A-Z]{3}', message_text),  # Matches NZDJPY-OTC format
        "OTC" in message_text
    ]
    
    return (any(indicator in message_text for indicator in signal_indicators) or 
            any(pair_indicators))

def is_result_message(message_text):
    """Check if message is a result"""
    result_indicators = [
        "WIN ✅",
        "WIN✅", 
        "WIN ✓",
        "LOSS ❌",
        "LOSS❌",
        "LOSS ✗",
        "💔 Loss",
        "💔Loss",
        "Loss 💔"
    ]
    return any(indicator in message_text for indicator in result_indicators)

async def main():
    # Create the client with config values
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    # Start the client
    await client.start(phone=PHONE_NUMBER)
    
    logger.info("Bot started successfully!")
    logger.info(f"Monitoring channel: {SOURCE_CHANNEL}")
    logger.info(f"Forwarding to: {TARGET_CHANNEL}")
    
    # For private channels, we need to resolve the entity first
    try:
        source_entity = await client.get_entity(SOURCE_CHANNEL)
        logger.info(f"Successfully connected to source channel: {source_entity.title}")
    except Exception as e:
        logger.error(f"Failed to connect to source channel: {e}")
        logger.error("Make sure you have joined the private channel first")
        return
    
    @client.on(events.NewMessage(chats=source_entity))
    async def handle_new_message(event):
        try:
            message_text = event.message.message
            logger.info(f"Received message: {message_text[:100]}...")
            
            if is_signal_message(message_text):
                # Process trading signal
                signal_info = extract_signal_info(message_text)
                formatted_message = format_signal_message(signal_info)
                
                # Send to target channel with markdown formatting
                await client.send_message(TARGET_CHANNEL, formatted_message, parse_mode='md')
                logger.info(f"Signal forwarded: {signal_info['pair']} - {signal_info['direction']}")
                
                # Update stats
                accuracy_stats['total_signals'] += 1
                
            elif is_result_message(message_text):
                # Process result message
                if any(win_indicator in message_text for win_indicator in ["WIN ✅", "WIN✅", "WIN ✓"]):
                    accuracy_stats['wins'] += 1
                    result_text = "WIN ✅"
                elif any(loss_indicator in message_text for loss_indicator in ["💔 Loss", "💔Loss", "Loss 💔"]):
                    result_text = "LOSS 💔"
                else:
                    result_text = "LOSS ❌"
                
                # Only count as total signal if we haven't already counted the original signal
                # This ensures we have proper total count for accuracy
                if accuracy_stats['total_signals'] == 0:
                    accuracy_stats['total_signals'] = accuracy_stats['wins'] + 1
                
                formatted_result = format_result_message(result_text)
                
                # Send to target channel with markdown formatting
                await client.send_message(TARGET_CHANNEL, formatted_result, parse_mode='md')
                logger.info(f"Result forwarded: {result_text}")
                
                # Update accuracy
                accuracy_stats['accuracy'] = calculate_accuracy()
                logger.info(f"Current accuracy: {accuracy_stats['accuracy']}% (Wins: {accuracy_stats['wins']}, Total: {accuracy_stats['total_signals']})")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(f"Message content: {message_text}")
    
    # Keep the client running
    logger.info("Listening for messages...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
