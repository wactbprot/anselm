# https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
import os
import time
import re
from anselm.system import System
from anselm.db import DB
from slackclient import SlackClient
# instantiate Slack client
from _thread import start_new_thread


class Bot(System):

    MENTION_REGEX = "^<@(|[WU].+?)>(.*)"
    RTM_READ_DELAY = 1
    OUT_CHANNEL = "bot"
    def __init__(self):
        super().__init__()

        self.db = DB()

        channel_list = None
        self.info_channel_id = None

        self.p.subscribe("info")
        self.log.info('start listening redis ')

        self.slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

        if self.slack_client.rtm_connect(with_team_state=False, auto_reconnect=True):
            anselm_id = self.slack_client.api_call("auth.test")["user_id"]
            self.log.info('start listening redis ')
            channel_list = self.slack_client.api_call("channels.list")

        if  channel_list and 'channels' in channel_list:
            for channel in channel_list.get('channels'):
                if channel.get('name') == 'bot':
                    self.log.info("git info channel id")
                    self.info_channel_id = channel.get('id')
                    break

    def parse_bot_commands(self, slack_events):

        for event in slack_events:
            if event["type"] == "message" and not "subtype" in event:
                user_id, message = self.parse_direct_mention(event["text"])
                if user_id == self.anselm_id:
                    return message, event["channel"]
        return None, None

    def parse_direct_mention(self, message_text):

        matches = re.search(self.MENTION_REGEX, message_text)
        return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

    def handle_command(self, command, channel):

        ok = False

        if command.startswith('to'):
            ok = True

            todo_pressures_acc = []
            lines = self.get_lines('cal_id')
            for line in lines:
                cal_id = self.aget('cal_id', line)
                doc = self.db.get_doc(cal_id)
                todo_pressures_acc, todo_unit =  self.db.acc_todo_pressure(todo_pressures_acc, doc, self.unit)
                meas_pressure, meas_unit, meas_points = self.db.get_last_target_pressure(doc)

            if len(todo_pressures_acc) > 0:
                self.post(channel, "There are {} todo pressures in total:".format(len(todo_pressures_acc)))
                for i, p in enumerate(todo_pressures_acc):
                    if float(meas_pressure) >= float(p):
                        self.post(channel, "№ {}:         {} {} ✔".format(i+1, p, todo_unit))
                    else:
                        self.post(channel, "№ {}:         {} {}".format(i+1, p, todo_unit))

            else:
                msg = "No calibrations selelected so far."
                self.post(channel, msg )

        if command.startswith('cu'):
            ok = True
            p = self.aget('current_target_pressure', 0)
            if p:
                msg = "The current target pressure is {}".format(p)
            else:
                msg = "The current target pressure is not set yet"
            self.post(channel, msg )

        if command.startswith('ga'):
            ok = True
            self.post(channel, "calibration gas is {}".format(self.aget('gas', 0)))

        if command.startswith('ch'):
            ok = True
            self.post(channel, "I send my infos to channel #{}".format(self.OUT_CHANNEL))

        if command.startswith('id'):
            ok = True
            self.post(channel, "doc ids are:")
            lines = self.get_lines("cal_id")
            for line in lines:
                self.post(channel, self.aget("cal_id", line))

        if command.startswith('fu'):
            ok = True
            self.post(channel, "fullscale of the devices are:")
            lines = self.get_lines("fullscale_value")
            for line in lines:
                self.post(channel, "{} {} ".format(self.aget("fullscale_value", line), self.aget("fullscale_unit", line)))

        if command.startswith('he'):
            ok = True
            self.post(channel, "Beside *he[lp]* further available commands are:")
            self.post(channel, "*to[do pressure]*, *cu[rrent target pressure]*, *ch[annel]*, *ga[s]*, *fu[llscales]* or *id[s]*.")

        if not ok:
            self.post(channel, "Not sure what you mean. Try *help* command.")



    def post(self, channel, msg):

        self.slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=msg
        )

    def msg_in(self):
        self.log.debug("message in")

        self.anselm_id = self.slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = self.parse_bot_commands(self.slack_client.rtm_read())
            if command:
                self.handle_command(command, channel)
            time.sleep(self.RTM_READ_DELAY)


    def msg_out(self):
        if self.info_channel_id:
            for item in self.p.listen():
                self.log.debug("received item: {}".format(item))
                if item['type'] == 'message':

                    self.slack_client.api_call(
                         "chat.postMessage",
                        channel=self.info_channel_id,
                        text=item.get('data')
                        )
        else:
            self.log.error("got no info channel id")

if __name__ == "__main__":
    bot = Bot()
    start_new_thread(bot.msg_out, ())
    bot.msg_in()