project(
	'badgr',
	'c',
	version : '0.1',
	default_options : [
		'c_std=c23',
		'warning_level=everything',
		'b_lto=true',
		'b_pie=true',
	],
)

add_project_arguments(
	'-Wno-padded',
	'-Wno-c99-extensions',
	'-Wno-c++-compat',
	'-Wno-vla',
	language : ['c'],
)

executable(
	'badgr-worker',
	c_args : ['-DALWAYS_WEBP=true'],
	sources : [
		'./worker.c',
		'./worker-sandbox.c',
	],
	implicit_include_directories : false,
	dependencies : [
		dependency('libseccomp', include_type : 'system'),
		dependency('MagickWand', include_type : 'system'),
		dependency('lcms2', include_type : 'system'),
	],
)

executable(
	'badgr-init',
	sources : [
		'./init.c',
	],
	implicit_include_directories : false,
)
