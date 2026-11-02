extends SceneTree

func _initialize() -> void:
	var checks := {
		"display/window/size/viewport_width": 320,
		"display/window/size/viewport_height": 224,
		"display/window/stretch/mode": "viewport",
		"display/window/stretch/aspect": "keep",
		"rendering/textures/canvas_textures/default_texture_filter": 0,
		"physics/common/physics_ticks_per_second": 60,
		"physics/common/max_physics_steps_per_frame": 8,
	}
	var ok := true
	for key in checks.keys():
		var expected = checks[key]
		var actual = ProjectSettings.get_setting(key, "<UNSET>")
		var pass_ = (actual == expected)
		if not pass_:
			ok = false
		print("%s -> %s (esperado %s) %s" % [key, actual, expected, "OK" if pass_ else "FALLO"])
	print("RESULTADO: %s" % ("PASS" if ok else "FAIL"))
	quit()
