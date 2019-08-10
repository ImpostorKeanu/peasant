from pathlib import Path

def file_presence(file_name,*args,**kwargs):
    if not Path(file_name).exists():
        return False,Exception(f'File does not exist: {file_name}')
    return True,None

def validate(v_callback):

    def outer(func):

        def wrapper(*args,**kwargs):

            outcome, reason = v_callback(*args, **kwargs)
            if not outcome: raise reason

            return func(*args,**kwargs)

        return wrapper

    return outer
