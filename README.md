# DAPNET2APRSNotifier
This is sort of a merging of DAPNET2APRS by KR0SIV and DAPNETNotifier by N8ACL

At first I tried DAPNET2APRS... and while it worked at sending the messages to APRS... it was sending ALL the messages, including ones that weren't intended for me.  This seemed to be due to trying to parse the pi-star HTML for the messages, there had to be a better way... 

And that's where I found DAPNETNotifier... it uses the DAPNET API to get your messages..... BUT, while it will send messages to all sorts of services, it didn't have anything to send them to APRS.... 

So... I stripped out all the other messenger services.... If you want them, DAPNETNotifier is a good bit of code... use it.   I then plugged in the APRS sending code from DAPNET2APRS, that and some housekeeping to use a MySQL or SQLite database to keep track of what messages have been sent, and only add a message to the database once it has been sent successfully, improved error handling as well.

Once I did that, I made a few other changes... DAPNETNotifier uses sqlite to keep a database of the messages its sent, and I didn't like the idea of it hammering away on an sqlite file on my SD card on my pi.... so I added the capability for it to use the MariaDB server on my NAS instead.... so now you can choose either sqlite or MariaDB

Here's how to install this on a Pi-Star or WPSD system so it will run as a service behind the scenes.
This program requires the following python3 modules requests, aprslib, and configparser.  The install script will attempt to install them with pip, but you may need to install manually if that doesn't work.


github clone https://github.com/mytechguyri/DAPNET2APRSNotifier.git

cd DAPNET2APRSNotifier

./install.sh

Then complete the config in the /etc/dapnet2aprs file and start the dapnet2aprs service.

Make sure you have OUTPUT port 8080 open on the firewall, or else you won't be able to connect to the DAPNET API.  I discovered this after trying to figure out all night why the DAPNET API wasn't working, only to find the WPSD firewall rules were defaulting to DENY on the OUTPUT chain (typically output is default ACCEPT, because folks are more concerned with what gets in, not what gets out)

This is of course a work in progress, so if you have any problems, please feel free to email me john at wa1okb.radio

