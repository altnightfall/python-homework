def cases(test_cases):
    def decorator(func):
        def wrapper(self):
            for i, case in enumerate(test_cases):
                try:
                    func(self, case)
                except AssertionError as e:
                    raise AssertionError(f"Case #{i + 1} failed: {case}\n{e}") from e
        return wrapper
    return decorator