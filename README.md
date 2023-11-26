# 📊 Monthly Budget Reports for Firefly III 🚀

**This email report app is a magical fork of [davidschlachter](https://github.com/davidschlachter/firefly-iii-email-summary)'s email report app.**

An external plugin for [firefly-iii](https://github.com/firefly-iii/firefly-iii) that brings you a delightful email report! 📧✨ Get ready for a monthly overview, perfect for the 1st of each month, summarizing the previous month's financial adventures.

## Features 🌟

You'll receive a mobile-optimized email that crafts snazzy cards for every budget, showing how much you've spent as a percentage. 📈 If you've respected your budget, a gleaming green card awaits. If not, brace yourself for a red card and details on where the funds flowed from the categories within that budget. At the finale, a monthly overview reveals your earnings, expenses, savings, and their percentages—ideal for setting monthly targets! 💸🎯

Benefits? 🤩
- **Effortless Reading:** A mere swipe reveals overspending details in a flash! ⚡️
- **Intuitively Designed:** Easy on the eyes, simple in use! 👀
- **Shareable:** Perfect for less tech-savvy partners who prefer simplicity over complexity! 👫

## Installation 🛠️

Installing the email plugin is a breeze, but you'll need a couple of things beforehand:

### Prerequisites

Since Google Mail will bid farewell to unsecured email apps starting Jan 2024, we recommend [SMTP2GO](https://www.smtp2go.com/) as your email server. It sends emails as you and offers a generous free tier of up to 1000 mails per month (we just need 1). 📩🔒

### Installation Steps

1. Run `pip install -r requirements.txt` inside the file directory to install all the essential packages for our plugin. 📦
2. Copy `config.yaml.sample` and create `config.yaml`, then update it with your personalized details. 📝
3. Set up a cron job to run the script. For Docker, use this command: `0 12 1 * * /usr/bin/python3 /<path-yo-your-file>/monthly-report.py`. Access the cron job file with `crontab -e` on Ubuntu. 🕒

Screenshot 📸:

![Firefly-iii monthly report screenshot](screenshot.png?raw=true)
