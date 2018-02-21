import collections

Return_code = collections.namedtuple('Return_code', ['done', 'error'])
EXIT_CODE = Return_code(done=0, error=1)


def success_result(result_code):
    return result_code == EXIT_CODE.done
