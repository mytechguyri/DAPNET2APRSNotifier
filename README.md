# DAPNET2APRSNotifier
This is sort of a merging of DAPNET2APRS by KR0SIV and DAPNETNotifier by n8acl

At first I tried DAPNET2APRS... and while it worked at sending the messages to APRS... it was sending ALL the messages, including ones that weren't intended for me.  This seemed to be due to trying to parse the pi-star HTML for the messages, there had to be a better way.

And that's where I found DAPNETNotifier... it uses the DAPNET API to get your messages..... BUT, while it will send messages to all sorts of services, it didn't have anything to send them to APRS.... 

So... I stripped out all the other messenger services.... If you want them, DAPNETNotifier is a good bit of code... use it.   I then plugged in the APRS sending code from DAPNET2APRS

Once I did that, I made a few other changes... DAPNETNotifier uses sqlite to keep a database of the messages its sent, and I didn't like the idea of it hammering away on an sqlite file on my SD card on my pi.... so I added the capability for it to use the MariaDB server on my NAS instead.... so now you can choose either sqlite or MariaDB


