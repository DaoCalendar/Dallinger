import logging
import six
import smtplib
from cached_property import cached_property
from datetime import datetime
from email.mime.text import MIMEText

logger = logging.getLogger(__file__)


def get_email_server():
    return smtplib.SMTP('smtp.gmail.com:587')


resubmit_whimsical = """Dearest Friend,

I am writing to let you know that at {when},
during my regular (and thoroughly enjoyable) perousal of the most charming
participant data table, I happened to notice that assignment {assignment_id}
has been taking longer than we were expecting. I recall you had suggested
{duration} minutes as an upper limit for what was an acceptable length of time
for each assignement, however this assignment had been underway for a shocking
{minutes_so_far} minutes, a full {minutes_excess} minutes over your allowance.
I immediately dispatched a telegram to our mutual friends at AWS and they were
able to assure me that although the notification had failed to be correctly
processed, the assignment had in fact been completed. Rather than trouble you,
I dealt with this myself and I can assure you there is no immediate cause for
concern. Nonetheless, for my own peace of mind, I would appreciate you taking
the time to look into this matter at your earliest convenience.

I remain your faithful and obedient servant,

William H. Dallinger

P.S. Please do not respond to this message, I am busy with other matters.
"""


resubmit_nonwhimsical = """Dear experimenter,

This is an automated email from
Dallinger. You are receiving this email because the Dallinger platform has
discovered evidence that a notification from Amazon Web Services failed to
arrive at the server. Dallinger has automatically contacted AWS and has
determined the dropped notification was a submitted notification (i.e. the
participant has finished the experiment). This is a non-fatal error and so
Dallinger has auto-corrected the problem. Nonetheless you may wish to check the
database.

Best,
The Dallinger dev. team.

Error details:
Assignment: {assignment_id}
Allowed time: {duration}
Time since participant started: {minutes_so_far}
"""


cancelled_hit_whimsical = """Dearest Friend,

I am afraid I write to you with most grave tidings. At {when},
during a routine check of the usually most delightful participant data table,
I happened to notice that assignment {assignment_id} has been taking longer
than we were expecting. I recall you had suggested {duration} minutes as an
upper limit for what was an acceptable length of time for each assignment,
however this assignment had been underway for a shocking {minutes_so_far}
minutes, a full {minutes_excess} minutes over your allowance. I immediately
dispatched a telegram to our mutual friends at AWS and they infact informed me
that they had already sent us a notification which we must have failed to
process, implying that the assignment had not been successfully completed. Of
course when the seriousness of this scenario dawned on me I had to depend on
my trusting walking stick for support: without the notification I didn't know
to remove the old assignment's data from the tables and AWS will have already
sent their replacement, meaning that the tables may already be in a most
unsound state!

I am sorry to trouble you with this, however, I do not know how to proceed so
rather than trying to remedy the scenario myself, I have instead temporarily
ceased operations by expiring the HIT with the fellows at AWS and have
refrained from posting any further invitations myself. Once you see fit I
would be most appreciative if you could attend to this issue with the caution,
sensitivity and intelligence for which I know you so well.

I remain your faithful and
obedient servant,
William H. Dallinger

P.S. Please do not respond to this
message, I am busy with other matters.
"""

cancelled_hit_nonwhimsical = """Dear experimenter,

This is an automated email from
Dallinger. You are receiving this email because the Dallinger platform has
discovered evidence that a notification from Amazon Web Services failed to
arrive at the server. Dallinger has automatically contacted AWS and has
determined the dropped notification was an abandoned/returned notification
(i.e. the participant had returned the experiment or had run out of time).
This is a serious error and so Dallinger has paused the experiment - expiring
the HIT on MTurk and setting auto_recruit to false. Participants currently
playing will be able to finish, however no further participants will be
recruited until you do so manually. We strongly suggest you use the details
below to check the database to make sure the missing notification has not caused
additional problems before resuming.
If you are receiving a lot of these
emails this suggests something is wrong with your experiment code.

Best,

The Dallinger dev. team.

Error details:
Assignment: {assignment_id}

Allowed time: {duration}
Time since participant started: {minutes_so_far}
"""

idle_template = """Dear experimenter,

This is an automated email from Dallinger. You are receiving this email because
your dyno has been running for over {minutes_so_far} minutes.

The application id is: {app_id}

To see the logs, use the command "dallinger logs --app {app_id}"
To pause the app, use the command "dallinger hibernate --app {app_id}"
To destroy the app, use the command "dallinger destroy --app {app_id}"


The Dallinger dev. team.
"""

hit_error_template = """Dear experimenter,

This is an automated email from Dallinger. You are receiving this email because
a recruited participant has been unable to complete the experiment due to
a bug.

The application id is: {app_id}

The information about the failed HIT is recorded in the database in the
Notification table, with assignment_id {assignment_id}.

To see the logs, use the command "dallinger logs --app {app_id}"
To pause the app, use the command "dallinger hibernate --app {app_id}"
To destroy the app, use the command "dallinger destroy --app {app_id}"


The Dallinger dev. team.
"""


