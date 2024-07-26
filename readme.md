# Powerlink 3.1 Interface

This library can sit as a MITM between a Visonic Alarm with a Powerlink 3.1 module (only tested with PowerMaster 30) and a PowerManage server to read and decode messages.  It also allows the ability to inject commands into this connection to request data from the panel directly.  It is not designed to be a working solution for anything other than the decoding of messages.

Please note the usual, use at your own risk, no warranties of any kind, it may have bugs, ommisions or incorrect information, your PowerManage provider may not like it and block you etc.

It only requires a small change to your alarm config to tell the alarm to connect to your machine running this library.  Instructions below.

There is also a function to be able to input a message and have the decoder, decode it for you.  Run cmdline_decoder.py and input the message including the b0 and upto any of the end of data marker (43) or the checksum.

## Configure your Visonic Alarm to work with this library

In order to use this with your panel, you need to configure the Central Station Reporting settings in the Installer to point to your machine running this code.

On my PowerMaster-30, it allows 2 receivers.  I recommend you do not remove the existing receiver details pointing to your current PowerManage server, but instead configure your machine as the second receiver.

- Set your IP in the Receiver 2 IP field
- Set the Receiver 2 Account No to be the same as the Receiver Account No 1.
- Set the Report Events to Central Station to all *all.
- Save this config to your panel.

Once this has been done,

- Block your panel's IP address from having internet access.  I did this by adding a block on my router in parental controls.
- Notes:
  - I recommend doing it this way as if you loose conneciton to the PowerManager server, you can no longer use the apps to perform functions.  Whilst, when this is running in Proxy mode, you can use the apps, if it doesn't work for some reason, you can unblock the panels access and it will reconnect to the PowerManage server.
  - Initial connection can take some time, but the panel seems to remember its previous successful connection and therefore subsequent connections are much quicker (but still can take 30s or so)
  - You may need to remove the panels ethernet connection from your switch for 30s to force it to reconnect to this server.

## Using this library

### Setting the mode

In the config.py file, the the PROXY_MODE constant to True or False to determine Proxy or Standard mode.

### Running and stopping the library

You will need python 3.12, recommend running in a venv.
Use python run.py to start
Use CTRL+C to stop

### Receiving commands

At this time, the library just outputs to the screen log.  If debug mode is set in config.py, you will get lots of messages as it receives the message, sends an ACK, decodes the structure, rebuilds paged data and decodes the data itself.  Setting to info level logging will just show the messages and decoded data.

### Sending commands

The library (in both Proxy and Standalone modes) creates a server listening on port 5002 (the Injector).  Connect a TCP Client to this port to be able to send commands to the panel.  Note, it does not yet have a flow controller to prevent you from interupting message flow between the panel and the PowerManager server.  Be mindful of this and wait for the back and forth traffic to quieten down before injecting messages.

### What commands can I send?

So far, it has been designed to send and decode B0 messages, however you can also send standard messages.  If you want to send a B0 command to the panel, you can type this into your Injector TCP client:

#### Shortcode Commands

Send command 24 (Panel status):
B0 24

Send command 17 (Request list with list of commands)
B0 17 18 24 58

Send command 35 (Settings) - this needs a settings id too.  So:
B0 35 01 00

Send command 42 (Settings) - this needs a settings id too.  So:
B0 42 00 00

Command 35 allows a list of requests.  Send multiple command 35 settings requests by:
B0 35 01 00 02 00 03 00 04 00


NOTE: The known settings ids are listed in decoders/b0_35_command.py.  The settings ids for command 42 are the same and have nearly identical meaning.

#### Full Commands

If you want to send a standard message to the panel - is just needs to end in 43 if it starts with B0
A6 00 00 00 00 00 00 00 00 00 00 43
B0 01 24 01 05 43
