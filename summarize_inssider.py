#
# InSSIDer GPX to Summary GPX including ability to merge
#   data from multiple InSSIDer GPX files
# 
# May 2012 by Stephen Genusa http://development.genusa.com
# 
# Written for Python 2.7x
#
# 

import xml.dom.minidom
import cPickle
import os.path

lst_WAPs = []
intMaxWPTsPerRead = 20000	# Max waypoints to process in a single chunk 
							# (due to machine memory limits of parsing the
							# XML)

def LoadWAPs (strWAPsFileName):
	# Load any existing WAP data so that multiple inSSIDer files 
	# can be merged into a single summary GPX file
	global lst_WAPs
	if os.path.exists(strWAPsFileName):
		filPickle = open(strWAPsFileName, 'r')
		pickler = cPickle.Unpickler(filPickle)
		lst_WAPs = pickler.load()
		filPickle.close()
		print 'WAP Data Loaded ...'
	else:
		print 'No Existing WAP Data ...'

def SaveWAPs (strWAPsFileName):
	# Pickle and save the WAP list
	filPickle = open(strWAPsFileName, 'w')
	pickler = cPickle.Pickler(filPickle)
	pickler.dump(lst_WAPs)
	filPickle.close()
	print 'WAP Data Saved...'


def getText(nodelist):
	# Transform nodelist into text if TEXT_NODE elements exist in nodelist
	rc = []
	for node in nodelist:
		if node.nodeType  == node.TEXT_NODE:
			rc.append(node.data)
	return ''.join(rc)

def getListPositionForWAP (strBSSID, strSSID):
	# Locate the given BSSID/SSID list element or return -1 if not found
	global lst_WAPs
	intCount = 0
	intRes = -1
	for itmWAP in lst_WAPs:
		if itmWAP[0] == strBSSID and itmWAP[1] == strSSID:
			intRes = intCount
			break			
		intCount += 1
	return intRes


def handleWaypoint(waypoint):
	# Process individual waypoints
	global lst_WAPs
	# desc = waypoint.getElementsByTagName('desc')[0]
	t_lat = waypoint.getAttribute('lat')
	t_lon = waypoint.getAttribute('lon')
	# Toss waypoints that have no lat/lon or that contain invalid GPS data
	if t_lat != "" and t_lat != "36":
		t_ssid = getText(waypoint.getElementsByTagName('SSID')[0].childNodes)
		t_bssid = getText(waypoint.getElementsByTagName('MAC')[0].childNodes)
		t_rssi = getText(waypoint.getElementsByTagName('RSSI')[0].childNodes)
		t_security = getText(waypoint.getElementsByTagName('security')[0].childNodes)	
		intLstPos = getListPositionForWAP(t_bssid, t_ssid)
		# If the SSID/BSSID do not appear in the list then add the waypoint
		if intLstPos == -1:
			lst_WAPs.append([t_bssid, t_ssid, t_rssi, t_lat, t_lon, t_security])
			print t_ssid, t_bssid, 'added to summary'
		else:
			# The SSID/BSSID exist so make sure we keep the best rssi lat/lon waypoints
			if t_rssi < lst_WAPs[intLstPos][2]:
				print t_ssid, t_bssid, 'updated. Old rssi =', lst_WAPs[intLstPos][2], "- New rssi =", t_rssi
				lst_WAPs[intLstPos] = [t_bssid, t_ssid, t_rssi, t_lat, t_lon, t_security]
	
def handleWaypoints(waypoints):
	# Convenient "for loop" to loop through wpt elements
	intWaypoints = 0
	print 'Processing', len(waypoints), 'waypoints ...'
	for waypoint in waypoints:
		handleWaypoint(waypoint)
		intWaypoints += 1
	print 'Finished Processing', intWaypoints, 'waypoints ...'
	

def ReadWaypointFile(strFileName):
	# Read the inSSIDer GPX file in chunks if necessary and then individually
	# process those chunks
	# Warning: Written for and tested against only InSSIDer generated GPX files
	if os.path.exists(strFileName):
		print 'Loading waypoint file', strFileName, '...'		
		filGPXWaypoints = open(strFileName, 'r')
		# Read XML header line
		filGPXWaypoints.readline()
		# Read <gpx> line
		filGPXWaypoints.readline()
		intWPTCount = 0
		rc = []
		for strLine in filGPXWaypoints:
			strLine = strLine.rstrip()
			if strLine != '</gpx>':
				rc.append(strLine+'\n')
			if strLine.find('</wpt>') != -1:
				intWPTCount+= 1
			if strLine == '</gpx>' or intWPTCount == intMaxWPTsPerRead:
				print intWPTCount, 'waypoints loaded. Parsing XML for waypoints ...'
				rc.insert(0, '<gpx>\n')
				rc.insert(0, '<?xml version="1.0" encoding="utf-8"?>\n')
				rc.append('</gpx>')
				dom = xml.dom.minidom.parseString(''.join(rc))
				handleWaypoints(dom.getElementsByTagName('wpt'))
				rc = []
				intWPTCount = 0
		filGPXWaypoints.close()
			
def WriteSummaryWaypointFile (strFileName):
	filGPX = open(strFileName, 'w')
	filGPX.write('<?xml version="1.0" encoding="utf-8"?>\n<gpx>\n')
	for itmWAP in lst_WAPs:
		# Dump the lat/lon 
		filGPX.write('<wpt lat="' + itmWAP[3] + '" lon="' + itmWAP[4] + '">\n')
		# Dump the SSID and BSSID
		filGPX.write('<name>'+ itmWAP[1] + '\n' + itmWAP[0] + '\n')
		# Dump the Security Type and (best RSSI)
		filGPX.write(itmWAP[5] + ' (' + itmWAP[2] + ')</name>\n')
		filGPX.write('</wpt>\n')
	filGPX.write ('</gpx>\n')
	filGPX.close()
	print 'Unique BSSID/SSIDS = ', len(lst_WAPs)
	print 'Summary GPX file written ...'

		
# ------------------------------------------------------------------------------------	
# Loading and saving WAP data across different executions of this program is optional.
# You may want to uncomment LoadWAPs() and SaveWAPs()
# ------------------------------------------------------------------------------------	
# LoadWAPs ('waps.dat')
ReadWaypointFile('myinssiderfile.gpx')
WriteSummaryWaypointFile ('summary.gpx')
# SaveWAPs ('waps.dat')
