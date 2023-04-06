import os
import sqlite3
import telebot
from io import BytesIO
import numpy as np
import matplotlib.pyplot as plt
bot = telebot.TeleBot(os.environ['TELEGRAM_TOKEN'])  # replace this with your own Telegram bot token

conn = sqlite3.connect('budget.db', check_same_thread=False)
cur = conn.cursor()
"""Create table 'categories' if it doesn't exist."""
cur.execute('''CREATE TABLE IF NOT EXISTS categories
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT);''')

"""Create table 'income' if it doesn't exist.
   The 'category' column is a foreign key to the 'categories' table."""
cur.execute('''CREATE TABLE IF NOT EXISTS income
                (id INTEGER PRIMARY KEY AUTOINCREMENT,amount REAL,
                category TEXT,
                FOREIGN KEY (category) REFERENCES categories (name));''')

"""Create table 'expenses' if it doesn't exist.
   The 'category' column is a foreign key to the 'categories' table."""
cur.execute('''CREATE TABLE IF NOT EXISTS expenses
                (id INTEGER PRIMARY KEY AUTOINCREMENT,amount REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                category TEXT,
                description TEXT,
                FOREIGN KEY (category) REFERENCES categories (name));''')

"""Create table 'planned_expenses' if it doesn't exist.
   The 'category' column is a foreign key to the 'categories' table."""
cur.execute('''CREATE TABLE IF NOT EXISTS planned_expenses
                (id INTEGER PRIMARY KEY AUTOINCREMENT,amount REAL,
                category TEXT,
                FOREIGN KEY (category) REFERENCES categories (name));''')

"""Create table 'planned_income' if it doesn't exist.
    The 'category' column is a foreign key to the 'categories' table."""
cur.execute('''CREATE TABLE IF NOT EXISTS planned_income
                (id INTEGER PRIMARY KEY AUTOINCREMENT,amount REAL,
                category TEXT,
                FOREIGN KEY (category) REFERENCES categories (name));''')

@bot.message_handler(commands=['start'])
def start(message):
    """Send a welcome message when the command /start is issued.
    Provides the reply keyboard.
    Keyboard buttons are handled by the respective message handlers.
    Buttons are named 'Новый доход', 'Новая трата', 'Отчёт', 'Планирование'. They trigger the following commands:
    Новый доход - add a new income entry
    Новая трата - add a new expense entry
    Отчёт - generate a report of the user's income and expenses
    Планирование - add a new planned expense or income entry
    """
    keyboard = telebot.types.ReplyKeyboardMarkup()
    keyboard.row('Новый доход', 'Новая трата')
    keyboard.row('Отчёт', 'Планирование')
    bot.reply_to(message, 'Привет, это трекинг бюджета семьи Губановых-Полтарыхиных!', reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == 'Планирование')
def planning(message):
    """Handles the 'Планирование' button click.
    Takes the user to the planning menu.
    Provides the reply keyboard.
    Keyboard buttons are handled by the respective message handlers.
    Buttons are named 'Планирование дохода' and 'Планирование трат'. They trigger the following commands:
    Планирование дохода - add a new planned income entry
    Планирование трат - add a new planned expense entry
    """
    keyboard = telebot.types.ReplyKeyboardMarkup()
    keyboard.row('Планирование дохода', 'Планирование трат')
    keyboard.row('Выйти из режима планирования')
    bot.reply_to(message, 'Выберите тип планирования:', reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == 'Планирование дохода')
def add_planned_income(message):
    """Handles the 'Планирование дохода' button click.
    The user is prompted to enter the amount of planned income and the category."""
    bot.reply_to(message, 'Введите сумму:')
    bot.register_next_step_handler(message, add_planned_income_amount)


def add_planned_income_amount(message):
    """Add a new planned income entry.
    Prompts the user to enter the category of planned income in a reply keyboard.
    Gets the categories from the table 'categories' and provides buttons named after them."""
    amount = float(message.text)
    keyboard = telebot.types.ReplyKeyboardMarkup()
    cur.execute("SELECT name FROM categories")
    categories = list(set([category[0] for category in cur.fetchall()]))
    for category in categories:
        keyboard.row(category)
    bot.reply_to(message, 'Введите категорию дохода:', reply_markup=keyboard)
    bot.register_next_step_handler(message, add_planned_income_category, amount)


def add_planned_income_category(message, amount):
    """Add a new planned income entry.
    If category is not in the table 'categories', add it.
    Insert new an entry into the table 'planned_income' with the amount and category as a foreign key.
    """
    category = message.text
    cur.execute("SELECT name FROM categories WHERE name = ?", (category,))
    if not cur.fetchone():
        cur.execute("INSERT INTO categories (name) VALUES (?)", (category,))
    cur.execute("INSERT INTO planned_income (amount, category) VALUES (?, ?)", (amount, category))
    conn.commit()
    keyboard = telebot.types.ReplyKeyboardMarkup()
    keyboard.row('Планирование дохода', 'Планирование трат')
    keyboard.row('Выйти из режима планирования')
    bot.reply_to(message, 'Планирование дохода добавлено!', reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == 'Планирование трат')
