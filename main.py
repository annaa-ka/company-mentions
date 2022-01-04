import logging
import os

from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Update,
)
from telegram.bot import Bot, BotCommand
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    DispatcherHandlerStop,
    Filters,
    InlineQueryHandler,
    MessageHandler,
    PicklePersistence,
    TypeHandler,
    Updater,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

load_dotenv()
botToken = os.environ.get('TELEGRAM_BOT_TOKEN')
updater = Updater(token=botToken, use_context=True)
dispatcher = updater.dispatcher

set_with_company_names = set()


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Hi! \n\n"
                                  "This bot can help you to stay informed with the latest "
                                  "news about the companies that you are interested in. "
                                  "We will monitor the articles, send you the link and give a sentiment analysis. \n\n"
                                  "The command /cancel is to stop the conversation.")

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Please, type the company names using comma. Here is the example \n\n"
                                  "Google, Яндекс, Газпром")
    return PARSING_NAMES_OF_COMPANIES


def parsing_names(update, context):
    global set_with_company_names
    string_with_names = update.message.text
    set_with_company_names = set(string_with_names.split(','))
    my_companies(update, context)
    return ConversationHandler.END


def cancel(update, context):
    update.message.reply_text(
        "The process is stopped. If you want to restart, use /start"
    )
    return ConversationHandler.END


PARSING_NAMES_OF_COMPANIES = range(1)
getting_names_of_companies_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        PARSING_NAMES_OF_COMPANIES: [
            MessageHandler(Filters.text & (~Filters.command), parsing_names)
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True,
)
dispatcher.add_handler(getting_names_of_companies_handler)

command = [
    BotCommand("start", "to start work"),
    BotCommand("add_companies", "add new companies"),
    BotCommand("my_companies", "view the list of my companies"),
    BotCommand("delete_companies", "delete company from the list"),
    BotCommand("clean_list", "delete all companies from the list")
]
bot = Bot(botToken)
bot.set_my_commands(command)


def my_companies(update, context):
    global set_with_company_names
    if len(set_with_company_names) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Your list is empty, "
                                                                        "use /add_companies to add new one.")
        return ConversationHandler.END
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="These are your companies:")
        company_list = str()
        for item in set_with_company_names:
            company_list += (item + "\n")
        context.bot.send_message(chat_id=update.effective_chat.id, text=company_list)
        return ConversationHandler.END


show_company_handler = CommandHandler('my_companies', my_companies)
dispatcher.add_handler(show_company_handler)


def add_companies(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Enter names of the new companies.")
    return GETTING_NAMES_OF_NEW_COMPANIES


def new_companies_adding(update, context):
    global set_with_company_names
    string_with_new_companies = update.message.text
    set_with_new_company_names = set(string_with_new_companies.split(','))
    set_with_company_names = set.union(set_with_company_names, set_with_new_company_names)
    return ConversationHandler.END


GETTING_NAMES_OF_NEW_COMPANIES = range(1)
add_company_handler = ConversationHandler(
    entry_points=[CommandHandler("add_companies", add_companies)],
    states={
        GETTING_NAMES_OF_NEW_COMPANIES: [
            MessageHandler(Filters.text & (~Filters.command), new_companies_adding)
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True,
)
dispatcher.add_handler(add_company_handler)


def delete_companies(update, context):
    global set_with_company_names
    if len(set_with_company_names) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Your list is empty, "
                                                                        "use /add_companies to add new one.")
        return ConversationHandler.END
    else:
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text="Please, type the company names using comma. Here is the example \n\n"
                                      "Google, Яндекс, Газпром")
        return GETTING_NAMES_OF_DELETING_COMPANIES


def deleting_companies(update, context):
    global set_with_company_names
    array_with_companies_to_delete = set(update.message.text.split(','))
    for item in array_with_companies_to_delete:
        if item in set_with_company_names:
            set_with_company_names.remove(item)
    return ConversationHandler.END



GETTING_NAMES_OF_DELETING_COMPANIES = range(1)
delete_companies_handler = ConversationHandler(
    entry_points=[CommandHandler('delete_companies', delete_companies)],
    states={
        GETTING_NAMES_OF_DELETING_COMPANIES: [
            MessageHandler(Filters.text & (~Filters.command), deleting_companies)
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    allow_reentry=True,
)
dispatcher.add_handler(delete_companies_handler)


def clean_list(update, context):
    global set_with_company_names
    if len(set_with_company_names) == 0:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Your list is empty, "
                                                                        "use /add_companies to add new one.")
        return ConversationHandler.END
    else:
        set_with_company_names.clear()
        context.bot.send_message(chat_id=update.effective_chat.id, text="Now your list is empty, "
                                                                        "use /add_companies to add new one.")
        return ConversationHandler.END


clean_list_handler = CommandHandler('clean_list', clean_list)
dispatcher.add_handler(clean_list_handler)

def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command.")


unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)

updater.start_polling()

