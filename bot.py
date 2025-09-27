import asyncio
import logging
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Set
from collections import defaultdict
from aiogram.filters import Command
from aiogram import Bot, Dispatcher, F, types
from aiogram.types import Message, ChatPermissions,ChatMemberUpdated
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from config import (
    BOT_TOKEN, FORBIDDEN_WORDS, PUNISHMENT_DURATIONS, 
    VIOLATION_WINDOW, BLOCKED_MESSAGE_TEMPLATE, GROUP_NOTIFICATION_TEMPLATE, format_duration
)

# Configure logging
def setup_logging():
    """Logging konfiguratsiyasini sozlash"""
    
    # Log papkasi yaratish
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Log fayl nomi (bugungi sana bilan)
    log_filename = os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y-%m-%d')}.txt")
    
    # Root logger sozlash
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Mavjud handlerlarni tozalash
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # File handler - barcha INFO va yuqori loglar uchun
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler - faqat ERROR va yuqori loglar uchun
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Handlerlarni root loggerga qo'shish
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return log_filename

# Logging sozlash
log_file = setup_logging()
logger = logging.getLogger(__name__)

# Bot boshlanganda log fayl haqida xabar
print(f"Bot ishga tushdi. Loglar quyidagi faylga yozilmoqda: {log_file}")

# Initialize bot and dispatcher
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is required")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class ModerationBot:
    """Main moderation bot class"""
    
    def __init__(self):
        self.forbidden_words = [word.lower() for word in FORBIDDEN_WORDS]
        # Store user violations: user_id -> list of timestamps
        self.user_violations = defaultdict(list)
        # Store admin notification messages for delayed deletion: user_id -> (message_id, chat_id, duration)
        self.admin_notifications = {}
    
    def clean_old_violations(self, user_id: int) -> None:
        """Remove violations older than 24 hours"""
        current_time = time.time()
        self.user_violations[user_id] = [
            timestamp for timestamp in self.user_violations[user_id]
            if current_time - timestamp < VIOLATION_WINDOW
        ]
    
    def get_violation_count(self, user_id: int) -> int:
        """Get current violation count for user in last 24 hours"""
        self.clean_old_violations(user_id)
        return len(self.user_violations[user_id])
    
    def add_violation(self, user_id: int) -> int:
        """Add new violation and return total count"""
        current_time = time.time()
        self.user_violations[user_id].append(current_time)
        return self.get_violation_count(user_id)
    
    def get_punishment_duration(self, violation_count: int) -> int:
        """Get punishment duration based on violation count"""
        if violation_count <= len(PUNISHMENT_DURATIONS):
            return PUNISHMENT_DURATIONS.get(violation_count, PUNISHMENT_DURATIONS[max(PUNISHMENT_DURATIONS.keys())])
        else:
            # After max violations, always use the last duration
            return PUNISHMENT_DURATIONS[max(PUNISHMENT_DURATIONS.keys())]
    
    def contains_forbidden_word(self, text: str) -> tuple:
        """Check if text contains any forbidden words. Returns (is_forbidden, word)"""
        if not text:
            return False, None
        
        text_lower = text.lower()
        for word in self.forbidden_words:
            if word in text_lower:
                return True, word
        return False, None
    
    async def restrict_user(self, chat_id: int, user_id: int, duration: int) -> bool:
        """Restrict user from sending messages for specified duration"""
        try:
            if duration == -1:  # -1 → guruhdan chiqarish
                await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)
                logger.info(f"User {user_id} banned from chat {chat_id}")
                return True

            # Vaqtinchalik bloklash
            permissions = ChatPermissions(
                can_send_messages=False,
                can_send_audios=False,
                can_send_documents=False,
                can_send_photos=False,
                can_send_videos=False,
                can_send_video_notes=False,
                can_send_voice_notes=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )

            until_date = datetime.now() + timedelta(seconds=duration)

            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=permissions,
                until_date=until_date
            )

            logger.info(f"User {user_id} restricted in chat {chat_id} for {duration} seconds")
            return True

        except Exception as e:
            logger.error(f"Failed to restrict/ban user {user_id} in chat {chat_id}: {e}")
            return False

    async def send_private_warning(self, user_id: int, word: str, duration: int, violation_count: int) -> bool:
        """Send private warning message to user"""
        try:
            message = BLOCKED_MESSAGE_TEMPLATE.format(
                word=word,
                duration=format_duration(duration),
                count=violation_count
            )
            
            await bot.send_message(
                chat_id=user_id,
                text=message
            )
            logger.info(f"Warning sent to user {user_id} for word '{word}', violation #{violation_count}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send warning to user {user_id}: {e}")
            return False
    
    async def send_group_notification(self, chat_id: int, user_id: int, user_name: str, word: str, duration: int, violation_count: int) -> None:
        """Send notification to group about user restriction"""
        try:
            message = GROUP_NOTIFICATION_TEMPLATE.format(
                user_name=user_name,
                user_id=user_id,
                word=word,
                duration=format_duration(duration),
                count=violation_count
            )
            
            # Send notification to group
            notification_msg = await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown"
            )
            
            logger.info(f"Group notification sent for user {user_name} (#{user_id}) - word: '{word}', violation #{violation_count}")
            
            # Store message info for delayed deletion when user is unblocked
            self.admin_notifications[user_id] = {
                'message_id': notification_msg.message_id,
                'chat_id': chat_id,
                'duration': duration,
                'start_time': time.time()
            }
            
            # Schedule deletion after restriction ends
            asyncio.create_task(self.delete_group_notification_after_unblock(user_id, duration))
                
        except Exception as e:
            logger.error(f"Failed to send group notification: {e}")
    
    async def delete_group_notification_after_unblock(self, user_id: int, duration: int) -> None:
        """Delete group notification message after user is unblocked"""
        try:
            # Wait for the restriction duration
            await asyncio.sleep(duration)
            
            # Check if we have stored notification for this user
            if user_id in self.admin_notifications:
                notification_data = self.admin_notifications[user_id]
                
                # Delete the stored message
                try:
                    await bot.delete_message(
                        chat_id=notification_data['chat_id'], 
                        message_id=notification_data['message_id']
                    )
                    logger.info(f"Deleted group notification message for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to delete group notification for user {user_id}: {e}")
                
                # Remove from storage
                del self.admin_notifications[user_id]
                logger.info(f"Cleaned up notification for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to delete group notification for user {user_id}: {e}")


