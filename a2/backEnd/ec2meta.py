import os

class EC2Meta():
    def getCurrentID():
        '''
        get the current id of this instance
        return: string, aws-id (i-xxxxxxxxxxxxxxxxx)
        '''
        return os.system('wget -q -O - http://169.254.169.254/latest/meta-data/instance-id')


    def getAMILaunchIndex():
        '''
        get the current launch index of this instance
        '''
        return os.system('wget -q -O - http://169.254.169.254/latest/meta-data/ami-launch-index')


    def getCurrentIP(iptype):
        '''
        get the current ip (local or public) of this instance
        type: (str) 'local' or 'public'
        '''
        if iptype == 'local':
            return os.system('wget -q -O - http://169.254.169.254/latest/meta-data/local-ipv4')
        elif iptype == 'public':
            return os.system('dig +short myip.opendns.com @resolver1.opendns.com')
        else:
            raise Exception('No IP type: {}'.format(iptype))