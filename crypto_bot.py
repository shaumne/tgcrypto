from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from pycoingecko import CoinGeckoAPI
from decouple import config
import asyncio
from datetime import datetime
import logging

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Config
TELEGRAM_TOKEN = config('TELEGRAM_TOKEN')
CHANNEL_ID = config('CHANNEL_ID')
UPDATE_INTERVAL = 300  # 5 minutes

# Initialize CoinGecko API
cg = CoinGeckoAPI()

# Coin configurations
COINS = {
    'bitcoin': {'symbol': 'BTC', 'tradingview': 'BTCUSDT'},
    'ethereum': {'symbol': 'ETH', 'tradingview': 'ETHUSDT'},
    'binancecoin': {'symbol': 'BNB', 'tradingview': 'BNBUSDT'},
    'ripple': {'symbol': 'XRP', 'tradingview': 'XRPUSDT'},
    'cardano': {'symbol': 'ADA', 'tradingview': 'ADAUSDT'},
    'solana': {'symbol': 'SOL', 'tradingview': 'SOLUSDT'},
    'polkadot': {'symbol': 'DOT', 'tradingview': 'DOTUSDT'},
    'dogecoin': {'symbol': 'DOGE', 'tradingview': 'DOGEUSDT'},
    'avalanche-2': {'symbol': 'AVAX', 'tradingview': 'AVAXUSDT'},
    'tron': {'symbol': 'TRX', 'tradingview': 'TRXUSDT'}
}

async def get_crypto_prices():
    """Fetch cryptocurrency prices"""
    try:
        prices = cg.get_price(
            ids=list(COINS.keys()),
            vs_currencies='usd',
            include_24hr_change=True,
            include_24hr_vol=True,
            include_market_cap=True
        )
        return prices
    except Exception as e:
        logger.error(f"Error fetching prices: {e}")
        return None

def get_chart_links(coin_name):
    """Generate chart links for a coin"""
    trading_symbol = COINS[coin_name]['tradingview']
    
    links = {
        'TradingView': f"https://www.tradingview.com/chart/?symbol=BINANCE:{trading_symbol}",
        'Binance': f"https://www.binance.com/en/trade/{trading_symbol}",
        'CoinGecko': f"https://www.coingecko.com/en/coins/{coin_name}"
    }
    
    return links

def format_price_message(prices):
    """Format the price data into a readable message"""
    message = "🚀 CRYPTO MARKET UPDATE 🚀\n\n"
    message += f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"

    for coin, data in prices.items():
        symbol = COINS[coin]['symbol']
        price = data['usd']
        change = data['usd_24h_change']
        market_cap = data['usd_market_cap']

        # Determine emoji based on price change
        emoji = "🟢" if change >= 0 else "🔴"
        
        # Get chart links
        links = get_chart_links(coin)
        
        message += f"{emoji} {symbol}\n"
        message += f"💵 Price: ${price:,.2f}\n"
        message += f"📈 24h Change: {change:.2f}%\n"
        message += f"💰 Market Cap: ${market_cap:,.0f}M\n"
        message += f"📊 Charts:\n"
        message += f"• <a href='{links['TradingView']}'>TradingView</a>\n"
        message += f"• <a href='{links['Binance']}'>Binance</a>\n"
        message += f"• <a href='{links['CoinGecko']}'>CoinGecko</a>\n\n"

    message += "\n#crypto #bitcoin #ethereum"
    return message

async def send_price_updates(context):
    """Send price updates to the channel"""
    try:
        prices = await get_crypto_prices()
        if prices:
            message = format_price_message(prices)
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True  # Prevent link previews
            )
            logger.info("Price update sent successfully")
    except Exception as e:
        logger.error(f"Error sending price update: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    await update.message.reply_text(
        "Bot is running! Price updates will be sent to the channel every 5 minutes."
    )

async def prices(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /prices command"""
    try:
        prices = await get_crypto_prices()
        if prices:
            message = format_price_message(prices)
            await update.message.reply_text(
                message, 
                parse_mode='HTML',
                disable_web_page_preview=True
            )
    except Exception as e:
        await update.message.reply_text(f"Error fetching prices: {e}")

def main():
    """Start the bot"""
    try:
        # Create application
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("prices", prices))

        # Add job for price updates
        job_queue = application.job_queue
        job_queue.run_repeating(send_price_updates, interval=UPDATE_INTERVAL, first=10)

        # Start the bot
        logger.info("Bot started successfully!")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == '__main__':
    main() 