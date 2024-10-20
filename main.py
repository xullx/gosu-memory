# /////////////////////////////////////////
# TAIKO RATE CONVERTER / ? UNTESTED OTHER MODES
# NAKABAMITV (pohmx) - DEVELOPMENT 2022
# https://www.surina.net/soundtouch/README.html#SoundStretch COMMANDS
# SEE ISSUE https://github.com/jiaaro/pydub/issues/645, to fix .ogg conversion crackling
# USING data from https://github.com/l3lackShark/gosumemory
# TO DO: 
# - ADD GUI
# - MOVE FILES
# issue:
# [fixed] WidescreenStoryboard:
# [pending] 3158947 slider big (timing issue)
# [pending] 195760 ValueError: could not convert string to float: '76277,0:0:0'
# [pending] syaron105: when scaling beatmap pattern doesn't fill properly [clean, newpattern, newbpm]
# /////////////////////////////////////////

from urllib.request import urlopen
import json
from pydub import AudioSegment
from pydub.utils import mediainfo
import shutil
import os
import wave
import subprocess
from decimal import Decimal
import sys
import re
import math
from itertools import groupby
from decimal import Decimal


# RUNNING
link = "http://localhost:24050/json"
one_pass = True
new_rate = 1.1
export_osu = ''
osu_is_loaded = False
mode = ['osu!', 'osu!taiko', 'osu!catch', 'osu!mania']
hide_bpm_from_version = True # hides bpm '(500bpm)'
debug_mode = False
show_new_settings = True # shows new difficulty changes in version
new_settings_string = '' # xd
sv_ez_mode = False
sv_ez_factor = 7/8 # EZ Mod nominal factor: 0.5 *pending video confirmation check
scale_od = True
clean_beatmap = False
fill_pattern = False
show_pattern = False
fill_pattern_start = 0
fill_pattern_end = 0
fill_pattern_pattern = 'kkkkdddd'


# NOT IMPLEMENTED
	# Force_OD = True
	# Force_OD_VALUE = 10
	# Rainbow_mode
	# MAX OD!!!!!!!!! DTHR 0.75X SV REDUCE
'''
	settings = {
		'sv_ez_mode':'False',
		'sv_ez_factor':'7/8',
		'scale_od':'True'
		'show_new_settings':'True',
		'hide_bpm_from_version':'True'
		}
'''
# Audio switches 
switches_quick = True
switches_no_anti_alias = True
switches_string = ''

# BEATMAP STRUCTURE
mapLines = []
bpm = 0
mapGeneral = { # osu file format v14
	# [General]
	'AudioFilename:':'',
	'AudioLeadIn:':'',
	'PreviewTime:':'',
	'Countdown:':'',
	'SampleSet:':'',
	'StackLeniency:':'',
	'Mode:':'',
	'LetterboxInBreaks:':'',
	'SpecialStyle:':'',
	'WidescreenStoryboard:':'',
	# [Editor]
	'Bookmarks:':'',
	'DistanceSpacing:':'',
	'BeatDivisor:':'',
	'GridSize:':'',
	'TimelineZoom:':'',
	# [Metadata]
	'Title:':'',
	'TitleUnicode:':'',
	'Artist:':'',
	'ArtistUnicode:':'',
	'Creator:':'',
	'Version:':'',
	'Source:':'',
	'Tags:':'',
	'BeatmapID:':'',
	'BeatmapSetID:':'',
	# [Difficulty]
	'HPDrainRate:':'',
	'CircleSize:':'',
	'OverallDifficulty:':'',
	'ApproachRate:':'',
	'SliderMultiplier:':'',
	'SliderTickRate:':''
}
mapGroups = {
	# [Group]
	'Events':[],
	'TimingPoints':[],
	'Colours':[],
	'HitObjects':[],
	'NewHitObjects':[],
}

###### stolen functions

def all_equal(iterable):
	g = groupby(iterable)
	return next(g, True) and not next(g, False)

def clamp(od):
	if od < 0: return 0 
	elif od > 11: return 11
	else: return od

###### end of stolen functions

