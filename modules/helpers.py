botAdmins = [368894926]
allowedExtensions = ['pdf']

def isAdmin(chat_id):
    return chat_id in botAdmins


def getFileType(file):
    return file['mime_type'].split('/', 1)[1]


def supportedFile(msg):
    if not msg.get('document'):
        return False
    if getFileType(msg['document']) not in allowedExtensions:
        return False
    return True
