# SIP Healthcheck [Python SIP OPTIONS Packet]

SIP Healthcheck is a simple tool that allow to check and alert that refect on SIP endpoint by sending SIP OPTIONS methods

## Features:
* Ping SIP endpoin by SIP OPTIONS
* Collecting evaualuation metric such as latency, timeout or response code
* Configuration inventory via yaml format
* Support TCP, UDP transport
* Notify via Slack, SMS, Email, or Voice.
* Setting up sequent time send notification
* Setting up threshold for alert
* and many more .., pull requests are welcome

## REQUIREMENTS
* requests
* yaml
* twilio

## USAGE
* Setting your inventory in configuration.yml

* Start Monitoring by run command:  
```python siphealthcheck.py```

## Container: 
Docker will be added soon.

## Notification
Current nofications are supported to use slack, mailgun, sms and voice call.

Chat channel with Slack     |  Email with Mailgun        | SMS & Call with Twilio
:-------------------------:|:-------------------------:|:-------------------------:
<img src="https://a.slack-edge.com/4a5c4/marketing/img/icons/icon_slack.svg" width="128" height="64">  |<img src="https://login.mailgun.com/login/static/logo.svg" width="128" height="64"> |<img src="https://www.twilio.com/marketing/bundles/company-brand/img/logos/red/twilio-logo-red.png" width="137" height="64"> 


## Slack Alert Example:
![sip-healthcheck-alert](https://user-images.githubusercontent.com/58973699/71613706-e56dc100-2be2-11ea-9770-d44e69d4cc39.jpg)

## AUTHOR

**Minh Minh**

---