def add_planned_expense(message):
    """Handles the 'Планирование трат' button click.
    The user is prompted to enter the amount of planned expense and the category."""
    bot.reply_to(message, 'Введите сумму:', reply_markup=None)
    bot.register_next_step_handler(message, add_planned_expense_amount)


def add_planned_expense_amount(message):
    """Add a new planned expense entry.
    Prompts the user to enter the category of planned expense in a reply keyboard.
    Gets the categories from the table 'categories' and provides buttons named after them."""
    amount = float(message.text)
    keyboard = telebot.types.ReplyKeyboardMarkup()
    cur.execute("SELECT name FROM categories")
    categories = list(set([category[0] for category in cur.fetchall()]))
    for category in categories:
        keyboard.row(category)
    bot.reply_to(message, 'Введите категорию траты:', reply_markup=keyboard)
    bot.register_next_step_handler(message, add_planned_expense_category, amount)


def add_planned_expense_category(message, amount):
    """Add a new planned expense entry.
    """
    category = message.text
    cur.execute("SELECT name FROM categories WHERE name = ?", (category,))
    if not cur.fetchone():
        cur.execute("INSERT INTO categories (name) VALUES (?)", (category,))
    cur.execute("INSERT INTO planned_expenses (amount, category) VALUES (?, ?)", (amount, category))
    conn.commit()
    keyboard = telebot.types.ReplyKeyboardMarkup()
    keyboard.row('Планирование дохода', 'Планирование трат')
    keyboard.row('Выйти из режима планирования')
    bot.reply_to(message, 'Планирование траты добавлено!', reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == 'Выйти из режима планирования')
def exit_planning(message):
    """Handles the 'Выйти из режима планирования' button click.
    Takes the user to the main menu.
    Provides the reply keyboard.
    Keyboard buttons are handled by the respective message handlers.
    Buttons are named 'Доход', 'Траты', 'Планирование', 'Статистика'. They trigger the following commands:
    Доход - add a new income entry
    Траты - add a new expense entry
    Планирование - add a new planned income or expense entry
    Статистика - show the statistics
    """
    keyboard = telebot.types.ReplyKeyboardMarkup()
    keyboard.row('Доход', 'Траты')
    keyboard.row('Планирование', 'Статистика')
    bot.reply_to(message, 'Выберите действие:', reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == 'Новый доход')
def add_income(message):
    """Handles the 'Income' button click. The user is prompted to enter the amount of income.
    Prompt the user to enter the amount of income."""
    bot.reply_to(message, 'Введите сумму:', reply_markup=None)
    bot.register_next_step_handler(message, add_income_amount)


def add_income_amount(message):
    """Add a new income entry.
    The amount is passed as an argument to the function.
    Prompts the user to enter the category of income in a reply keyboard.
    Gets the categories from the database and provides buttons named after them."""
    amount = float(message.text)
    keyboard = telebot.types.ReplyKeyboardMarkup()
    cur.execute("SELECT category FROM income")
    categories = list(set([category[0] for category in cur.fetchall()]))
    for category in categories:
        keyboard.row(category)
    bot.reply_to(message, 'Введите категорию дохода:', reply_markup=keyboard)
    bot.register_next_step_handler(message, add_income_category, amount)


def add_income_category(message, amount):
    """Add a new income entry.
    """
    category = message.text
    cur.execute("SELECT name FROM categories WHERE name = ?", (category,))
    if not cur.fetchone():
        cur.execute("INSERT INTO categories (name) VALUES (?)", (category,))
    cur.execute("INSERT INTO income (amount, category) VALUES (?, ?)", (amount, category))
    conn.commit()
    keyboard = telebot.types.ReplyKeyboardMarkup()
    keyboard.row('Новый доход', 'Новая трата')
    keyboard.row('Отчёт', 'Планирование')
    bot.reply_to(message, f'Доход {amount} в категории {category} сохранён.', reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == 'Новая трата')
def add_expense(message):
    """Handles the 'Expense' button click.
    The user is prompted to enter the amount of expense and the category."""
    bot.reply_to(message, 'Введите сумму:')
    bot.register_next_step_handler(message, add_expense_amount)


def add_expense_amount(message):
    """Add a new expense entry.
    Prompts the user to enter the category of expense in a reply keyboard.
    Gets the categories from the database and provides buttons named after them."""
    amount = float(message.text)
    keyboard = telebot.types.ReplyKeyboardMarkup()
    cur.execute("SELECT category FROM expenses")
    categories = list(set([category[0] for category in cur.fetchall()]))
    for category in categories:
        keyboard.row(category)
    bot.reply_to(message, 'Введите категорию траты:', reply_markup=keyboard)
    bot.register_next_step_handler(message, add_expense_category, amount)


