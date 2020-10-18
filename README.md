# Summary emails for Firefly III

Objective: send a monthly summary email, showing totals for each category.

Usage: run 'monthly-report.py' on the command line (e.g. with cron) to send the category report for the previous month. Add your configuration data to config.yaml (copy from config.yaml.sample).

Bugs:

- SMTP authentication not actually implemented (despite appearing in config.yaml)
- Only supports a single currency

Screenshot:

![Firefly-iii monthly report screenshot](screenshot.png?raw=true)