extends SceneTree
## Paso 0.3 ampliado: cada acción tiene teclado y mando; disparo/granada/melee también ratón;
## y existen las teclas de depuración F1-F7.

func _initialize() -> void:
	var expected := {
		"move_left": {"physical_keycode": [KEY_A, KEY_LEFT], "axis": [JOY_AXIS_LEFT_X], "button": [JOY_BUTTON_DPAD_LEFT]},
		"move_right": {"physical_keycode": [KEY_D, KEY_RIGHT], "axis": [JOY_AXIS_LEFT_X], "button": [JOY_BUTTON_DPAD_RIGHT]},
		"aim_up": {"physical_keycode": [KEY_W, KEY_UP], "axis": [JOY_AXIS_LEFT_Y], "button": [JOY_BUTTON_DPAD_UP]},
		"aim_down": {"physical_keycode": [KEY_S, KEY_DOWN], "axis": [JOY_AXIS_LEFT_Y], "button": [JOY_BUTTON_DPAD_DOWN]},
		"jump": {"physical_keycode": [KEY_SPACE], "button": [JOY_BUTTON_A]},
		"shoot": {"physical_keycode": [KEY_J], "button": [JOY_BUTTON_X], "axis": [JOY_AXIS_TRIGGER_RIGHT], "mouse": [MOUSE_BUTTON_LEFT]},
		"grenade": {"physical_keycode": [KEY_K], "button": [JOY_BUTTON_B], "mouse": [MOUSE_BUTTON_RIGHT]},
		"melee": {"physical_keycode": [KEY_L], "button": [JOY_BUTTON_Y], "mouse": [MOUSE_BUTTON_MIDDLE]},
		"pause": {"physical_keycode": [KEY_ESCAPE], "button": [JOY_BUTTON_START]},
		"debug_toggle": {"physical_keycode": [KEY_F1]},
		"debug_hitboxes": {"physical_keycode": [KEY_F2]},
		"debug_invincible": {"physical_keycode": [KEY_F3]},
		"debug_weapon": {"physical_keycode": [KEY_F6]},
		"debug_spawn": {"physical_keycode": [KEY_F7]},
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
		var found_mouse: Array = []
		for ev in events:
			if ev is InputEventKey:
				found_keys.append(ev.physical_keycode)
			elif ev is InputEventJoypadButton:
				found_buttons.append(ev.button_index)
			elif ev is InputEventJoypadMotion:
				found_axes.append(ev.axis)
			elif ev is InputEventMouseButton:
				found_mouse.append(ev.button_index)
		var want: Dictionary = expected[action_name]
		var ok := true
		for k in want.get("physical_keycode", []):
			ok = ok and found_keys.has(k)
		for b in want.get("button", []):
			ok = ok and found_buttons.has(b)
		for a in want.get("axis", []):
			ok = ok and found_axes.has(a)
		for m in want.get("mouse", []):
			ok = ok and found_mouse.has(m)
		if not ok:
			all_ok = false
		print("%s -> teclas=%s botones=%s ejes=%s raton=%s %s" % [action_name, found_keys, found_buttons, found_axes, found_mouse, "OK" if ok else "FALLO"])

	print("RESULTADO: %s" % ("PASS" if all_ok else "FAIL"))
	quit()
