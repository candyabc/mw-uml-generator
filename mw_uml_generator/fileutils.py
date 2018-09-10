from .log import logger
import os
class FileOp(object):
    """Namespace for file operations during an update"""

    NO_OVERWRITE = 0
    """Do not overwrite an existing file during update
    (still created if not exists)
    """

    NO_CREATE = 1
    """Do not create the file during an update"""

    CREATE_NEW =2
    '''create a newfile with ext .__ during an update'''

    OVERWRITE =3
    '''overwrite an existing file during update
    (still created if not exists) '''

def save_file(path, content, opType,isupdate=False):
    if isupdate:
        update_save_file(path, content, opType)
    else:
        create_file(path, content)

def update_save_file(path, content, opType=FileOp.NO_OVERWRITE,overwrite =False):
    if overwrite ==True:
        opType = FileOp.OVERWRITE

    if opType==FileOp.NO_CREATE:
        logger.report('skip', path)
        return
    isexist = os.path.exists(path)
    if isexist:
        if opType==FileOp.NO_OVERWRITE:
            logger.report('skip',path)
            return
        elif opType==FileOp.CREATE_NEW:
            create_file(path+'.__',content)
        elif opType ==FileOp.OVERWRITE:
            create_file(path,content)
    else:
        create_file(path,content)

def create_directory(path, update=False, pretend=False):
    """Create a directory in the given path.

    This function reports the operation in the logs.

    Args:
        path (str): path in the file system where contents will be written.
        update (bool): false by default. A :obj:`OSError` is raised when update
            is false and the directory already exists.
        pretend (bool): false by default. Directory is not created when
            pretending, but operation is logged.
    """
    if not pretend:
        try:
            if not os.path.exists(path):
                os.mkdir(path)
                logger.report('create', path)

        except OSError:
            if not update:
                raise
            return  # Do not log if not created



def create_file(path, content, pretend=False):

    """Create a file in the given path.

    This function reports the operation in the logs.

    Args:
        path (str): path in the file system where contents will be written.
        content (str): what will be written.
        pretend (bool): false by default. File is not written when pretending,
            but operation is logged.
    """
    # logger.info('%s,%s' %(path,content))
    isexist = os.path.exists(path)
    if not pretend:
        if not os.path.exists(os.path.dirname(path)):
            create_directory(os.path.dirname(path))

        with open(path, 'w') as fh:
            fh.write(content)

    if isexist:
        logger.report('overwrite',path)
    else:
        if os.path.split('.')[-1]=='__':
            logger.report('create_new',path)
        else:
            logger.report('create' , path)