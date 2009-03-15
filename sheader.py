# Hammer - header.py
# Copyright 2007 - 2008 Dietrich Epp <depp@zdome.net>
# This source code is licensed under the GNU General Public License,
# Version 3. See gpl-3.0.txt for details.
import re
import os

cstart = '/*'
cend = '*/'

projectName = 'Spacestation Pheta'
name = 'Dietrich Epp <depp@zdome.net>'
license_gpl = [
	'This source code is licensed under the GNU General Public License,',
	'Version 3. See gpl-3.0.txt for details.'
]
license = []

copy = re.compile(r'\s*Copyright\s*([-\d\s,]*\d)')

getYear = re.compile(r'^(\d{4})-\d{2}-\d{2} \d{2}:\d{2}:\d{2} -\d{4}$')
def getFileModYears(filename):
	if not options.update_dates:
		return ()
	pin, pout = os.popen2(['git-log', '--pretty=format:%ci', filename])
	years = set()
	for line in pout:
		line = line.strip()
		match = getYear.match(line)
		if not match:
			raise Exception("Cannot parse git-log output: %r." % line)
		year = int(match.group(1))
		years.add(year)
	return years

def parseDates(dates):
	intDates = set()
	for dateRange in dates.split(','):
		if '-' in dateRange:
			start, end = tuple(dateRange.split('-'))
			start = int(start)
			end = int(end)
			intDates.update(range(start, end + 1))
		else:
			intDates.add(int(dateRange))
	return intDates

def formatDates(dates):
	ranges = []
	for date in sorted(dates):
		if ranges and ranges[-1][1] == date - 1:
			start, end = ranges.pop()
			end = date
		else:
			start, end = date, date
		ranges.append((start, end))
	rangeTexts = []
	for start, end in ranges:
		if end > start:
			rangeTexts.append('%s - %s' % (start, end))
		# rangeTexts.extend(['%s' % start, '%s' % end])
		else:
			rangeTexts.append('%s' % start)
	return ', '.join(rangeTexts)

def getOldCopyright(path, version):
	if os.system('svn cat -r %s "%s" > .temp' % (version, path)):
		result = None
	else:
		result = findCopyrightDate(list(file('.temp', 'r')))
	os.unlink('.temp')
	return result

def toMacroName(path):
	#if path.startswith('Common'):
	return '_'.join(path.split('/')).upper()
	#else:
	#	return None

def splitHeader(lines):
	if not lines or cstart not in lines[0]:
		return [], lines
	for n, line in enumerate(lines):
		if cend in line:
			end = n + 1
			break
	else:
		end = 0
	return lines[:end], lines[end:]

def splitGuard(lines):
	if (len(lines) >= 2 and
		lines[0].strip().startswith('#ifndef') and
		lines[1].strip().startswith('#define')):
		start = 2
		end = len(lines) - 1
		while end >= start:
			line = lines[end].strip()
			if line.startswith('#endif'):
				break
			end -= 1
			if not line:
				continue
			else:
				start = 0
				end = len(lines)
				break
		else:
			start = 0
			end = len(lines)
	else:
		start = 0
		end = len(lines)
	return lines[:start], lines[start:end], lines[end:]

def ask(question):
	question = '%s (y/n)? ' % question
	while 1:
		answer = raw_input(question)
		if answer.lower().startswith('y'):
			return True
		elif answer.lower().startswith('n'):
			return False
		print "don't understand answer %r" % answer

def findCopyrightDate(lines):
	for line in lines:
		match = copy.match(line)
		if match:
			return match.group(1)
	return None

def printDiffs(olds, news):
	for old, new in zip(olds, news):
		for n, (ol, nl) in enumerate(zip(old, new)):
			if ol != nl:
				print '- %s\n+ %s' % (ol.strip('\n'), nl.strip('\n'))
			else:
				print '  %s' % ol.strip('\n')
		if len(old) > len(new):
			for ol in old[len(new):]:
				print '- %s' % ol.strip('\n')
		elif len(new) > len(old):
			for nl in new[len(old):]:
				print '+ %s' % nl.strip('\n')

def processFile(path):
	if options.verbose:
		print "processing %r" % path
	base, ext = os.path.splitext(path)
	isHeader = (ext == '.h') and not path.lower().startswith('macosx')
	
	lines = list(file(path, 'rb'))
	
	header, lines = splitHeader(lines)
	guardStart, lines, guardEnd = splitGuard(lines)
	
	if isHeader:
		if not guardStart:
			print 'No guard found: %s' % path
			makeGuard = ask('Add guard')
		else:
			makeGuard = True
	else:
		makeGuard = False
	
	#dates = getOldCopyright(path, 225)
	#if not dates:
	dates = findCopyrightDate(header)
	if not dates:
		print 'No copyright found: %s' % path
		dates = set([2008])
	else:
		dates = parseDates(dates)
	dates.update(getFileModYears(path))
	dates = formatDates(dates)
	
	newHeader = [
		'/* %s - %s' % (projectName, path),
		'   Copyright %s %s' % (dates, name)
	] + [ '   ' + line for line in license ]
	newHeader[-1] += ' */'
	newHeader = [line + '\n' for line in newHeader]
	
	if makeGuard:
		mn = toMacroName(base) + '_H'
		newGuardStart = [
			'#ifndef %s\n' % mn,
			'#define %s\n' % mn,
		]
		newGuardEnd = ['#endif\n']
	else:
		newGuardStart = []
		newGuardEnd = []
	
	old = [header, guardStart, ['[BODY]\n'], guardEnd]
	new = [newHeader, newGuardStart, ['[BODY]\n'], newGuardEnd]
	if old != new:
		print 'CHANGES: %s' % path
		printDiffs(old, new)
		if ask('Apply'):
			out = file(path, 'wb')
			for line in newHeader + newGuardStart + lines + newGuardEnd:
				out.write(line)

exts = set(['c', 'cpp', 'm', 'mm', 'h'])

def processFilePath(path, explicit):
	root, filename = os.path.split(path)
	if filename.startswith('.'):
		if explicit:
			print "skipping %r" % path
		return
	filebase, ext = os.path.splitext(filename)
	if ext.startswith('.'):
		ext = ext[1:]
	if ext not in exts:
		if explicit:
			print "skipping %r" % path
		return
	processFile(os.path.normpath(path))

def processDirPath(top):
	for root, dirs, files in os.walk(top):
		dirs[:] = [dir for dir in dirs if not dir.startswith('.')]
		root = os.path.normpath(root)
		for file in files:
			if file.startswith('.'):
				continue
			fn, ext = os.path.splitext(file)
			if ext.startswith('.'):
				ext = ext[1:]
			if ext not in exts:
				continue
			if root:
				file = os.path.join(root, file)
			processFilePath(file, False)

def processPath(path):
	if os.path.isdir(path):
		processDirPath(path)
	elif os.path.isfile(path):
		processFilePath(path, True)
	else:
		raise Exception, "can't process %r" % path

if __name__ == '__main__':
	import sys
	from optparse import OptionParser
	parser = OptionParser()
	parser.add_option("-d", "--update-dates", dest="update_dates", help="update copyright dates", action="store_true", default=False)
	parser.add_option("-v", "--verbose", dest="verbose", help="verbose output", action="store_true", default=False)
	options, args = parser.parse_args()
	roots = args or ['.']
	roots = [os.path.normpath(root) for root in roots]
	for root in roots:
		if os.path.isabs(root):
			print "Error: absolute path %r" % root
			sys.exit(1)
	for root in roots:
		processPath(root)
