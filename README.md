# Summary emails for Firefly III

Background: Self-hosted budgeting software [firefly-iii](https://github.com/firefly-iii/firefly-iii) doesn’t have an email reports feature. I missed this when I switched from Mint.

Objective: send a monthly summary email, showing totals for each category.

Usage: run 'monthly-report.py' on the command line (e.g. with cron) to send the category report for the previous month. Add your configuration data to config.yaml (copy from config.yaml.sample).

Known issues:

- Only supports a single currency

Screenshot:

![Firefly-iii monthly report screenshot](screenshot.png?raw=true)
