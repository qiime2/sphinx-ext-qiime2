import sys
import io


def execute_code(code, use):
    """ Executes supplied code as pure python and returns a list of stdout, stderr

    Args:
        code (string): Python code to execute

    Results:
        (list): stdout, stderr of executed python code

    Raises:
        ExecutionError when supplied python is incorrect

    Examples:
        >>> execute_code('print "foobar"')
        'foobar'
    """

    output = io.StringIO()
    err = io.StringIO()

    # sys.stdout = output
    # sys.stderr = err

    try:
        # pylint: disable=exec-used
        exec(code)
    # If the code is invalid, just skip the block - any actual code errors
    # will be raised properly
    except TypeError:
        pass
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

    results = list()
    results.append(output.getvalue())
    results.append(err.getvalue())
    results = ''.join(results)

    return results
