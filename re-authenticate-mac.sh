 eval "$(ssh-agent -s)"
 ssh-add --apple-use-keychain ~/.ssh/id_rsa_github
 ssh -T git@github.com
