# ### Running The Script #######################################################
# This script should be run from the DOMAIN_HOME directory. If it is not, the domain
# home can be provided via a property or entered via prompt.
# 
# > wlst createOracleJDBCDatasource.py
# > wlst -loadProperties datasource.properties createOracleJDBCDatasource.py
#
# or from within WLST, 
# wls:/offline> loadProperties('datasource.properties')
# wls:/offline> execfile('createOracleJDBCDatasource.py)
#
# ### Property File ############################################################
# All properties (except db password) can come from the properties file. Any missing
# required properties will be prompted for.
#
# prod_db - 
# database - DB Name
# user - DB User
# host - DB Host
# port - DB Port
# domain_home - weblogic domain home directory (optional, with escaped slashes)
#

from weblogic.descriptor import BeanAlreadyExistsException

print "************************************************************************"
print "*** Oracle JDBC Database Create Script "
print "*** Follow the prompts as instructed.  Values in parenthesis are the "
print "*** default values that will be used if you simply press Enter."
print "************************************************************************"

# ### FUNCTION - getPropertyValue ############################################## 
# 
# Gets a property from the local namespace, then global namespace, and then prompts
# the user lastly
# Inputs (all optional meaning you can pass in '' or None)
#   propertyName             : key to look up in namespaces, else what is displayed to user in prompt. 
#                              If its a key, it must not contain spaces or spaces must be escaped in property file
#   displayMessage (optional): message to display to user when prompting 
#   defaultValue   (optional): default value to use if value not found or user doesn't specify
#
def getPropertyValue( propertyName, displayMessage, defaultValue ):

  if propertyName == "" or propertyName is None:
		print "*** getPropertyValue: PropertyName is a required parameter"
		return ""
    	
	propertyValue = ""
	# put the default in the display message
	if defaultValue == '' or defaultValue is None:
		defaultMsg = "Please enter a value for " + propertyName + ": "
	else:
		defaultMsg = "Please enter a value for " + propertyName + " (" + defaultValue + "): "  	
  
	# check locals	
	if propertyName in locals():
		propertyValue = locals()[propertyName]
  
	# check globals
	elif propertyName in globals():
		propertyValue = globals()[propertyName]

	# if still not set, setup prompt message and query user
	if propertyValue == "" or propertyValue is None:
		if displayMessage != "" and displayMessage is not None:
			msg = displayMessage
		else:
			msg = defaultMsg
		propertyValue = raw_input(msg)
  
	# use the default if one is specified and no value was found/specified
	if (propertyValue == "" or propertyValue is None) and (defaultValue != "" and defaultValue is not None):
		propertyValue = defaultValue

	print propertyName + " is set to",propertyValue
	return propertyValue
	
ds_prod_db  = getPropertyValue('prod_db', None, None)
ds_host     = getPropertyValue('host', None, None)
ds_port     = getPropertyValue('port', None, '1521')
ds_database = getPropertyValue('database', None, None)
ds_user     = getPropertyValue('user', None, None)
ds_password = getPropertyValue('password','Enter password for ' + ds_user + ': ', None)

if connected == 'false':
	print "*** Attempting to connect to AdminServer..."
	# Determine the port for the Administration server
	domainHome = getPropertyValue('domain_home',"Please enter the domain home or press Enter to use the current directory:",'.')

	print "*** Reading domain configuration..."
	readDomain(domainHome)
	cd('Server/AdminServer')

	# Replace listen address with localhost if it is all local addresses
	listenAddress = str(get('ListenAddress'))
	if listenAddress == 'All Local Addresses':
	        listenAddress = 'localhost'

	admin_url = 't3://' + listenAddress + ':' + str(get('ListenPort'))
	
	closeDomain()

	# Connect to the Administration Server
	# In order to connect using this method, the WLST script must be run from the DOMAIN_HOME folder
	# of the domain you wish to modify.
	
	print "*** Connecting to AdminServer..."
	connect(url=admin_url, adminServerName='AdminServer')
	print "*** Connected to",domainName
elif isAdminServer == 'false':
	print "*** Error: You are connected to a server which is not an AdminServer. Please connect to an AdminServer first."
	exit(-1)
	
# Start an edit session
edit()
startEdit()

jdbc_url    = 'jdbc:oracle:thin:@' + ds_host + ':' + ds_port + ':' + ds_database
jndi_name_1 = 'jdbc.' + ds_database.lower() + '.' + ds_user.lower()
jndi_name_2 = 'jdbc.' + ds_prod_db.lower() + '.' + ds_user.lower()
ds_name     = ds_database.upper() + '.' + ds_user.upper()

print('*** JDBC System Resource Name: ' + ds_name)
print('*** JDBC URL: ' + jdbc_url)

try:
	cd('/')
	cmo.createJDBCSystemResource(ds_name)
	
	cd('/JDBCSystemResources/' + ds_name + '/JDBCResource/' + ds_name)
	cmo.setName(ds_name)
	
	cd('/JDBCSystemResources/' + ds_name + '/JDBCResource/' + ds_name + '/JDBCDataSourceParams/' + ds_name)
	set('JNDINames',jarray.array([String(jndi_name_1), String(jndi_name_2)], String))
	
	cd('/JDBCSystemResources/' + ds_name + '/JDBCResource/' + ds_name + '/JDBCDriverParams/' + ds_name)
	cmo.setUrl(jdbc_url)
	cmo.setDriverName('oracle.jdbc.xa.client.OracleXADataSource')
	cmo.setPassword(ds_password)
	
	cd('/JDBCSystemResources/' + ds_name + '/JDBCResource/' + ds_name + '/JDBCConnectionPoolParams/' + ds_name)
	cmo.setTestTableName('SQL SELECT 1 FROM DUAL\r\n\r\n')
	
	cd('/JDBCSystemResources/' + ds_name + '/JDBCResource/' + ds_name + '/JDBCDriverParams/' + ds_name + '/Properties/' + ds_name)
	cmo.createProperty('user')
	
	cd('/JDBCSystemResources/' + ds_name + '/JDBCResource/' + ds_name + '/JDBCDriverParams/' + ds_name + '/Properties/' + ds_name + '/Properties/user')
	cmo.setValue(ds_user)
	
	cd('/JDBCSystemResources/' + ds_name + '/JDBCResource/' + ds_name + '/JDBCDataSourceParams/' + ds_name)
	cmo.setGlobalTransactionsProtocol('TwoPhaseCommit')
	
	cd('/SystemResources/' + ds_name)
	
    print "*** Targeting datasource to just AdminServer..."
    set('Targets',jarray.array([ObjectName('com.bea:Name=AdminServer,Type=Server')], ObjectName))
	
except BeanAlreadyExistsException:
	print '*** Error: ' + ds_name + ' datasource already exists... Exiting.'
	cancelEdit('y')
	exit() 

# Activate the changes
save()
activate()

print "************************************************************************"
print "*** Successfully created datasource!"
print "************************************************************************"

# Disconnect from the Administration Server
disconnect()