# Initialize moderation bot
moderation_bot = ModerationBot()

# Required channels (tuzatildi)
REQUIRED_CHANNELS = [
    "@QwenChattBot",
    "@zumradchi",
    "@Lightuz"
]

# Channel names (yozish ixtiyoriy)
CHANNEL_NAMES = {
    "@QwenChattBot": "1-Kanal",
    "@zumradchi": "2-Kanal",
    "@Lightuz": "3-Kanal"
}

async def check_user_subscription(user_id: int) -> dict:
    """
    Foydalanuvchi kanallarga obuna bo'lishini tekshirish
    """
    not_subscribed = []

    for channel in REQUIRED_CHANNELS:  # RUQUIRED_CHANNELS o'rniga REQUIRED_CHANNELS
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                not_subscribed.append(channel)
        except Exception as e:
            logging.error(f"Kanal {channel} uchun xatolik: {e}")
            not_subscribed.append(channel)
    return {
        'is_subscribed': len(not_subscribed) == 0,
        'not_subscribed_channels': not_subscribed,
    }

def create_subscription_keyboard() -> InlineKeyboardMarkup:
    """
    Obuna bo'lish uchun klaviatura
    """
    builder = InlineKeyboardBuilder()

    # Har bir kanal uchun tugma qo'shish
    for channel in REQUIRED_CHANNELS:  # RUQUIRED_CHANNELS o'rniga REQUIRED_CHANNELS
        channel_name = CHANNEL_NAMES.get(channel, f"Kanal {channel}")
        if str(channel).startswith('@'):
            channel_link = f"https://t.me/{channel[1:]}"
        else:
            channel_link = f"https://t.me/dn8eed7gd788djdsx"

        builder.add(InlineKeyboardButton(
            text=f"📢{channel_name}",
            url=channel_link
        ))
    builder.adjust(1)

    builder.row(InlineKeyboardButton(
        text="✅ Tekshirish",
        callback_data="check_subscription"
    ))

    return builder.as_markup()


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    subscription_status = await check_user_subscription(user_id)

    if subscription_status['is_subscribed']:
        await message.answer(
            f"Xush kelibsiz! {message.from_user.full_name}!\n\n"
            "Siz barcha kerakli kanallarga obuna bo'ldingiz!\nbot to'liq ishlayapti! 🚀 \nendi botni guruhga qo'shing va admin qiling!"
        )
        logger.info(f"User {user_id} ({message.from_user.full_name}) started bot - already subscribed")
    else:
        await message.answer(
            f"Assalomu alaykum, {message.from_user.full_name}!\n\n"
            "Botdan foydalanish uchun quyidagi kanallarga obuna bo'lishingiz kerak: ",
            reply_markup=create_subscription_keyboard()
        )
        logger.info(f"User {user_id} ({message.from_user.full_name}) started bot - not subscribed")