def fillPattern(start, end, pattern):
	converted_pattern = []	
	for t in pattern:
		if t == 'd': converted_pattern.append('0')
		elif t == 'k': converted_pattern.append('8')
		elif t == 'D': converted_pattern.append('4')
		elif t == 'K': converted_pattern.append('12')
		else: converted_pattern.append('x')
	print(converted_pattern)
	x_y = "256, 192"
	time = start
	otype = "1"
	params = "0:0:0:0:"
	factor = 60
	while time <= end:	
		for hitsound in converted_pattern:	
			if hitsound != 'x':
				newObject = x_y + ", " + str(time) + ", " + otype + ", " + hitsound + ", " + params
				mapGroups['NewHitObjects'].append(newObject)
			time += factor

def getBpm():
	global bpm
	bpm_list = []
	for t in mapGroups['TimingPoints']:
		if t.split(",",1)[1][0] != '-':
			bpm_list.append(int(round(1/float(t.split(',')[1])*60000))) # round then convert

	# if there are multiple bpms but they are all the same it will not show in version name '(500bpm)'
	if all_equal(bpm_list) == True:
		bpm = bpm_list[0]

	if len(bpm_list) == 1:
		bpm = bpm_list[0]
	# IF THERE ARE MORE BPMS DONT CARE (maybe add in the future)
	print("BPM: ",bpm)

def readOsu(osuFile):
	global mapLines
	global mapGroups
	capture = False

	# openfile
	with open(osuFile, 'r', encoding="utf8") as mapFile:
		mapLines = mapFile.readlines()
	
	# Get parameters from beatmap
	for line in mapLines:
		for key in mapGeneral:
			if key in line:
				mapGeneral[key] = line.split(":")[1].rstrip("\n").lstrip()
	
	# Read [Events]
	for line in mapLines:			
		if '[' in line:
			capture = False
		if capture:
			mapGroups['Events'].append(line.rstrip("\n"))
		if '[Events]' in line:
			capture = True
	mapGroups['Events'] = [x for x in mapGroups['Events'] if x]

	# Read [Timing Points]
	for line in mapLines:		
		if '[' in line:
			capture = False
		if capture:			
			mapGroups['TimingPoints'].append(line.rstrip("\n"))
		if '[TimingPoints]' in line:
			capture = True
	mapGroups['TimingPoints'] = [x for x in mapGroups['TimingPoints'] if x]

	# Read [Colours]
	for line in mapLines:		
		if '[' in line:
			capture = False
		if capture:			
			mapGroups['Colours'].append(line.rstrip("\n"))
		if '[Colours]' in line:
			capture = True
	mapGroups['Colours'] = [x for x in mapGroups['Colours'] if x]

	# Read [HitObjects]
	for line in mapLines:
		if capture:
			mapGroups['HitObjects'].append(line.rstrip("\n"))
		if '[HitObjects]' in line:
			capture = True
	capture = False
	mapGroups['HitObjects'] = [x for x in mapGroups['HitObjects'] if x]

