extends SceneTree

func _initialize() -> void:
	var expected := {
		"move_left": {"physical_keycode": [KEY_A, KEY_LEFT], "axis": [JOY_AXIS_LEFT_X], "button": [JOY_BUTTON_DPAD_LEFT]},
		"move_right": {"physical_keycode": [KEY_D, KEY_RIGHT], "axis": [JOY_AXIS_LEFT_X], "button": [JOY_BUTTON_DPAD_RIGHT]},
		"aim_up": {"physical_keycode": [KEY_W, KEY_UP], "axis": [JOY_AXIS_LEFT_Y], "button": [JOY_BUTTON_DPAD_UP]},
		"aim_down": {"physical_keycode": [KEY_S, KEY_DOWN], "axis": [JOY_AXIS_LEFT_Y], "button": [JOY_BUTTON_DPAD_DOWN]},
		"jump": {"physical_keycode": [KEY_SPACE], "button": [JOY_BUTTON_A]},
		"shoot": {"physical_keycode": [KEY_J], "button": [JOY_BUTTON_X]},
		"grenade": {"physical_keycode": [KEY_K], "button": [JOY_BUTTON_B]},
		"melee": {"physical_keycode": [KEY_L], "button": [JOY_BUTTON_Y]},
		"pause": {"physical_keycode": [KEY_ESCAPE], "button": [JOY_BUTTON_START]},
		"debug_toggle": {"physical_keycode": [KEY_F1]},
	}

	var all_ok := true
	for action_name in expected.keys():
		if not InputMap.has_action(action_name):
			print("%s -> FALTA LA ACCION" % action_name)
			all_ok = false
			continue

		var events := InputMap.action_get_events(action_name)
		var found_keys: Array = []
		var found_buttons: Array = []
		var found_axes: Array = []
		for ev in events:
			if ev is InputEventKey:
				found_keys.append(ev.physical_keycode)
			elif ev is InputEventJoypadButton:
				found_buttons.append(ev.button_index)
			elif ev is InputEventJoypadMotion:
				found_axes.append(ev.axis)

		var want: Dictionary = expected[action_name]
		var ok := true
		if want.has("physical_keycode"):
			for k in want["physical_keycode"]:
				if not found_keys.has(k):
					ok = false
		if want.has("button"):
			var wanted_buttons = want["button"]
			if typeof(wanted_buttons) != TYPE_ARRAY:
				wanted_buttons = [wanted_buttons]
			for b in wanted_buttons:
				if not found_buttons.has(b):
					ok = false
		if want.has("axis"):
			for a in want["axis"]:
				if not found_axes.has(a):
					ok = false

		if not ok:
			all_ok = false
		print("%s -> teclas=%s botones=%s ejes=%s %s" % [action_name, found_keys, found_buttons, found_axes, "OK" if ok else "FALLO"])

	print("RESULTADO: %s" % ("PASS" if all_ok else "FAIL"))
	quit()
