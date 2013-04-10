print "************************************************************************"
print "*** WebLogic AD Authenticator creation script - "
print "*** Follow the prompts as instructed.  Values in parenthesis are the "
print "*** default values that will be used if you simply press Enter."
print "************************************************************************"

def getPropertyValue( propertyName, displayMessage=None, defaultValue=None ):
  """Gets a property from the local namespace, then global namespace, and then prompts user
	
	Keyword arguments:
	propertyName             -- key to look up in namespaces, else what is displayed to user in prompt. If its a key, it must not contain spaces or spaces must be escaped in property file
	displayMessage (optional)-- message to display to user when prompting
	defaultValue   (optional)-- default value to use if value not found or user doesn't specify
    """
	if not propertyName:
		print "*** getPropertyValue: PropertyName is a required parameter"
		return ""
    	
	propertyValue = ""
	# put the default in the display message
	if not defaultValue:
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
	if not propertyValue:
		if displayMessage:
			msg = displayMessage
		else:
			msg = defaultMsg
		propertyValue = raw_input(msg)
  
	# use the default if one is specified and no value was found/specified
	if (not propertyValue) and defaultValue:
		propertyValue = defaultValue

	print propertyName + " is set to",propertyValue
	return propertyValue

providerName = "ADAuthenticator"
domain = ""  
ldapusr = "" 
ldappwd = "" 
ldapdomain = ""
ldapport = 389;
ldapSSL = False;
ldapbaseDN = ""

wluser = "weblogic"
wlpwd = ""
wladminserver = "" 

providerName = getPropertyValue("Security Provider Name", None, providerName)

# Collect Admin Server 
wladminserver = getPropertyValue("WebLogic Admin Server", "Please enter WebLogic Admin Server host and post (i.e. server:7101): ", None)
if wladminserver == "":
	print "*** ERROR: You must enter a WebLogic Admin Server and port."
	exit(-1)

# Collect WebLogic user 
wluser = getPropertyValue("WebLogic User", None, "weblogic")
# Collect WebLogic user password
wlpwd = getPropertyValue("WebLogic User Password", None, None)

# Collect WebLogic domain 
domain = getPropertyValue("WebLogic Domain", None, None)
if domain == "":
	print "*** ERROR: You must enter a domain."
	exit(-1)

# Collect LDAP Domain
ldapdomain = getPropertyValue("LDAP Domain", None, ldapdomain)

# Collect LDAP Port
ldapport = int(getPropertyValue( "LDAP Port", "Please enter LDAP port, 389 (default) or 636 (SSL): ", str(ldapport)))

# Collect LDAP SSL Enabled
ldapSSL = getPropertyValue("LDAP over SSL", "Enable LDAP over SSL, true or false (false): ", "false")
if ldapSSL.lower() == "true":
	ldapSSL = True
else:
	ldapSSL = False

# Collect LDAP Base DN
ldapbaseDN = getPropertyValue("LDAP Base DN", None, ldapbaseDN)

# Collect LDAP User
ldapusr = getPropertyValue("LDAP User (i.e user@domain.com)", None, None)

# Collect LDAP User password
ldappwd = getPropertyValue("LDAP User Password", None, None)

if ldapusr == "" or ldappwd == "" :
	print "*** ERROR: You must enter an LDAP username and password."
	exit(-1)
	
connect(wluser, wlpwd, wladminserver)

edit()

# make the default authenticator sufficient
startEdit()
cd('/SecurityConfiguration/' + domain + '/Realms/myrealm/AuthenticationProviders/DefaultAuthenticator')
cmo.setControlFlag('SUFFICIENT')

activate()

startEdit()
cd('/SecurityConfiguration/' + domain + '/Realms/myrealm')
cmo.createAuthenticationProvider(providerName, 'weblogic.security.providers.authentication.ActiveDirectoryAuthenticator')

cd('/SecurityConfiguration/' + domain + '/Realms/myrealm/AuthenticationProviders/' + providerName)
cmo.setControlFlag('SUFFICIENT')
cmo.setUseRetrievedUserNameAsPrincipal(true)

activate()

startEdit()

cmo.setUserNameAttribute('sAMAccountName')
cmo.setPrincipal(ldapusr)
cmo.setHost(ldapdomain)
cmo.setPort(ldapport)
cmo.setSSLEnabled(ldapSSL)
cmo.setAllUsersFilter('(&(sAMAccountName=*)(objectclass=user))')
cmo.setAllGroupsFilter('(&(sAMAccountName=*)(objectclass=group))')
cmo.setGroupFromNameFilter('(&(sAMAccountName=%g)(objectclass=group))')
cmo.setCredential(ldappwd)
cmo.setGroupBaseDN(ldapbaseDN)
cmo.setUserFromNameFilter('(&(sAMAccountName=%u)(objectclass=user))')
cmo.setStaticGroupNameAttribute('sAMAccountName')
cmo.setUserBaseDN(ldapbaseDN)

# prevents cyclically nested AD groups from causing the JVM to seg fault (kinda bad)
print "*** Limiting nested group membership searching to 25 levels..."
cmo.setGroupMembershipSearching('limited')
cmo.setMaxGroupMembershipSearchLevel(25)

activate()

startEdit()

cd('/SecurityConfiguration/' + domain + '/Realms/myrealm')
set('AuthenticationProviders',jarray.array([ObjectName('Security:Name=myrealm'+providerName), ObjectName('Security:Name=myrealmDefaultAuthenticator'), ObjectName('Security:Name=myrealmDefaultIdentityAsserter')], ObjectName))

save()
activate()

print "************************************************************************"
print "*** Successfully created authentication provider. Please restart your server(s)."
print "************************************************************************"

disconnect()
