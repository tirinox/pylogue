from comm.menu_driver import MessageRequest, BotMenuBase, MenuOption


class BotMenu(BotMenuBase):
    def menu_manage_orders(self):
        yield from ()

    def menu_analytics(self):
        yield from ()

    def menu_bot(self):
        yield from ()

    def main_menu(self):
        item_index = yield from self.gen_select_option('➡ Main menu:', [
            [
                MenuOption('💵 Show balance', 'bal'),
                MenuOption('📔 Manage orders', 'orders')
            ],
            [
                MenuOption('🤖 Bot trading', 'bot'),
                MenuOption('📈 Analytics', 'analytics')
            ]
        ], compact_kbd=False)

        if item_index == 'bal':
            yield from ()
        elif item_index == 'orders':
            yield from self.menu_manage_orders()
        elif item_index == 'bot':
            yield from self.menu_bot()
        elif item_index == 'analytics':
            yield from self.menu_analytics()

    def root_generator(self):
        while True:
            yield from self.main_menu()