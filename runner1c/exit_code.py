EXIT_CODE = {'done': 0, 'error': 1}


def success_result(result_code):
    return result_code == EXIT_CODE['done']