# Group message handlers should come before the general message handler
@dp.message(F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]))
async def handle_group_message(message: Message):
    """Handle messages in groups and supergroups"""
    
    # First handle join/leave messages
    try:
        if message.new_chat_members:
            await message.delete()
            logger.info(f"Guruh {message.chat.id} da qo'shilish xabari o'chirildi!")
            return

        # Agar kimdir guruhdan chiqib ketgan bo'lsa yoki chiqib ketsa:
        elif message.left_chat_member:
            await message.delete()
            logger.info(f"Guruh {message.chat.id} da chiqib ketish xabari o'chirildi!")
            return
    except Exception as e:
        logger.error(f"Xabarni o'chirishda xatolik yuzaga keldi: {e}")
    
    # Check for forwarded messages
    if message.forward_origin is not None:
        try:
            await message.delete()
            await message.reply("Xabarni tashqaridan guruhga uzatish taqiqlanadi!")
            logger.info(f"Forwarded message deleted from {message.chat.id}")
        except Exception as e:
            logger.error(f"Xabarni o'chirishda xatolik yuz berdi: {e}")
        return
    
    # Skip if no text content
    if not message.text:
        return
    
    # Check for forbidden words
    is_forbidden, forbidden_word = moderation_bot.contains_forbidden_word(message.text)
    if is_forbidden:
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # Get user display name
        user_name = message.from_user.full_name or message.from_user.username or f"User {user_id}"
        
        # Add violation and get count
        violation_count = moderation_bot.add_violation(user_id)
        duration = moderation_bot.get_punishment_duration(violation_count)
        
        logger.info(f"Forbidden word '{forbidden_word}' detected from user {user_name} ({user_id}) in chat {chat_id}. Violation #{violation_count}")

        # Try to delete the offensive message
        try:
            await message.delete()
            logger.info(f"Deleted message from user {user_name}")
        except Exception as e:
            logger.error(f"Failed to delete message: {e}")
        
        # Restrict the user
        restriction_success = await moderation_bot.restrict_user(chat_id, user_id, duration)
        
        if restriction_success:
            # Send group notification (in background task)
            asyncio.create_task(
                moderation_bot.send_group_notification(chat_id, user_id, user_name, forbidden_word, duration, violation_count)
            )
            
            # Send private warning (in background)
            asyncio.create_task(
                moderation_bot.send_private_warning(user_id, forbidden_word, duration, violation_count)
            )


@dp.message(F.chat.type == ChatType.PRIVATE)
async def handle_private_message(message: Message):
    """Handle private messages - check subscription first"""
    user_id = message.from_user.id
    subscription_status = await check_user_subscription(user_id)
    
    if not subscription_status['is_subscribed']:
        await message.answer(
            "🔒 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling!",
            reply_markup=create_subscription_keyboard()
        )
        logger.info(f"User {user_id} tried to use bot without subscription")
        return
    
    # If subscribed, handle the message
    if message.text and message.text.startswith('/start'):
        return  # /start command is handled separately
    
    await message.answer(
        f"👍 Xabaringiz qabul qilindi!\n\n"
        f"Siz yozdingiz: {message.text}\n\n"
        "Bot to'liq ishlayapti! 🚀"
    )
    logger.info(f"Message processed from subscribed user {user_id}: {message.text[:50]}...")


@dp.chat_member()
async def chat_member_handler(chat_member: ChatMemberUpdated):
    """Chat member o'zgarishlari uchun handler (qo'shimcha)"""
    try:
        old_status = chat_member.old_chat_member.status
        new_status = chat_member.new_chat_member.status

        # Agar kimdir yangi qo'shilgan bo'lsa
        if old_status in ['left', 'kicked'] and new_status in ['member', 'administrator', 'creator']:
            logger.info(f"Yangi a'zo qo'shildi: {chat_member.new_chat_member.user.full_name}")

        # Agar kimdir guruhdan chiqib ketgan bo'lsa
        elif old_status in ['member', 'administrator'] and new_status in ['left', 'kicked']:
            logger.info(f"Guruhdan a'zo chiqib ketdi: {chat_member.new_chat_member.user.full_name}")

    except Exception as e:
        logger.info(f"Chat member handlerda xatolik: {e}")


@dp.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback_query: CallbackQuery):
    """
    Obuna tekshirish tugmasi bosilganda
    """
    user_id = callback_query.from_user.id
    subscription_status = await check_user_subscription(user_id)

    if subscription_status['is_subscribed']:
        await callback_query.message.answer(
            f"Tabriklaymiz! {callback_query.from_user.full_name}!\n\n"
            "Siz barcha kerakli kanallarga obuna bo'ldingiz!"
        )
        await callback_query.answer("✅ Obuna tasdiqlandi")
        logger.info(f"User {user_id} subscription confirmed")
    else:
        not_subscribed_names = []
        for channel in subscription_status['not_subscribed_channels']:
            name = CHANNEL_NAMES.get(channel, f"Kanal {channel}")
            not_subscribed_names.append(f"...{name}")
        await callback_query.answer(
            f"❌ Quyidagi kanallarga obuna bo'lmadingiz: \n" +
            "\n".join(not_subscribed_names),
            show_alert=True
        )
        logger.info(f"User {user_id} subscription check failed")


async def main():
    """Main function to start the bot"""
    logger.info("Starting Telegram Moderation Bot...")
    print("Bot ishga tushmoqda...")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot stopped with error: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())