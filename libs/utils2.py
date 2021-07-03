typeName = lambda x:''.join([ch for ch in str(x).split()[-1] if (str(ch).isprintable() and (str(ch).isalnum() or (str(ch) in ['.'])))])

def print_traceback(ex, ex_traceback=None):
    import traceback
    if ex_traceback is None:
        ex_traceback = ex.__traceback__
    tb_lines = [ line.strip() for line in
                traceback.format_exception(ex.__class__, ex, ex_traceback)]
    print('\n'.join(tb_lines))

