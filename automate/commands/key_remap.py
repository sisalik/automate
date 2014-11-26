from input_hook import Hook, send_combo


Hook.register("SCROLL", send_combo, ["HOME"])
Hook.register("LSHIFT + SCROLL", send_combo, ["RSHIFT + HOME"])
# Hook.register("LCONTROL + SCROLL", send_keys, [(win32con.VK_RCONTROL, win32con.VK_HOME)])
Hook.register("PAUSE", send_combo, ["END"])
Hook.register("LSHIFT + PAUSE", send_combo, ["RSHIFT + END"])
# Hook.register("LCONTROL + PAUSE", send_keys, [(win32con.VK_RCONTROL, win32con.VK_END)])

Hook.register("DECIMAL", send_combo, ["OEM_PERIOD"])