class MessengerError(Exception):
    """A message could not be relayed."""


class HITSummary(object):

    def __init__(self, assignment_id, duration, time_active, app_id, when=datetime.now()):
        self.when = when
        self.assignment_id = assignment_id
        self.duration = int(round(duration / 60))
        self.minutes_so_far = int(round(time_active / 60))
        self.minutes_excess = int(round((time_active - duration) / 60))
        self.app_id = app_id


class EmailConfig(object):
    """Extracts and validates email-related values from a Configuration
    """
    _map = {
        'username': 'dallinger_email_address',
        'toaddr': 'contact_email_on_error',
        'email_password': 'dallinger_email_password',
    }

    def __init__(self, config):
        self.username = config.get('dallinger_email_address', '')
        self.toaddr = config.get('contact_email_on_error', '')
        self.email_password = config.get('dallinger_email_password', '')
        self.fromaddr = self.username
        self.whimsical = config.get('whimsical', False)

    def validate(self):
        """Could this config be used to send a real email?"""
        missing = []
        for k, v in self._map.items():
            if not getattr(self, k, False):
                missing.append(v)
        if missing:
            return "Missing or invalid config values: {}".format(
                ', '.join(missing)
            )


class BaseHITMessenger(object):

    def __init__(self, hit_info, email_settings):
        self.when = hit_info.when
        self.assignment_id = hit_info.assignment_id
        self.duration = hit_info.duration
        self.minutes_so_far = hit_info.minutes_so_far
        self.minutes_excess = hit_info.minutes_excess
        self.app_id = hit_info.app_id
        self.whimsical = email_settings.whimsical
        self.username = email_settings.username
        self.fromaddr = email_settings.fromaddr
        self.toaddr = email_settings.toaddr
        self.email_password = email_settings.email_password

    def send_resubmitted_msg(self):
        data = self._build_resubmitted_msg()
        self._send(data)
        return data

    def send_hit_cancelled_msg(self):
        data = self._build_hit_cancelled_msg()
        self._send(data)
        return data

    def send_idle_experiment(self):
        template = idle_template
        data = {
            'message': template.format(**self.__dict__),
            'subject': "Idle Experiment."
        }
        self._send(data)
        return data

    def send_hit_error(self):
        template = hit_error_template
        data = {
            'message': template.format(**self.__dict__),
            'subject': "Error during HIT."
        }
        self._send(data)
        return data

    def _build_resubmitted_msg(self):
        if self.whimsical:
            template = resubmit_whimsical
            data = {
                'message': template.format(**self.__dict__),
                'subject': 'A matter of minor concern.'
            }

        else:
            template = resubmit_nonwhimsical
            data = {
                'message': template.format(**self.__dict__),
                'subject': "Dallinger automated email - minor error."
            }

        return data

    def _build_hit_cancelled_msg(self):
        if self.whimsical:
            template = cancelled_hit_whimsical
            data = {
                'message': template.format(**self.__dict__),
                'subject': "Most troubling news."
            }
        else:
            template = cancelled_hit_nonwhimsical
            data = {
                'message': template.format(**self.__dict__),
                'subject': "Dallinger automated email - major error."
            }

        return data


class EmailingHITMessenger(BaseHITMessenger):
    """Actually sends an email message to the experiment owner.
    """

    @cached_property
    def server(self):
        return get_email_server()

    def _send(self, data):
        msg = MIMEText(data['message'])
        msg['Subject'] = data['subject']
        try:
            self.server.starttls()
            self.server.login(self.username, self.email_password)
            self.server.sendmail(self.fromaddr, self.toaddr, msg.as_string())
            self.server.quit()
        except smtplib.SMTPException as ex:
            six.raise_from(
                MessengerError('SMTP error sending HIT error email.'),
                ex
            )
        except Exception as ex:
            six.raise_from(
                MessengerError("Unknown error sending HIT error email."),
                ex
            )


class NullHITMessenger(BaseHITMessenger):
    """Does nothing at all.

    Used as a placeholder in contexts where sending a message is not possible.
    """

    def _send(self, data):
        pass


class DebugHITMessenger(BaseHITMessenger):
    """Used in debug mode.

    Prints the message contents to the log instead of sending an email.
    """

    def _send(self, data):
        logger.info(
            "{} sending message:\n{}".format(
                self.__class__.__name__, data['message'])
        )


def get_messenger(hit_info, config):
    email_settings = EmailConfig(config)
    if config.get("mode") == "debug":
        return DebugHITMessenger(hit_info, email_settings)
    problems = email_settings.validate()
    if problems:
        logger.info(problems + " Will log errors instead of emailing them.")
        return DebugHITMessenger(hit_info, email_settings)
    return EmailingHITMessenger(hit_info, email_settings)