def changeTiming():

	# BREAK PERIODS FIX
	# list items that come after '//Break Periods' until '//Storyboard Layer 0 (Background)' is reached
	# change in place ** review other changes why they are not in place such as timingPoints and hitObjects

	index_start, index_end = mapGroups['Events'].index('//Break Periods'), mapGroups['Events'].index('//Storyboard Layer 0 (Background)')
	
	for i, t in enumerate(mapGroups['Events']):
		if i > index_start and i < index_end:
			separate = t.split(',')
			separate[1], separate[2] = str(round(float(separate[1])/new_rate)), str(round(float(separate[2])/new_rate)) # round, although idk why i floated it
			separate = ",".join(separate)
			mapGroups['Events'][i] = separate

	# TIMING POINTS

	newTiming = []

	for timingPoint in mapGroups['TimingPoints']:
		if timingPoint.split(",",1)[1][0] != '-': # negative symbol
			newBpm = str(round(float(timingPoint.split(",",1)[1].split(",",1)[0]) / new_rate, 11)) # ROUND??????? WHY? CHECK IF THIS FIXES KATACHEH BUG, UNLIKELY BUT OK
			newOffset = str(int(float(timingPoint.split(",",1)[0].split(",",1)[0]) / new_rate))			
			fullTiming = newOffset + "," + newBpm + "," + timingPoint.split(",",1)[1].split(",",1)[1]
			newTiming.append(fullTiming)
		else:
			newOffset = str(int(float(timingPoint.split(",",1)[0].split(",",1)[0]) / new_rate))
			fullTiming = newOffset + "," + timingPoint.split(",",1)[1]
			newTiming.append(fullTiming)

	mapGroups['TimingPoints'] = []

	for override in newTiming:
		mapGroups['TimingPoints'].append(override)

	# HITOBJECTS

	for hitObject in mapGroups['HitObjects']:

		# hitObject normalised
		
		x_y_time_type_hitsound = [ x for x in hitObject.split(",",5) ][:5]
		objectParams = ''
		hitSample = ''
		is_mania_bug = False

		# Check A1 for explanation

		if hitObject[-1] == ':':
			hitSample = hitObject[::-1][:8][::-1]
			if hitObject[:len(hitObject)-8][-1] == ':': # Mania bug? objectParams ends with : instead of colon, catch.
				is_mania_bug = True
			wo_hitSample = hitObject[:len(hitObject)-9]
			if (len(wo_hitSample.split(",",5))) > 5:
				objectParams = wo_hitSample.split(",",5)[-1]
		else:
			if (len(hitObject.split(",",5))) > 5:
				objectParams = hitObject.split(",",5)[-1]

		# Hold-X-X-X-Spinner-NewCombo-Slider-Hitcircle (0,1,2,3,4,5,6,7 bit)
		bit_mask = format(int(x_y_time_type_hitsound[3]), '08b')
		
		# Hit circle
		if bit_mask[7] == '1':
			x_y_time_type_hitsound[2] = float(x_y_time_type_hitsound[2])/new_rate

		# Spinner
		if bit_mask[4] == '1':
			x_y_time_type_hitsound[2] = float(x_y_time_type_hitsound[2])/new_rate
			objectParams = float(objectParams)/new_rate

		# Slider Big 
		# Slider
		# x,y,time,type,hitSound,Sliderdata,repeat,osuPixelsLength(endtime)**DONT APPLY RATE HERE**
		if bit_mask[6] == '1':
			x_y_time_type_hitsound[2] = float(x_y_time_type_hitsound[2])/new_rate

		# Hold Note
		if bit_mask[0] == '1':
			x_y_time_type_hitsound[2] = float(x_y_time_type_hitsound[2])/new_rate
			objectParams = float(objectParams)/new_rate

		# Prepare string

		x_y_time_type_hitsound[2] = str(x_y_time_type_hitsound[2])
		objectParams = str(objectParams)

		if objectParams != '': 
			objectParams = ',' + objectParams

		if hitSample != '':
			if is_mania_bug is False:
				hitSample = ',' + hitSample
			else: 
				hitSample = ':' + hitSample

		newObject = ','.join(x_y_time_type_hitsound) + objectParams + hitSample
		mapGroups['NewHitObjects'].append(newObject)
		
	# BOOKMARKS

	bookmarksNew = []

	if mapGeneral['Bookmarks:'].split(",") != ['']:
		for bookmark in mapGeneral['Bookmarks:'].split(","):
			bookmarksNew.append(str(int(int(bookmark) / new_rate)))
		mapGeneral['Bookmarks:'] = ",". join(bookmarksNew)

def changeDifficulty():
	global new_settings_string
	global new_rate

	if scale_od == True:
		od = float(mapGeneral['OverallDifficulty:'])
		new_bpm_ms = (Decimal('-6.0') * Decimal(od) + Decimal('79.5')) / Decimal(new_rate)
		new_bpm_od = (Decimal('79.5') - new_bpm_ms) / Decimal('6.0')
		new_bpm_od = round(new_bpm_od, 1)
		clamped_new_od = clamp(new_bpm_od)
		mapGeneral['OverallDifficulty:'] = str(clamped_new_od)
		new_settings_string += ' od:scaled'

	if sv_ez_mode == True:
		original_sv = float(mapGeneral['SliderMultiplier:'])
		new_sv = original_sv * sv_ez_factor
		mapGeneral['SliderMultiplier:'] = str(new_sv)
		new_settings_string += ' sv:ez'

	if show_pattern == True:
		new_settings_string += ' ' + fill_pattern_pattern

