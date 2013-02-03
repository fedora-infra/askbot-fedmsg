A askbot plugin for sending messages across the Fedora Infrastructure message
bus.  This plugin hooks itself up to django signals sent by askbot and simply
republishes information to the fedmsg bus.
