This project provides a Fabric file suitable for installing a
pmxbot instance on a clean Ubuntu Trusty host.

To use it, simply install fabric in your local environment, then invoke:

    python -m fabric bootstrap

You will be prompted for the MongoDB password and Twilio token. If this is
a new installation, you should get those credentials from someone. If you're
simply refreshing an existing installation, it's safe to skip those prompts
by simply hitting carriage return.

Read the source in fabfile.py for more details.
