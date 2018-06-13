from comm.telegram import TelegramCommunicationBot
from telegram import Message
from util.misc import wlog, die, enumerate_2d_array
import traceback


class MessageResponse:
    def __init__(self, text, user_id):
        self.user_id = user_id
        self.text = str(text).strip()


class MessageRequest:
    pass


class MenuOption:
    def __init__(self, caption, key=None):
        self.caption = caption
        self.key = key


class BotMenuBase:
    def root_generator(self):
        yield from ()

    def __init__(self, bot: TelegramCommunicationBot):
        self.bot = bot
        self.user_id = None
        self.next_message = None
        self.buffer = []
        self.last_options = []
        self.last_hide_kb = False
        self.last_is_kbd_compact = False

    def flush(self):
        if self.buffer:
            full_message = '\n\n'.join(self.buffer)
            self.bot.send_message(user_id=self.user_id,
                                  message=full_message,
                                  hide_keyboard=self.last_hide_kb,
                                  options=self.last_options,
                                  resize_keyboard=self.last_is_kbd_compact)
            self.buffer = []

    def notify(self, text, hide_kb=False, options=list(), flush=False, compact_kbd=False):
        if self.user_id and text:
            self.last_hide_kb = hide_kb
            self.last_options = options
            self.last_is_kbd_compact = compact_kbd
            self.buffer.append(text)
            if flush or len(self.buffer) >= 4:
                self.flush()
        else:
            wlog("Warning: can't notify; you need set user_id and send a valid text")

    def notify_error(self, text):
        self.notify('{}\nType /quit or /q if you give up.'.format(text), flush=True)

    def set_next_message(self, msg: MessageRequest):
        self.next_message = msg

    def stop(self):
        raise StopIteration

    def gen_ask_until_validated(self, validator, text_on_fail='Try again.'):
        while True:
            r = yield MessageRequest()
            text = r.text
            if text in ['/quit', '/q']:
                self.notify('😤 Dialog stopped.')
                self.stop()
                return None

            value = validator(text)
            if value is None:
                if text_on_fail:
                    self.notify_error(text_on_fail)
            else:
                return value

    def gen_confirm(self, request_text: str, yes_option='Yes, I confirm', no_option='No, cancel please'):
        text = '🤝 Do you confirm this operation❓\n{}'.format(request_text)
        result = yield from self.gen_select_option(text, [
            MenuOption('✅ {}'.format(yes_option), 'yes'),
            MenuOption('🚫 {}'.format(no_option), 'no')
        ])
        return result == 'yes'

    def gen_select_option(self, request_text: str, options: list, compact_kbd=True) -> [str, int]:
        key_table = {}

        n_options = 0

        def extract_string_for_keyboard(item, index):
            if isinstance(item, MenuOption):
                text = item.caption
                key = item.key if item.key else index
            else:
                return 'error: each item must be a MenuOption instance'

            caption = '{}. {}'.format(index, text)

            key_table[str(index)] = key
            key_table[text] = key
            key_table[caption] = key
            key_table[key] = key

            nonlocal n_options
            n_options += 1

            return caption

        keyboard_numbered = enumerate_2d_array(options, 1, extract_string_for_keyboard)

        if n_options == 0:  # no options provided
            self.stop()
            return ''

        message_text = request_text
        while True:
            self.notify(message_text, options=keyboard_numbered, compact_kbd=compact_kbd)
            self.flush()
            answer = yield MessageRequest()
            answer_text = str(answer.text).strip()
            if answer_text in ['/quit', '0', 'q']:
                self.notify('😤 Dialog stopped.')
                self.stop()
                return ''
            else:
                if answer_text in key_table:
                    return key_table[answer_text]
                else:
                    message_text = '😡 Please select a valid option or send a number ' \
                                   'between 1 and {n}. Use /quit or 0 or q to exit. {orig_text}'.format(
                        orig_text=request_text,
                        n=n_options)


class BotMenuDriver:
    def set_user_id(self, user_id):
        self.menu.user_id = user_id

    def on_message(self, msg: Message):
        try:
            user_id = self.bot.user_id_from_msg(msg)
            self.set_user_id(user_id)
            text = msg.text
            self.gen.send(MessageResponse(text, user_id))
        except StopIteration:
            wlog('Restarting menu generator.')
            self.start_generator()
        except Exception as e:
            wlog('Menu exception: {}'.format(e))
            traceback.print_exc()

    def start_generator(self):
        self.gen = self.menu.root_generator()
        try:
            next(self.gen)
        except:
            wlog("Error! Couldn't start the menu generator")

    def attach_to_bot(self, bot: TelegramCommunicationBot):
        self.bot = bot
        self.bot.message_handler = self.on_message
        self.set_user_id(bot.get_allowed_chat())
        self.start_generator()

    def __init__(self, menu: BotMenuBase):
        self.bot = None
        self.menu = menu
        self.gen = None