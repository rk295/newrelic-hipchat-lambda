# newrelic-hipchat-lambda

This is a [Lambda] function which aims to integrate [New Relic] with [HipChat]. There exists already a HipChat integration for NewRelic, but at this time it only supports HipChat cloud, not the on prem server version.

The lambda function is designed to be called from New Relic as a WebHook, which `POSTs` to the Lambda function. The code then constructs both a `HTML` fallback message and a 'Card'. These are then sent onto the Hipchat server you have configured.

## Example HipChat Card

![example][example]

## Setup

There is a few bits to setup and get working to make this work, which I'll aim to document at some point. Untile then, there are some screenshots in [this](aws-nr-setup.md) file, which attempt to outline the steps.



[Lambda]: https://aws.amazon.com/lambda/
[New Relic]: https://newrelic.com/
[HipChat]: https://hipchat.com/
[example]: img/example.png