def add_expense_category(message, amount):
    """Add a new expense entry.
    """
    category = message.text
    cur.execute("SELECT name FROM categories WHERE name = ?", (category,))
    if not cur.fetchone():
        cur.execute("INSERT INTO categories (name) VALUES (?)", (category,))
    keyboard = telebot.types.ReplyKeyboardMarkup()
    cur.execute("SELECT description FROM expenses WHERE category = ?", (category,))
    descriptions = list(set([description[0] for description in cur.fetchall()]))
    for description in descriptions:
        keyboard.row(description)
    bot.reply_to(message, 'Введите описание траты:', reply_markup=keyboard)
    bot.register_next_step_handler(message, add_expense_description, amount, category)


def add_expense_description(message, amount, category):
    """Add a new expense entry.
    """
    description = message.text
    cur.execute("INSERT INTO expenses (amount, category, description) VALUES (?, ?, ?)", (amount, category, description))
    conn.commit()
    keyboard = telebot.types.ReplyKeyboardMarkup()
    keyboard.row('Новый доход', 'Новая трата')
    keyboard.row('Отчёт', 'Планирование')
    bot.reply_to(message, f'Трата {amount} в категории {category} добавлена.', reply_markup=keyboard)


@bot.message_handler(func=lambda message: message.text == 'Отчёт' or message.text == 'Статистика')
def report(message):
    """Generate a report of the user's income and expenses."""
    cur.execute("SELECT category, SUM(amount) FROM income GROUP BY category")
    income = dict(cur.fetchall())
    income_total = sum(income.values())
    cur.execute("SELECT category, SUM(amount) FROM planned_income GROUP BY category")
    planned_income = dict(cur.fetchall())
    cur.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    expenses = dict(cur.fetchall())
    cur.execute("SELECT category, SUM(amount) FROM planned_expenses GROUP BY category")
    planned_expenses = dict(cur.fetchall())
    report_text = f'Общий доход составил {int(income_total)}.\n\n'
    report_text += 'Траты по категориям:\n'
    for category, amount in expenses.items():
        report_text += f'{category}: {int(amount)}\n'
    report_text += '\n'
    report_text += f'Остаток: {int(income_total) - int(sum(expenses.values()))}'
    keyboard = telebot.types.ReplyKeyboardMarkup()
    keyboard.row('Новый доход', 'Новая трата')
    keyboard.row('Отчёт', 'Планирование')
    pastel_green = '#77DD77'
    pastel_red = '#FF6961'
    pastel_blue = '#AEC6CF'
    """
    For each category, plot a stacked bar chart with the planned and actual expenses.
    They are plotted on one plot, horisontally.
    """
    fig, ax = plt.subplots()
    # Set the width of the bars
    bar_width = 0.35
    # Clean data (if there are no expenses in a category, set the value to 0)
    for category in planned_expenses.keys():
        if category not in expenses.keys():
            expenses[category] = 0

    planned_values = []
    values = []
    for category in expenses.keys():
        planned_values.append(planned_expenses[category])
        values.append(expenses[category])
    # Set the position of the bars on the x-axis
    r1 = np.arange(len(expenses))
    r2 = [x + bar_width for x in r1]
    # Make the plot
    plt.barh(r2, planned_values, color=pastel_blue, height=bar_width, edgecolor='white', label='Планируемые траты')
    plt.barh(r2, values, color=pastel_green, height=bar_width, edgecolor='white', label='Траты')
    # Add xticks in the middle of the group bars
    plt.yticks([r + bar_width for r in range(len(expenses))], expenses.keys())
    # Create legend & Show graphic
    plt.legend()
    plt.title('Траты по категориям')
    # Tight layout
    plt.tight_layout()
    bar_file = BytesIO()
    plt.savefig(bar_file, format='png')
    bar_file.seek(0)
    plt.close()


    # Create a pie diagram for expenses categories
    cur.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    expenses = dict(cur.fetchall())
    pastel_colors = ['#F9A7B0', '#D8BFD8', '#C3E6CB', '#F0E68C', '#B0C4DE', '#FFB347', '#C6E2FF', '#E0BBE4', '#B19CD9',
                     '#FFD1DC']

    plt.pie(expenses.values(),
            labels=expenses.keys(),
            colors=pastel_colors,
            autopct='%1.1f%%',
            shadow=True,
            startangle=90)
    plt.title('Категории трат')
    plt.tight_layout()
    pie_file = BytesIO()
    plt.savefig(pie_file, format='png')
    pie_file.seek(0)
    bot.send_media_group(message.chat.id, [telebot.types.InputMediaPhoto(pie_file),
                                           telebot.types.InputMediaPhoto(bar_file)])
    bot.reply_to(message, report_text, reply_markup=keyboard)


bot.infinity_polling()
