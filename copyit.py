class Copyit():
    def deepish_copy(org):
        '''
        much, much faster than deepcopy, for a dict of the simple python types.
        '''
        out = dict().fromkeys(org)
        for k, v in org.items():
            try:
                out[k] = v.copy()  # dicts, sets
            except AttributeError:
                try:
                    out[k] = v[:]  # lists, tuples, strings, unicode
                except TypeError:
                    out[k] = v  # ints
        return out