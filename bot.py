# https://www.fullstackpython.com/blog/build-first-slack-bot-python.html
import os
import time
import re
from anselm.system import System
from anselm.db import DB
from anselm.utils import Utils
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
        self.utils = Utils()

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
            todo_n_acc = []
            lines = self.get_lines('cal_id')
            for line in lines:
                cal_id = self.aget('cal_id', line)
                doc = self.db.get_doc(cal_id)
                todo_dict = self.utils.extract_todo_pressure(doc)
                todo_pressures_acc, todo_n_acc, todo_unit =  self.utils.acc_pressure(todo_dict, todo_pressures_acc, todo_n_acc)

            if len(todo_pressures_acc) > 0:
                self.post(channel, "There are {no} todo pressures in total:".format(no=len(todo_pressures_acc)))
                for i, p in enumerate(todo_pressures_acc):
                    self.post(channel, "№ {no}:  {p} {unit} (N = {n})".format(no=i+1,p=p, unit=todo_unit, n=todo_n_acc[i]))
            else:
                msg = "No calibrations selelected so far."
                self.post(channel, msg )
            
        if command.startswith('re'):
            ok = True

            todo_pressures_acc = []
            todo_n_acc = []
            lines = self.get_lines('cal_id')
            for line in lines:
                cal_id = self.aget('cal_id', line)
                doc = self.db.get_doc(cal_id)
                todo_dict = self.utils.extract_todo_pressure(doc)
                todo_pressures_acc, todo_n_acc, unit =  self.utils.acc_pressure(todo_dict, todo_pressures_acc, todo_n_acc)
            
            remaining_pressure_acc = []
            remaining_n_acc = []
            for line in lines: 
                cal_id = self.aget('cal_id', line)
                doc = self.db.get_doc(cal_id)
                target_dict = self.utils.extract_target_pressure(doc)
               
                remaining_pressure, remaining_n, unit =  self.utils.remaining_pressure(target_dict, todo_pressures_acc, todo_n_acc)
                remaining_dict = {'Value':remaining_pressure, 'N':remaining_n, 'Unit': unit}
                remaining_pressure_acc, remaining_n_acc , unit = self.utils.acc_pressure(remaining_dict, remaining_pressure_acc, remaining_n_acc)
            
            
            if len(remaining_pressure_acc) > 0:
                self.post(channel, "There following target pressure(s) remain:".format(no=len(remaining_pressure_acc)))
                for i, p in enumerate(remaining_pressure_acc):
                    self.post(channel, "№ {no}:  {p} {unit} (N = {n})".format(no=i+1,p=p, unit=unit, n=remaining_n_acc[i]))
            else:
                msg = "There are no remaining target pressures."
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
            self.post(channel, "*to[do pressure]*, *re[maining pressures]*, *cu[rrent target pressure]*, *ch[annel]*, *ga[s]*, *fu[llscales]* or *id[s]*.")

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