def createMap(audio, rate):

	global export_osu	

	if bpm != 0 and hide_bpm_from_version == False:
		mapGeneral['Version:'] = mapGeneral['Version:'] + ' [' + str(float(rate)) + 'x (' + str(bpm) + 'bpm)'
	else:
		mapGeneral['Version:'] = mapGeneral['Version:'] + ' [' + str(float(rate)) + 'x'
	if show_new_settings == True:
		mapGeneral['Version:'] = mapGeneral['Version:'] + new_settings_string + ']'

	mapGeneral['AudioFilename:'] = audio
	if mapGeneral['PreviewTime:'] != '-1': #?
		mapGeneral['PreviewTime:'] = str(int(int(mapGeneral['PreviewTime:']) / new_rate))

	mapGeneral['Tags:'] += ' nimi-trainer'
	newMap = ['osu file format v14','','[General]']
	general = [
		'AudioFilename:',
		'AudioLeadIn:',
		'PreviewTime:',
		'Countdown:',
		'SampleSet:',
		'StackLeniency:',
		'Mode:',
		'LetterboxInBreaks:',
		'SpecialStyle:',
		'WidescreenStoryboard:'
		]
	editor = [
		'Bookmarks:',
		'DistanceSpacing:',
		'BeatDivisor:',
		'GridSize:',
		'TimelineZoom:'
	]
	metadata = [
		'Title:',
		'TitleUnicode:',
		'Artist:',
		'ArtistUnicode:',
		'Creator:',
		'Version:',
		'Source:',
		'Tags:',
		'BeatmapID:',
		'BeatmapSetID:'
	]
	difficulty = [
		'HPDrainRate:',
		'CircleSize:',
		'OverallDifficulty:',
		'ApproachRate:',
		'SliderMultiplier:',
		'SliderTickRate:'
	]
	
	# REMOVE EMPTY DATA
	# Remove from above list, not from raw data dictionary

	# GENERAL

	if len(mapGeneral['AudioFilename:']) == 0: general.remove('AudioFilename:') 
	if len(mapGeneral['AudioLeadIn:']) == 0: general.remove('AudioLeadIn:') 
	if len(mapGeneral['PreviewTime:']) == 0: general.remove('PreviewTime:') 
	if len(mapGeneral['Countdown:']) == 0: general.remove('Countdown:') 
	if len(mapGeneral['SampleSet:']) == 0: general.remove('SampleSet:') 
	if len(mapGeneral['StackLeniency:']) == 0: general.remove('StackLeniency:') 
	if len(mapGeneral['Mode:']) == 0: general.remove('Mode:') 
	if len(mapGeneral['LetterboxInBreaks:']) == 0: general.remove('LetterboxInBreaks:') 
	if len(mapGeneral['SpecialStyle:']) == 0: general.remove('SpecialStyle:')
	if len(mapGeneral['WidescreenStoryboard:']) == 0: general.remove('WidescreenStoryboard:')

	# EDITOR

	if len(mapGeneral['Bookmarks:']) == 0: editor.remove('Bookmarks:') 
	if len(mapGeneral['DistanceSpacing:']) == 0: editor.remove('DistanceSpacing:')
	if len(mapGeneral['BeatDivisor:']) == 0: editor.remove('BeatDivisor:')
	if len(mapGeneral['GridSize:']) == 0: editor.remove('GridSize:')
	if len(mapGeneral['TimelineZoom:']) == 0: editor.remove('TimelineZoom:')

	# METADATA

	if len(mapGeneral['Title:']) == 0: metadata.remove('Title:')
	if len(mapGeneral['TitleUnicode:']) == 0: metadata.remove('TitleUnicode:')
	if len(mapGeneral['Artist:']) == 0: metadata.remove('Artist:')
	if len(mapGeneral['ArtistUnicode:']) == 0: metadata.remove('ArtistUnicode:')
	if len(mapGeneral['Creator:']) == 0: metadata.remove('Creator:')
	if len(mapGeneral['Version:']) == 0: metadata.remove('Version:')
	if len(mapGeneral['Source:']) == 0: metadata.remove('Source:')
	if len(mapGeneral['Tags:']) == 0: metadata.remove('Tags:')
	if len(mapGeneral['BeatmapID:']) == 0: metadata.remove('BeatmapID:')
	if len(mapGeneral['BeatmapSetID:']) == 0: metadata.remove('BeatmapSetID:')
	
	# METADATA

	if len(mapGeneral['HPDrainRate:']) == 0: difficulty.remove('HPDrainRate:')
	if len(mapGeneral['CircleSize:']) == 0: difficulty.remove('CircleSize:')
	if len(mapGeneral['OverallDifficulty:']) == 0: difficulty.remove('OverallDifficulty:')
	if len(mapGeneral['ApproachRate:']) == 0: difficulty.remove('ApproachRate:')
	if len(mapGeneral['SliderMultiplier:']) == 0: difficulty.remove('SliderMultiplier:')
	if len(mapGeneral['SliderTickRate:']) == 0: difficulty.remove('SliderTickRate:')

	for v in general:
		newMap.append(str(v+' '+mapGeneral[v]))
	newMap.append('')

	newMap.append('[Editor]')
	for v in editor:
		newMap.append(str(v+' '+mapGeneral[v]))
	newMap.append('')

	newMap.append('[Metadata]')
	for v in metadata:
		newMap.append(str(v+mapGeneral[v]))
	newMap.append('')

	newMap.append('[Difficulty]')
	for v in difficulty:
		newMap.append(str(v+mapGeneral[v]))
	newMap.append('')

	newMap.append('[Events]')
	for v in mapGroups['Events']:
		newMap.append(v)
	newMap.append('')

	newMap.append('[TimingPoints]')
	for v in mapGroups['TimingPoints']:
		newMap.append(v)
	newMap.append('')

	# REMOVE EMPTY HEADERS

	if len(mapGroups['Colours']) != 0:
		newMap.append('[Colours]')
		for v in mapGroups['Colours']:
			newMap.append(v)
		newMap.append('')

	newMap.append('[HitObjects]')

	if clean_beatmap is True:
		mapGroups['NewHitObjects'] = []
	else:
		for o in mapGroups['NewHitObjects']:
			newMap.append(o)

	if fill_pattern is True:
		fillPattern(fill_pattern_start, fill_pattern_end, fill_pattern_pattern)
		for o in mapGroups['NewHitObjects']:
			newMap.append(o)
	
	newMap.append('')

	invalid = '<>:"/\|?*'
	filename = mapGeneral['Artist:'] + ' - ' + mapGeneral['Title:'] + ' (' + mapGeneral['Creator:'] + ') ' + '[' + mapGeneral['Version:'] +  '].osu'
	export_osu = "".join( x for x in filename if (x not in invalid)).replace('"','') # No illegal

	with open(export_osu,'w', encoding="utf8") as f:
		for line in newMap:
			f.write(line+'\n')
	
