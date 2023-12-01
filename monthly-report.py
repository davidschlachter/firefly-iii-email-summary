#!/usr/local/bin/python3.7

import yaml
import sys
import traceback
import datetime
import requests
import re
import bs4
import ssl
import smtplib

from email.message import EmailMessage
from email.headerregistry import Address
from email.utils import make_msgid


def main():
    #
    # Load configuration
    with open('config.yaml', 'r') as configFile:
        try:
            config = yaml.safe_load(configFile)
        except:
            traceback.print_exc()
            print("ERROR: could not load config.yaml")
            sys.exit(1)
    #
    # Determine the applicable date range: the previous month
    today = datetime.date.today()
    endDate = today.replace(day=1) - datetime.timedelta(days=1)
    startDate = endDate.replace(day=1)
    monthName = startDate.strftime("%B")
    #
    # Set us up for API requests
    HEADERS = {'Authorization': 'Bearer {}'.format(config['accesstoken'])}
    with requests.Session() as s:
        s.headers.update(HEADERS)
        #
        # Get all the categories
        url = config['firefly-url'] + '/api/v1/categories'
        categories = s.get(url).json()
        #
        # Get the spent and earned totals for each category
        totals = []
        for category in categories['data']:
            url = config['firefly-url'] + '/api/v1/categories/' + category['id'] + '?start=' + \
                startDate.strftime('%Y-%m-%d') + '&end=' + \
                endDate.strftime('%Y-%m-%d')
            r = s.get(url).json()
            categoryName = r['data']['attributes']['name']
            try:
                categorySpent = r['data']['attributes']['spent'][0]['sum']
            except (KeyError, IndexError):
                categorySpent = 0
            try:
                categoryEarned = r['data']['attributes']['earned'][0]['sum']
            except (KeyError, IndexError):
                categoryEarned = 0
            categoryTotal = float(categoryEarned) + float(categorySpent)
            totals.append({'name': categoryName, 'spent': categorySpent,
                          'earned': categoryEarned, 'total': categoryTotal})
        #
        # Get all the budgets
        budgetsUrl = config['firefly-url'] + '/api/v1/budgets'
        budgetsCategories = s.get(budgetsUrl).json()
        #
        # Get set value budgets for each category
        budgets = []
        for budget in budgetsCategories['data']:
            name = budget['attributes']['name']
            amount = budget['attributes']['auto_budget_amount']
            budgets.append({'name': name, 'budgeted': amount})
        #
        # Get all the budgets spent
        budgetIndex = 1
        for budget in budgets:
            budgetsSpentUrl = config['firefly-url'] + '/api/v1/budgets/' + str(
                budgetIndex) + '/limits?start=' + startDate.strftime('%Y-%m-%d') + endDate.strftime('%Y-%m-%d')
            budgetsSpentCategories = s.get(budgetsSpentUrl).json()
            # Get the spent for the current budget
            # Check is data is non-empty
            if len(budgetsSpentCategories['data']) > 0:
                spent = budgetsSpentCategories['data'][0]['attributes']['spent']
                # Update the 'spent' value for the current budget item
                budgets[budgetIndex - 1]['spent'] = round(abs(float(spent)), 2)
                # Increment budgetIndex for the next iteration
            budgetIndex += 1
        #
        # Get general information
        monthSummary = s.get(config['firefly-url'] + '/api/v1/summary/basic' + '?start=' +
                             startDate.strftime('%Y-%m-%d') + '&end=' + endDate.strftime('%Y-%m-%d')).json()
        yearToDateSummary = s.get(config['firefly-url'] + '/api/v1/summary/basic' + '?start=' +
                                  startDate.strftime('%Y') + '-01-01' + '&end=' + endDate.strftime('%Y-%m-%d')).json()
        currency = config.get('currency', None)
        currencySymbol = config.get('currencySymbol', None)
        if currency:
            currencyName = currency
        else:
            for key in monthSummary:
                if re.match(r'spent-in-.*', key):
                    currencyName = key.replace("spent-in-", "")
        spentThisMonth = abs(float(
            monthSummary['spent-in-'+currencyName]['monetary_value']))
        earnedThisMonth = float(
            monthSummary['earned-in-'+currencyName]['monetary_value'])
        netChangeThisMonth = float(
            monthSummary['balance-in-'+currencyName]['monetary_value'])
        spentThisYear = float(
            yearToDateSummary['spent-in-'+currencyName]['monetary_value'])
        earnedThisYear = float(
            yearToDateSummary['earned-in-'+currencyName]['monetary_value'])
        netChangeThisYear = float(
            yearToDateSummary['balance-in-'+currencyName]['monetary_value'])
        netWorth = float(
            yearToDateSummary['net-worth-in-'+currencyName]['monetary_value'])
        savedThisMonth = round(earnedThisMonth - spentThisMonth)
        savedPercentage = round((savedThisMonth / earnedThisMonth) * 100)
        spendPercentage = 100 - savedPercentage
        #
        # Set up the categories table
        categoriesTableBody = '<table><tr><th>Category</th><th style="text-align: right;">Total</th></tr>'
        # categoriesTableBody = '<table><tr><th>Category</th><th>Spent</th><th>Earned</th><th>Total</th></tr>'
        for category in totals:
            categoriesTableBody += '<tr><td style="padding-right: 1em;">' + \
                category['name']+'</td><td style="text-align: right;">' + \
                str(round(float(category['total']))).replace(
                    "-", "−")+'</td></tr>'
        # categoriesTableBody += '<tr><td>'+category['name']+'</td><td>'+str(round(float(category['spent'])))+'</td><td>'+str(round(float(category['earned'])))+'</td><td>'+str(round(float(category['total'])))+'</td></tr>'
        categoriesTableBody += '</table>'
        #
        # budgetsTableBody = '<table><tr><th>Category</th><th>Spent</th><th>Earned</th><th>Total</th></tr>'
        budgetsTableBody = '<table><tr><th>Category</th><th style="text-align: right;">Total</th></tr>'
        totalBudgetsAmount = 0
        for category in budgets:
            totalBudgetsAmount += round(float(category['budgeted']))
            budgetsTableBody += '<tr><td style="padding-right: 1em;">' + \
                category['name']+'</td><td style="text-align: right;">' + \
                str(round(float(category['budgeted'])))+'</td></tr>'
        #
        # budgetsTableBody += '<tr><td>'+category['name']+'</td><td>'+str(round(float(category['spent'])))+'</td><td>'+str(round(float(category['earned'])))+'</td><td>'+str(round(float(category['total'])))+'</td></tr>'#here
        budgetsTableBody += '</table>'
        #
        # Set up the general information table
        generalTableBody = '<table>'
        generalTableBody += '<tr><td>Spent this month:</td><td style="text-align: right;">' + \
            str(round(spentThisMonth)).replace("-", "−") + '</td></tr>'
        generalTableBody += '<tr><td>Earned this month:</td><td style="text-align: right;">' + \
            str(round(earnedThisMonth)).replace("-", "−") + '</td></tr>'
        generalTableBody += '<tr style="border-bottom: 1px solid black"><td>Net change this month:</td><td style="text-align: right;">' + \
            str(round(netChangeThisMonth)).replace("-", "−") + '</td></tr>'
        generalTableBody += '<tr><td>Spent so far this year:</td><td style="text-align: right;">' + \
            str(round(spentThisYear)).replace("-", "−") + '</td></tr>'
        generalTableBody += '<tr><td>Earned so far this year:</td><td style="text-align: right;">' + \
            str(round(earnedThisYear)).replace("-", "−") + '</td></tr>'
        generalTableBody += '<tr style="border-bottom: 1px solid black"><td style="padding-right: 1em;">Net change so far this year:</td><td style="text-align: right;">' + \
            str(round(netChangeThisYear)).replace("-", "−") + '</td></tr>'
        generalTableBody += '<tr><td>Current net worth:</td><td style="text-align: right;">' + \
            str(round(netWorth)).replace("-", "−") + '</td></tr>'
        generalTableBody += '</table>'
        #
        # Get transaction in a budget, group by category + sorted descending
        def getCategories(budget):
            index = 1
            pageNumber = 1
            categoriesAmount = []
            #
            # Find budget index
            for i, item in enumerate(budgets):
                if item["name"] == budget:
                    index = i + 1
                    break
            #            
            # Get all the transactions grouped by category in this budget
            while True:
                budgetsCategoryUrl = config['firefly-url'] + f'/api/v1/budgets/{index}/limits/{index}/transactions?limit=50&page={pageNumber}' + '&start=' + startDate.strftime('%Y-%m-%d') + '&end=' + endDate.strftime('%Y-%m-%d')
                transactionCategories = s.get(budgetsCategoryUrl).json()
                #
                # Get transactions from current page
                for category in transactionCategories['data']:
                    name = category['attributes']['transactions'][0]['category_name']
                    amount = category['attributes']['transactions'][0]['amount']
                    categoriesAmount.append({'name': name, 'spent': round(float(amount), 2)})
                    #
                    # Check pagination for the next page
                if pageNumber < transactionCategories['meta']['pagination']['total_pages']:
                    pageNumber += 1
                else:
                    break  # Exit the loop when all pages are processed
            #
            # Group and sort descending the categories amount
            sums = {}
            for item in categoriesAmount:
                name = item['name']
                spent = float(item['spent'])  # Convert spent to float
                if name not in sums:
                    sums[name] = 0
                sums[name] += spent
                
            sorted_sums = dict(sorted(sums.items(), key=lambda x: x[1], reverse=True))
            
            # Constructing the HTML string
            html_result = '<p style="margin-top: 10px">'
            html_result += 'Categories: <br />'
            for category, total_spent in sorted_sums.items():
                html_result += f"- {category}: {currencySymbol}{total_spent:.2f} <br />"

            html_result += '</p>'
            
            return html_result
        #
        # Display budgeting zone
        goodBudgeting = '''   
        <div
                    class="loading-bar-2"
                    style="
                    border: 2px solid #2ca58d;
                    border-radius: 20px;
                    padding: 10px;
                    margin-bottom: 20px;
                    "
                >
                    <div
                    class="loading-bar-name"
                    style="display: flex; justify-content: center; font-weight: bold"
                    >
                    <p style="margin-top: 10px">{budgetName}</p>
                    </div>
                    <div class="loading-bar-progress-2">
                    <div
                        class="loading-bar-progress"
                        style="border: 2px solid #2ca58d; border-radius: 10px"
                    >
                        <div
                        class="loading-bar-fill"
                        style="
                            background-color: #2ca58d;
                            height: 20px;
                            width: {percentage}%;
                            border-radius: 10px;
                            position: relative;
                        "
                        >
                        <span
                            class="loading-bar-percentage"
                            style="
                            position: absolute;
                            top: 50%;
                            left: 50%;
                            transform: translate(-50%, -50%);
                            color: #ffffff;
                            "
                            > {percentage}%</span
                        >
                        </div>
                    </div>
                    </div>
                    <p style="margin-top: 10px">Budget size: {currencySymbol}{budgetPlanned}</p>
                    <p style="margin-top: 10px">Paid: {currencySymbol}{spent}</p>
                    <p style="margin-top: 10px">Saved: {currencySymbol}{saved}</p>
                    <div class="budget-message respected">
                    <p>Your Budget is being Respectfully Managed! 🌟</p>
                    </div>
                </div>
        '''
        badBudgeting = '''
        <div
                    class="loading-bar"
                    style="
                    border: 2px solid #89023e;
                    border-radius: 20px;
                    padding: 10px;
                    margin-bottom: 20px;
                    "
                >
                    <div
                    class="loading-bar-name"
                    style="display: flex; justify-content: center; font-weight: bold"
                    >
                    <p style="margin-top: 10px">{budgetName}</p>
                    </div>
                    <div
                    class="loading-bar-progress"
                    style="border: 2px solid #89023e; border-radius: 10px"
                    >
                    <div
                        class="loading-bar-fill"
                        style="
                        background-color: #89023e;
                        height: 20px;
                        width: 100%;
                        border-radius: 20px;
                        position: relative;
                        "
                    >
                        <span
                        class="loading-bar-percentage"
                        style="
                            position: absolute;
                            top: 50%;
                            left: 50%;
                            transform: translate(-50%, -50%);
                            color: #ffffff;
                        "
                        > {percentage}% 💀</span
                        >
                    </div>
                    </div>
                    <p style="margin-top: 10px">Budget size: {currencySymbol}{budgetPlanned}</p>
                    <p style="margin-top: 10px">Paid: {currencySymbol}{spent}</p>
                    <div class="budget-message overspent">
                    <p>Oops! Some Overspending Detected! 😅</p>
                    <p style="margin-top: 10px">
                        Explore your expenses in these categories 🕵️‍♂️
                    </p>
                    </div>
                    {overspentCategories}
                </div>
        '''
        budgetsMonthlyList = ''
        for budget in budgets:
            if float(budget['budgeted']) > float(budget['spent']):
                budgetsMonthlyList += goodBudgeting.format(budgetName=budget['name'], currencySymbol=currencySymbol, budgetPlanned=round(float(budget['budgeted'])), spent=round(float(budget['spent'])), saved=round(
                    float(budget['budgeted'])) - round(float(budget['spent'])), percentage=round((round(float(budget['spent'])) / round(float(budget['budgeted']))) * 100)) # type: ignore
            else:
                budgetsMonthlyList += badBudgeting.format(budgetName=budget['name'], currencySymbol=currencySymbol, budgetPlanned=round(float(budget['budgeted'])), overspentCategories=getCategories(budget['name']),spent=round(
                    float(budget['spent'])), percentage=round((round(float(budget['spent'])) / round(float(budget['budgeted']))) * 100)) # type: ignore
        #
        # Assemble the email
        msg = EmailMessage()
        msg['Subject'] = "Firefly III: Monthly report"
        msg['From'] = "monthly-report <" + config['email']['from'] + ">"
        msg['To'] = (tuple(config['email']['to']))
        htmlBody = """
        <html lang="en">
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>FireFly III Monthly Report</title>
        </head>
        <body
            style="
            margin: 0;
            font-family: Arial, sans-serif;
            line-height: 1.6;
            background-color: #f5f5f5;
            "
        >
            <table
            class="container"
            cellpadding="0"
            cellspacing="0"
            border="0"
            align="center"
            style="
                width: 100%;
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
            "
            >
            <!-- Header -->
            <div
                class="navbar"
                style="
                background-color: #ffbf46;
                color: #ffffff;
                text-align: center;
                padding: 10px 0;
                "
            >
                <h1>FireFly III</h1>
            </div>
            <tr>
                <td class="header" style="padding: 40px 20px; text-align: center">
                <h1 style="margin: 0; color: #333333">
                    📊 Are you rocking your budgets? 🚀
                </h1>
                </td>
            </tr>
            <!-- Body Content -->
            <tr>
                <td class="body-content" style="padding: 40px 20px">
                <p style="margin-bottom: 20px">Hey there, Budget Boss! 🎉</p>
                <p style="margin-bottom: 20px">
                    Here comes your monthly review for {monthName} {year} - a treasure trove of insights into
                    your spending habits and financial triumphs! 💰✨
                </p>
                <!-- Container with Loading Bar and Budget Text -->
                {budgetsMonthlylList}
                <div
                    class="loading-bar-2"
                    style="
                    border: 2px solid #735cdd;
                    border-radius: 20px;
                    padding: 10px;
                    margin-bottom: 20px;
                    "
                >
                    <div
                    class="loading-bar-name"
                    style="display: flex; justify-content: center; font-weight: bold"
                    >
                    <p style="margin-top: 10px">{monthName} review</p>
                    </div>
                    <div class="loading-bar-progress-2">
                    <div
                        class="loading-bar-progress"
                        style="border: 2px solid #735cdd; border-radius: 20px"
                    >
                        <div
                        class="loading-bar-fill"
                        style="
                            background-color: #735cdd;
                            height: 20px;
                            width: {spendPercentage}%;
                            border-radius: 10px;
                            position: relative;
                        "
                        >
                        <span
                            class="loading-bar-percentage"
                            style="
                            position: absolute;
                            top: 50%;
                            left: 50%;
                            transform: translate(-50%, -50%);
                            color: #ffffff;
                            "
                            > {spendPercentage}%</span
                        >
                        </div>
                    </div>
                    </div>
                    <p style="margin-top: 10px">Earned: {currencySymbol}{earnedThisMonth}</p>
                    <p style="margin-top: 10px">Total budgeted: {currencySymbol}{totalBudgetsAmount}</p>
                    <p style="margin-top: 10px">Paid: {currencySymbol}{spentThisMonth}</p>
                    <p style="margin-top: 10px">Saved: {currencySymbol}{savedThisMonth} or {savedPercentage}%</p>
                    <div class="budget-message general-info">
                    <p>🌈 "Financial freedom is the new rich." - Unknown 🌟</p>
                    </div>
                </div>
                <p style="margin-bottom: 20px">
                    Cheers, <br />Your Budgeting Buddy 🌟
                </p>
                </td>
            </tr>
            </table>
        </body>
        </html>
		""".format(monthName=monthName, year=startDate.strftime("%Y"), currencySymbol=currencySymbol, totalBudgetsAmount=totalBudgetsAmount, budgetsMonthlylList=budgetsMonthlyList, spendPercentage=spendPercentage, savedPercentage=savedPercentage, savedThisMonth=savedThisMonth, spentThisMonth=round(spentThisMonth), earnedThisMonth=round(earnedThisMonth))
        msg.set_content(bs4.BeautifulSoup(
            htmlBody, "html.parser").get_text())  # just html to text
        msg.add_alternative(htmlBody, subtype='html')
        #
        # Set up the SSL context for SMTP if necessary
        context = ssl.create_default_context()
        #
        # Send off the message
        with smtplib.SMTP(host=config['smtp']['server'], port=config['smtp']['port']) as s:
            if config['smtp']['starttls']:
                s.ehlo()
                try:
                    s.starttls(context=context)
                except:
                    traceback.print_exc()
                    print("ERROR: could not connect to SMTP server with STARTTLS")
                    sys.exit(2)
            if config['smtp']['authentication']:
                try:
                    s.login(user=config['smtp']['user'],
                            password=config['smtp']['password'])
                except:
                    traceback.print_exc()
                    print("ERROR: could not authenticate with SMTP server.")
                    sys.exit(3)
            s.send_message(msg)


if __name__ == "__main__":
    main()
