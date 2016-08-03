import ldap
import getpass

default_email_domain = '@productiveedge.com' # Default domain to apply as the authors email
ldap_user_context = 'OU=PE Users,OU=Destiny Vitality,OU=US,DC=dhna,DC=corp' #context used for SSL connection to LDAP.


def create_author_file(svn_file,author_file_name):
    """Create an author file to move a subversion repository to git."""
    svn_authors = load_svn_file(svn_file)
    uname = input("Please provide LDAP username")
    upass = getpass.getpass("LDAP password")
    ldap_users = load_ldap_user_info(uname, upass)
    git_author_file_entries = []
    for svn_author in svn_authors:
        key = svn_author.strip().lower()
        author_name, author_email = '',''
        ldap_entry = None
        if(key in ldap_users):
            ldap_entry = ldap_users[key]
        elif(key+"@productiveedge.com" in ldap_users):
            ldap_entry = ldap_users[key+"@productiveedge.com"]
        if(ldap_entry):
            author_name = ldap_entry['displayName'][0].decode()
            if('mail' in ldap_entry):
                author_email = ldap_entry['mail'][0].decode()
            else:
                author_email = key + '@productiveedge.com'
        else:
            print(key + " not found in ldap")
            author_email = key + '@productiveedge.com'
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

def load_ldap_user_info(uname, upass):
    """ retrieves user info from LDAP as a dictionary """

    try:
        # Initialize the connection
        l = ldap.initialize('ldaps://adldapus.dhna.corp:636')
        l.protocol_version = ldap.VERSION3
        #username = "CN=" + uname + ", OU=PE Users,OU=Destiny Vitality,OU=US,DC=dhna,DC=corp"
        l.simple_bind_s(uname, upass)
        # Define search specific values
        baseDN = "OU=PE Users,OU=Destiny Vitality,OU=US,DC=dhna,DC=corp"
        searchScope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ['name', 'mail', 'displayName']
        searchFilter = "cn=*"

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
