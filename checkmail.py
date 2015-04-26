# portions credit: http://stackoverflow.com/questions/20414231/getting-unread-messages-using-poplib-python
import dateutil.parser
import email
import email.feedparser
import logging
import os.path
import poplib

# Checks an email inbox for Bamboo build notification emails
# Call load_config_from_file(), then call check() as many times as you want.
class MailChecker:
    def __init__(self):
        self.logger = logging.getLogger("rpi-bamboo-alert")

    # tries to load config info from a file
    # throws exception if something goes wrong
    def load_config_from_file(self, filename):
        errorStr = "Config file should have 4 lines: server, port, username, password";
        if not os.path.isfile(filename):
            raise Exception("File {} not found. {}".format(filename, errorStr));
        with open(filename) as f:
            content = f.read().splitlines()
            if len(content) != 4:
                raise Exception("File {} invalid. {}".format(filename, errorStr));
            self._set_mail_parameters(content[0], content[1], content[2], content[3]);

    # setup all the mail server config
    def _set_mail_parameters(self, mailServer, mailPopPort, emailId, emailPass):
        self.mailServer = mailServer
        self.mailPopPort = mailPopPort
        self.emailId = emailId
        self.emailPass = emailPass

    # return true if the user called init with non-empty parameters, false otherwise
    def configured(self):
        return self.mailServer != "" and self.mailPopPort != "" and self.emailId != "" and self.emailPass != ""

    # checks for email from the Bamboo build server
    # returns true if an email is present, false otherwise
    # empties the inbox in the process
    def check(self):
        # no config? get angry
        if not self.configured():
            raise Exception("mailChecker not configured. Did you forget to call init()?")

        pop_conn = poplib.POP3_SSL(self.mailServer, self.mailPopPort)
        pop_conn.user(self.emailId)
        pop_conn.pass_(self.emailPass)
        messages = [pop_conn.retr(i) for i in range(1, len(pop_conn.list()[1]) + 1)]
        # Concat message pieces:
        messages = [b"\n".join(mssg[1]) for mssg in messages]
        # Parse message into an email object:
        messages = [email.message_from_bytes(mssg) for mssg in messages]

        receivedBambooEmail = False

        for ind, message in enumerate(messages):
            # message from Bamboo?
            if message['From'].find("bamboo@cwmn.us") != -1:
                # yes. check the send date, then delete
                receivedBambooEmail = True
            else:
                # no. just delete it
                self.logger.info("Deleted message from unknown sender {}".format(message['From']))
            pop_conn.dele(ind + 1)
        pop_conn.quit()

        return receivedBambooEmail
