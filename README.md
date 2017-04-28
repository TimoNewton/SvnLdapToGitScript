# SvnLdapToGitScript
Small python script to use ldap and an svn author list to create a list of git authors when migrating from subversion

Current iteration of the script assumes that you have already retrieved a list of all users from Subversion, one user per file line.
For my own personal use, I've used the following command against a local copy of the repo:

`svn log --quiet | awk '/^r/ {print $3}' | sort -u`

This was taken from this StackOverflow article: 

http://stackoverflow.com/questions/2494984/how-to-get-a-list-of-all-subversion-commit-author-usernames

### possible improvements
* add capability when given the url of a remote SVN repo to run the log command against that remote repo
* Add conditional for when the user "key" is not found in LDAP to not include that in the generated file
* allow system to be run end-to-end, including prompting for additional user input/decisions.
