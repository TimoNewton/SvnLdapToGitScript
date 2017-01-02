import ldap
import getpass
import yaml

def read_config(config_file):
    """Open the external configuration file and read the appropriate variables"""
    with open(config_file, 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
    email_domain = cfg['default_email_domain'] #read the configured email domain
    ldap_config = cfg['ldap'] #get ldap configuration
    baseDN_list = [] #create empty list to populate with baseDN from file
    for section in ldap_config['user_context']:
        for item in ldap_config['user_context'][section]:
            baseDN_list.append(section + "=" + item)
    ldap_user_context={}
    ldap_user_context['baseDN'] = ",".join(baseDN_list)
    ldap_user_context['connection_string'] = ldap_config['connection_string']
    ldap_user_context['search_filter'] = ldap_config['search_filter']
    ldap_user_context['retrieve_attributes'] = retrieve_attributes = []
    for attribute in ldap_config['retrieve_attributes']:
        ldap_user_context['retrieve_attributes'].append(attribute)
    return email_domain, ldap_user_context


def create_author_file(svn_file,author_file_name, config_file):
    """Create an author file to move a subversion repository to git."""
    email_domain, ldap_user_context = read_config(config_file)
    svn_authors = load_svn_file(svn_file)
    uname = input("Please provide LDAP username")
    upass = getpass.getpass("LDAP password")
    ldap_users = load_ldap_user_info(uname, upass,ldap_user_context)
    git_author_file_entries = []
    for svn_author in svn_authors:
        key = svn_author.strip().lower()
        author_name, author_email = '',''
        ldap_entry = None
        if(key in ldap_users):
            ldap_entry = ldap_users[key]
        elif(key+"@"+email_domain in ldap_users):
            ldap_entry = ldap_users[key+"@"+email_domain]
        if(ldap_entry):
            author_name = ldap_entry['displayName'][0].decode()
            if('mail' in ldap_entry):
                author_email = ldap_entry['mail'][0].decode()
            else:
                author_email = key + "@" + email_domain
        else:
            print(key + " not found in ldap")
            author_email = key + "@" + email_domain
        git_author_file_entries.append(key + ' = ' + author_name + ' <' + author_email + '>')
    write_author_file(author_file_name,git_author_file_entries)
    return git_author_file_entries

def write_author_file(author_file_name,author_entries):
    author_file = open(author_file_name,'w')
    for entry in author_entries:
        author_file.write(entry + '\n')
    author_file.close()

def load_svn_file(svn_file):
    """load author file as a list."""
    svn_author_file = open(svn_file,'r')
    svn_authors = svn_author_file.read().splitlines()
    svn_author_file.close()
    return svn_authors

def load_ldap_user_info(uname, upass, ldap_user_context):
    """ retrieves user info from LDAP as a dictionary """

    try:
        # Initialize the connection
        l = ldap.initialize(ldap_user_context['connection_string'])
        l.protocol_version = ldap.VERSION3
        #username = "CN=" + uname + ", OU=PE Users,OU=Destiny Vitality,OU=US,DC=dhna,DC=corp"
        l.simple_bind_s(uname, upass)
        # Define search specific values
        baseDN = ldap_user_context['baseDN']
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ldap_user_context['retrieve_attributes']
        searchFilter = ldap_user_context['search_filter']

        ldap_result_id = l.search(baseDN, searchScope, searchFilter, retrieveAttributes)

        #process result set in to a dictionary.
        raw_pairs = []
        while 1:
            result_type, result_data = l.result(ldap_result_id, 0)
            if (result_data == []):
                break
            else:
                if result_type == ldap.RES_SEARCH_ENTRY:
                    raw_entry = result_data[0][1]
                    raw_pairs.append((raw_entry['name'][0].decode().strip().lower(), raw_entry))
                    if 'mail' in raw_entry:
                        # if an email address is defined in LDAP, add it as a reference for the record
                        raw_pairs.append((raw_entry['mail'][0].decode().strip(),raw_entry))
        result_set = dict(raw_pairs)
        l.unbind_s()
        return result_set
    except ldap.LDAPError as e:
        print('LDAP Exception occurred')
        print(e)
        l.unbind_s()