while True:
	# CHECK CONNECTION (IF DATA EXISTS.)
	try:
		json_data = str(urlopen(link).read().decode('utf-8'))
		json_converted = json.loads(json_data, strict=False)
		try:				
			# PATHS
			song_folder = json_converted['settings']['folders']['songs']
			path_folder = json_converted['menu']['bm']['path']['folder']
			path_beatmap = json_converted['menu']['bm']['path']['file']	
			path_audio = json_converted['menu']['bm']['path']['audio']	
			full_beatmap_path = song_folder + "\\" + path_folder + "\\" + path_beatmap
			full_folder_path = song_folder + "\\" + path_folder
			full_beatmap_path_audio = song_folder + "\\" + path_folder + "\\" + path_audio
			# METADATA
			metadata = json_converted['menu']['bm']['metadata']
			# SWITCH
			osu_is_loaded = True
		except:
			print('gosumemory-error: ', json_converted['error'])
	except:
		print("taiko-trainer-error: can't stablish connection to gosumemory.")

	if one_pass is True and osu_is_loaded is True:
		one_pass = False
		if debug_mode is False:

			# AUDIO FILE CREATION
			# COPY TO ROOT, CONVERT .MP3 & .OGG TO .WAV
			# CALCULATION, NAMING OF FILE

			shutil.copyfile(full_beatmap_path_audio, path_audio)
			path_wav = os.path.splitext(path_audio)[0] + ".wav"
			path_mp3 = os.path.splitext(path_audio)[0] + ".mp3"

			if os.path.splitext(path_audio)[1] == '.mp3':
				try:
					sound = AudioSegment.from_file(path_audio, 'mp3') # NORMAL READ			
					sound.export(path_wav, format="wav")
				except:
					sound = AudioSegment.from_file(path_audio) # EXCEPTED READ // CAN'T FIND CONTAINER
					sound.export(path_wav, format="wav")

			elif os.path.splitext(path_audio)[1] == '.ogg':	# convert to mp3 first bc .wav is crackling	
				print('file is .ogg')
				# to mp3
				sound = AudioSegment.from_file(path_audio, 'ogg')
				sound.export(path_mp3, format="mp3")
				print('converted .ogg to .mp3')
				# to wav
				sound = AudioSegment.from_file(path_mp3, 'mp3')
				sound.export(path_wav, format="wav")
				print('converted .mp3 to .wav')
			
			bpm_multiplier = (new_rate - 1) * 100
			newAudio = os.path.splitext(path_audio)[0] + '-' +  str(float(new_rate)) + 'x.wav' 

			# SETS SOUNDSTRETCHER OPTIONS
			# CREATES FILE, REMOVES OLD .WAV
			
			if switches_quick: switches_string += ' -quick'			
			if switches_no_anti_alias: switches_string += ' -naa'

			switches = 'soundstretch.exe "' + sys.path[0] + '\\' + path_wav + '" "' + sys.path[0] + '\\' + newAudio + '"' + switches_string + ' -tempo=' + str(bpm_multiplier)
			print(switches)
			subprocess.run(switches, shell=True) # MAYBE CHECK RETURN
			
			mp3 = AudioSegment.from_file(newAudio)
			mp3.export(os.path.splitext(newAudio)[0]+'.mp3', format="mp3", bitrate="320k")
			newAudio_mp3 = os.path.splitext(newAudio)[0]+'.mp3'

			# BEATMAP CREATION
			readOsu(full_beatmap_path)
			changeTiming()
			getBpm()
			changeDifficulty()
			createMap(newAudio_mp3, new_rate)

			# COPY TO ORIGINAL FOLDER
			shutil.copyfile(newAudio, full_folder_path + '\\' + newAudio_mp3)
			shutil.copyfile(export_osu, full_folder_path + '\\' + export_osu)
			
			''' REMOVE TEMP files'''
			try:
				os.remove(path_mp3)
			except:
				print('no mp3 was generated')
			os.remove(path_wav)
			#os.remove(path_audio)
			os.remove(newAudio)
			os.remove(newAudio_mp3)			
			os.remove(export_osu)

			print('taiko-trainer-info: created file', export_osu, newAudio_mp3)
		else: # Debug Mode

			print('Debug mode -on')
			readOsu(full_beatmap_path)

			mode = ['osu!', 'osu!taiko', 'osu!catch', 'osu!mania']

			# print(mode[(int(mapGeneral["Mode:"]))])
			# x,y,time,type,hitSound,objectParams,hitSample
			# attempt to normalise
			
			if mode[(int(mapGeneral["Mode:"]))] == 'osu!taiko':
				print('osu!taiko')

			errors = 0

			for hitObject in mapGroups['HitObjects']:

				x_y_time_type_hitsound = [ x for x in hitObject.split(",",5) ][:5]
				objectParams = ''
				hitSample = ''
				is_mania_bug = False

				# i don't want to explain but ok
				# checks if there is hitSample data (0:0:0:0:) -> always ends with ':'
				# else check if there is objectParameters and no hitSample (usually not true but just bc i don't know)
				# if there is hitSample then cut the hitObject string up until hitSample and split the original into 6 (5+1 comma), if there's
				# more than 5, that is the objectParameters

				if hitObject[-1] == ':':
					hitSample = hitObject[::-1][:8][::-1]
					if hitObject[:len(hitObject)-8][-1] == ':': # Mania bug? objectParams ends with : instead of colon, catch.
						is_mania_bug = True
					wo_hitSample = hitObject[:len(hitObject)-9]
					if (len(wo_hitSample.split(",",5))) > 5:
						objectParams = wo_hitSample.split(",",5)[-1]
				else:
					if (len(hitObject.split(",",5))) > 5:
						objectParams = hitObject.split(",",5)[-1]

				if objectParams != '':
					objectParams = ',' + objectParams

				if hitSample != '':
					if is_mania_bug is False:
						hitSample = ',' + hitSample
					else: 
						hitSample = ':' + hitSample

				restring = ','.join(x_y_time_type_hitsound) + objectParams + hitSample
				print(hitObject)
				print(restring)
				if hitObject == restring:
					print('check passed')
				else:
					print('check failed')
					errors += 1

				# Hold-X-X-X-Spinner-NewCombo-Slider-Hitcircle (0,1,2,3,4,5,6,7 bit)
				bit_mask = format(int(x_y_time_type_hitsound[3]), '08b')[5]

				print('-----------')

			print(str(len(mapGroups['HitObjects'])) + ' objects checked!! test finished, errors: ', errors)
