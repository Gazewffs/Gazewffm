
import asyncio
import re
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityBold, MessageEntityItalic
import logging
import json
import os
from config import API_ID, API_HASH, PHONE_NUMBER, SOURCE_CHANNEL, TARGET_CHANNEL, SESSION_NAME

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Accuracy tracking with persistence
STATS_FILE = 'daily_stats.json'

def load_daily_stats():
    """Load daily statistics from file"""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'total_signals': 0,
        'wins': 0,
        'losses': 0,
        'accuracy': 0.0,
        'start_date': datetime.now().strftime('%Y-%m-%d'),
        'last_reset': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def save_daily_stats():
    """Save daily statistics to file"""
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(accuracy_stats, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving stats: {e}")

accuracy_stats = load_daily_stats()

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

def format_daily_report():
    """Format the daily accuracy report"""
    accuracy = calculate_accuracy()
    losses = accuracy_stats.get('losses', accuracy_stats['total_signals'] - accuracy_stats['wins'])
    
    report_date = datetime.now().strftime('%Y-%m-%d')
    report_time = datetime.now().strftime('%H:%M:%S')
    
    return f"""**📊 DAILY PERFORMANCE REPORT 📊**
**🔥BILLIONAIRE BOSS🔥**

**📅 Date: {report_date}**
**🕘 Report Time: {report_time}**

**📈 TRADING STATISTICS:**
━━━━━━━━━━━━━━━━━━━━━━━━━━
**🚀 Total Signals: {accuracy_stats['total_signals']}**
**✅ Total Wins: {accuracy_stats['wins']}**
**❌ Total Losses: {losses}**
**📊 Success Rate: {accuracy}%**
━━━━━━━━━━━━━━━━━━━━━━━━━━

**🎯 PERFORMANCE ANALYSIS:**
{'🔥 EXCELLENT PERFORMANCE! 🔥' if accuracy >= 80 else '💪 GOOD PERFORMANCE! 💪' if accuracy >= 60 else '⚡ ROOM FOR IMPROVEMENT ⚡' if accuracy >= 40 else '🎯 FOCUS & STRATEGY NEEDED 🎯'}

**💎 Tomorrow is a new opportunity! 💎**
**🚀 Stay tuned for more profitable signals! 🚀**"""

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
                save_daily_stats()
                
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
                
                # Update accuracy and losses count
                accuracy_stats['accuracy'] = calculate_accuracy()
                if result_text != "WIN ✅":
                    accuracy_stats['losses'] = accuracy_stats.get('losses', 0) + 1
                
                # Save stats to file
                save_daily_stats()
                logger.info(f"Current accuracy: {accuracy_stats['accuracy']}% (Wins: {accuracy_stats['wins']}, Total: {accuracy_stats['total_signals']})")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            logger.error(f"Message content: {message_text}")

async def send_daily_report(client):
    """Send daily performance report"""
    try:
        daily_report = format_daily_report()
        await client.send_message(TARGET_CHANNEL, daily_report, parse_mode='md')
        logger.info("Daily report sent successfully!")
        
        # Reset stats for next day
        accuracy_stats.update({
            'total_signals': 0,
            'wins': 0,
            'losses': 0,
            'accuracy': 0.0,
            'last_reset': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        save_daily_stats()
        logger.info("Daily stats reset for new day")
        
    except Exception as e:
        logger.error(f"Error sending daily report: {e}")

async def schedule_daily_report(client):
    """Schedule daily report at 10 PM"""
    while True:
        try:
            now = datetime.now()
            # Set target time to 10 PM today
            target_time = now.replace(hour=22, minute=0, second=0, microsecond=0)
            
            # If it's already past 10 PM today, set target to 10 PM tomorrow
            if now >= target_time:
                target_time += timedelta(days=1)
            
            # Calculate time until next 10 PM
            time_until_report = (target_time - now).total_seconds()
            
            logger.info(f"Next daily report scheduled for: {target_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Time until report: {time_until_report/3600:.1f} hours")
            
            # Wait until 10 PM
            await asyncio.sleep(time_until_report)
            
            # Send the daily report
            await send_daily_report(client)
            
        except Exception as e:
            logger.error(f"Error in daily report scheduler: {e}")
            # Wait 1 hour before retrying if there's an error
            await asyncio.sleep(3600)

    # Start the daily report scheduler
    asyncio.create_task(schedule_daily_report(client))
    
    # Keep the client running
    logger.info("Listening for messages...")
    logger.info("Daily report scheduler started - reports will be sent at 10 PM daily")
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
    
