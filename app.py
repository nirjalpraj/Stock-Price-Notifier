import yfinance as yf
import sqlite3
from flask import Flask, request, render_template
from apscheduler.schedulers.background import BackgroundScheduler
import smtplib
from flask_cors import CORS, cross_origin
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
# Connect to the database
conn = sqlite3.connect('notifications.db',check_same_thread=False)
cursor = conn.cursor()

# Create the notifications table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications1 (
        ticker TEXT,
        threshold REAL,
        email TEXT,
        phone INTEGER,
        frequency INTEGER,
        notification_type TEXT
    )
''')
conn.commit()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ticker = request.form['ticker']
        threshold = request.form['threshold']
        day = request.form['day']
        hour = request.form['hour']
        minute = request.form['minute']
        notification_type = request.form['notification_type']
        email = request.form['email_address']
        phone = request.form['phone']
        
        frequency = int(day)*24*60 + int(hour)*60 + int(minute) 

        # Save the notification settings to the database
        cursor.execute('''
            INSERT INTO notifications1 (ticker, threshold, email, phone, frequency, notification_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (ticker, float(threshold), email, phone, frequency, notification_type))
        conn.commit()

        return 'Notification settings saved. You will receive a notification when the price of {} reaches or exceeds {} {}.'.format(ticker, threshold, notification_type)
    else:
        return render_template('index.html')


def check_price(ticker, threshold, notification_type, email, phone):
    # Retrieve the current price of the stock using the yfinance library
    stock = yf.Ticker(ticker).info
    price = stock['regularMarketPrice']


    # If the price reaches or exceeds the threshold, send a notification
    if price >= threshold:
        send_notification(notification_type, ticker, price, email, phone)
    return price

def send_notification(notification_type, ticker, price, email, phone):
    if notification_type == 'email':
        #Set up the email message
        from_email = 'stockprice.notifier01@gmail.com'
        to_email = email
        subject = 'Stock notification'
        body = f'The price of the stock with ticker symbol "{ticker}" has reached or exceeded the threshold of {price}.'

        msg = f'Subject: {subject}\n\n{body}'

        # Set up the SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()

        # Log in to the email account
        server.login('stockprice.notifier01@gmail.com', 'axxnwukhrnwsoylv')

        # Send the email
        server.sendmail(from_email, to_email, msg)

        # Close the SMTP server
        server.quit()

    elif notification_type == 'text':
        # Send a text message notification
        pass

if __name__ == '__main__':
    # Retrieve the saved notification settings from the database
    cursor.execute('''
        SELECT ticker, threshold,email, phone, frequency, notification_type
        FROM notifications1
    ''')
    rows = cursor.fetchall()

    # Start the scheduler for each saved notification
    scheduler = BackgroundScheduler()
   
    for row in rows:
        ticker, threshold, email, phone, frequency, notification_type = row
        scheduler.add_job(check_price, 'interval', [ticker, threshold, notification_type, email, phone], minutes=frequency)
    scheduler.start()

    app.run()
